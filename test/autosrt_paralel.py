#!/usr/bin/env python3.8
# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

import argparse
import audioop
import datetime
import json
import math
import multiprocessing
import os
import re
import subprocess
import sys
import tempfile
import threading
import time
import wave

import datetime
from glob import glob
from threading import Thread
from typing import Any, Callable, Iterator, List, Optional, Union

import httpx
import pysrt
import requests
import six

try:
    from json.decoder import JSONDecodeError
except ImportError:
    JSONDecodeError = ValueError

try:
    from progressbar import ProgressBar, Percentage, Bar, ETA
except ImportError:
    ProgressBar = Percentage = Bar = ETA = None


VERSION = "1.4.10"


# ================================================================
# GLOBALS
# ================================================================

thread_transcribe = None
thread_transcribe_starter = None
pool = {}
do_translate = False
completed_tasks = 0
wav_converter_pbar = None
start_time = None
end_time = None
endpoint_config = None


# ================================================================
# FFMPEG PROGRESS
# ================================================================

def to_ms(**kwargs):
    hour = int(kwargs.get("hour", 0))
    minute = int(kwargs.get("min", 0))
    sec = int(kwargs.get("sec", 0))
    ms = int(kwargs.get("ms", 0))

    return (
        (hour * 60 * 60 * 1000)
        + (minute * 60 * 1000)
        + (sec * 1000)
        + ms
    )


def _probe_duration(cmd):
    """
    Get media duration using ffprobe.
    """

    def _get_file_name(command):
        try:
            idx = command.index("-i")
            return command[idx + 1]
        except (ValueError, IndexError):
            return None

    file_name = _get_file_name(cmd)

    if file_name is None:
        return None

    try:

        command = [
            "ffprobe",
            "-loglevel", "error",
            "-hide_banner",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            file_name
        ]

        kwargs = {
            "universal_newlines": True
        }

        if sys.platform == "win32":
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

        output = subprocess.check_output(command, **kwargs)

        value = output.strip()

        if not value:
            return None

        return int(float(value) * 1000)

    except Exception:
        return None


def _uses_error_loglevel(cmd):
    try:
        idx = cmd.index("-loglevel")
        return idx + 1 < len(cmd) and cmd[idx + 1] == "error"
    except ValueError:
        return False


class FfmpegProgress(object):

    DUR_REGEX = re.compile(
        r"Duration: (?P<hour>\d{2}):(?P<min>\d{2}):"
        r"(?P<sec>\d{2})\.(?P<ms>\d{2})"
    )

    TIME_REGEX = re.compile(
        r"out_time=(?P<hour>\d{2}):(?P<min>\d{2}):"
        r"(?P<sec>\d{2})\.(?P<ms>\d{2})"
    )

    def __init__(self, cmd, dry_run=False):
        self.cmd = cmd
        self.stderr = None
        self.dry_run = dry_run
        self.process = None
        self.stderr_callback = None

        if sys.platform == "win32":

            self.base_popen_kwargs = {
                "stdin": subprocess.PIPE,
                "stdout": subprocess.PIPE,
                "stderr": subprocess.STDOUT,
                "universal_newlines": False,
                "shell": False
            }

        else:

            self.base_popen_kwargs = {
                "stdin": subprocess.PIPE,
                "stdout": subprocess.PIPE,
                "stderr": subprocess.STDOUT,
                "universal_newlines": False
            }

    def set_stderr_callback(self, callback):
        if not callable(callback):
            raise ValueError("Callback must be callable")

        self.stderr_callback = callback

    def run_command_with_progress(
        self,
        popen_kwargs=None,
        duration_override=None
    ):

        if self.dry_run:
            yield 0
            yield 100
            return

        total_dur = None

        if _uses_error_loglevel(self.cmd):
            total_dur = _probe_duration(self.cmd)

        cmd_with_progress = (
            [self.cmd[0]]
            + ["-progress", "-", "-nostats"]
            + self.cmd[1:]
        )

        stderr = []

        base_popen_kwargs = self.base_popen_kwargs.copy()

        if popen_kwargs is not None:
            base_popen_kwargs.update(popen_kwargs)

        if sys.platform == "win32":
            base_popen_kwargs["creationflags"] = (
                subprocess.CREATE_NO_WINDOW
            )

        self.process = subprocess.Popen(
            cmd_with_progress,
            **base_popen_kwargs
        )

        yield 0

        while True:

            if self.process.stdout is None:
                break

            raw_line = self.process.stdout.readline()

            if not raw_line:
                if self.process.poll() is not None:
                    break
                continue

            stderr_line = raw_line.decode(
                "utf-8",
                errors="replace"
            ).strip()

            if self.stderr_callback:
                try:
                    self.stderr_callback(stderr_line)
                except Exception:
                    pass

            stderr.append(stderr_line)
            self.stderr = "\n".join(stderr)

            if total_dur is None:

                total_dur_match = self.DUR_REGEX.search(
                    stderr_line
                )

                if total_dur_match:

                    total_dur = to_ms(
                        **total_dur_match.groupdict()
                    )

                    continue

                if duration_override is not None:

                    total_dur = int(
                        float(duration_override) * 1000
                    )

                    continue

            if total_dur:

                progress_time = self.TIME_REGEX.search(
                    stderr_line
                )

                if progress_time:

                    elapsed_time = to_ms(
                        **progress_time.groupdict()
                    )

                    progress = int(
                        elapsed_time * 100 / total_dur
                    )

                    progress = max(
                        0,
                        min(100, progress)
                    )

                    yield progress

        return_code = self.process.wait()

        if return_code != 0:

            pretty_stderr = "\n".join(stderr)

            self.process = None

            raise RuntimeError(
                "Error running command {}: {}".format(
                    self.cmd,
                    pretty_stderr
                )
            )

        self.process = None

        yield 100

    def quit_gracefully(self):

        if self.process is None:
            raise RuntimeError(
                "No process found. Did you run the command?"
            )

        try:
            self.process.communicate(input=b"q")
        finally:
            if self.process.poll() is None:
                self.process.kill()

            self.process = None

    def quit(self):

        if self.process is None:
            raise RuntimeError(
                "No process found. Did you run the command?"
            )

        try:
            self.process.kill()
        finally:
            self.process = None


# ================================================================
# PROCESS CONTROL
# ================================================================

def stop_ffmpeg_windows(error_messages_callback=None):

    try:

        output = subprocess.check_output(
            ["tasklist"],
            creationflags=subprocess.CREATE_NO_WINDOW
        ).decode(
            "utf-8",
            errors="replace"
        )

        ffmpeg_pids = []

        for line in output.splitlines():

            parts = line.split()

            if len(parts) >= 2:
                process_name = parts[0].lower()

                if process_name in (
                    "ffmpeg.exe",
                    "ffmpeg"
                ):
                    ffmpeg_pids.append(parts[1])

        for pid in ffmpeg_pids:

            subprocess.call(
                [
                    "taskkill",
                    "/F",
                    "/T",
                    "/PID",
                    pid
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW
            )

    except KeyboardInterrupt:

        if error_messages_callback:
            error_messages_callback(
                "Cancelling all tasks"
            )
        else:
            print("Cancelling all tasks")

    except Exception as e:

        if error_messages_callback:
            error_messages_callback(
                "stop_ffmpeg_windows : {}".format(e)
            )
        else:
            print(e)


def stop_ffmpeg_linux(error_messages_callback=None):

    try:

        output = subprocess.check_output(
            ["ps", "-eo", "pid,comm"]
        ).decode(
            "utf-8",
            errors="replace"
        )

        for line in output.splitlines():

            parts = line.split()

            if len(parts) >= 2:

                pid = parts[0]
                process_name = parts[1].lower()

                if process_name == "ffmpeg":

                    try:
                        subprocess.call(
                            ["kill", "-9", pid]
                        )
                    except Exception:
                        pass

    except KeyboardInterrupt:

        if error_messages_callback:
            error_messages_callback(
                "Cancelling all tasks"
            )
        else:
            print("Cancelling all tasks")

    except Exception as e:

        if error_messages_callback:
            error_messages_callback(
                "stop_ffmpeg_linux : {}".format(e)
            )
        else:
            print(e)


def remove_temp_files(
    extension,
    error_messages_callback=None
):

    try:

        temp_dir = tempfile.gettempdir()

        extension = extension.lower().lstrip(".")

        for root, dirs, files in os.walk(temp_dir):

            for file_name in files:

                if file_name.lower().endswith(
                    "." + extension
                ):

                    file_path = os.path.join(
                        root,
                        file_name
                    )

                    try:
                        os.remove(file_path)
                    except OSError:
                        pass

    except KeyboardInterrupt:

        if error_messages_callback:
            error_messages_callback(
                "Cancelling all tasks"
            )
        else:
            print("Cancelling all tasks")

    except Exception as e:

        if error_messages_callback:
            error_messages_callback(
                "remove_temp_files : {}".format(e)
            )
        else:
            print(e)


# ================================================================
# LANGUAGE
# ================================================================

def is_same_language(
    src,
    dst,
    error_messages_callback=None
):

    try:
        return src.split("-")[0] == dst.split("-")[0]

    except Exception as e:

        if error_messages_callback:
            error_messages_callback(
                "is_same_language : {}".format(e)
            )
        else:
            print(e)

        return False


class Language(object):

    def __init__(self):

        self.list_codes = [
            "af", "sq", "am", "ar", "hy", "as", "ay", "az",
            "bm", "eu", "be", "bn", "bho", "bs", "bg", "ca",
            "ceb", "ny", "zh-CN", "zh-TW", "co", "hr", "cs",
            "da", "dv", "doi", "nl", "en", "eo", "et", "ee",
            "fil", "fi", "fr", "fy", "gl", "ka", "de", "el",
            "gn", "gu", "ht", "ha", "haw", "he", "hi", "hmn",
            "hu", "is", "ig", "ilo", "id", "ga", "it", "ja",
            "jv", "kn", "kk", "km", "rw", "gom", "ko", "kri",
            "kmr", "ckb", "ky", "lo", "la", "lv", "ln", "lt",
            "lg", "lb", "mk", "mg", "ms", "ml", "mt", "mi",
            "mr", "mni-Mtei", "lus", "mn", "my", "ne", "no",
            "or", "om", "ps", "fa", "pl", "pt", "pa", "qu",
            "ro", "ru", "sm", "sa", "gd", "nso", "sr", "st",
            "sn", "sd", "si", "sk", "sl", "so", "es", "su",
            "sw", "sv", "tg", "ta", "tt", "te", "th", "ti",
            "ts", "tr", "tk", "tw", "uk", "ur", "ug", "uz",
            "vi", "cy", "xh", "yi", "yo", "zu"
        ]

        self.list_names = [
            "Afrikaans", "Albanian", "Amharic", "Arabic",
            "Armenian", "Assamese", "Aymara", "Azerbaijani",
            "Bambara", "Basque", "Belarusian", "Bengali",
            "Bhojpuri", "Bosnian", "Bulgarian", "Catalan",
            "Cebuano", "Chichewa", "Chinese (Simplified)",
            "Chinese (Traditional)", "Corsican", "Croatian",
            "Czech", "Danish", "Dhivehi", "Dogri", "Dutch",
            "English", "Esperanto", "Estonian", "Ewe",
            "Filipino", "Finnish", "French", "Frisian",
            "Galician", "Georgian", "German", "Greek",
            "Guarani", "Gujarati", "Haitian Creole", "Hausa",
            "Hawaiian", "Hebrew", "Hindi", "Hmong", "Hungarian",
            "Icelandic", "Igbo", "Ilocano", "Indonesian",
            "Irish", "Italian", "Japanese", "Javanese",
            "Kannada", "Kazakh", "Khmer", "Kinyarwanda",
            "Konkani", "Korean", "Krio", "Kurdish (Kurmanji)",
            "Kurdish (Sorani)", "Kyrgyz", "Lao", "Latin",
            "Latvian", "Lingala", "Lithuanian", "Luganda",
            "Luxembourgish", "Macedonian", "Malagasy", "Malay",
            "Malayalam", "Maltese", "Maori", "Marathi",
            "Meiteilon (Manipuri)", "Mizo", "Mongolian",
            "Myanmar (Burmese)", "Nepali", "Norwegian",
            "Odiya (Oriya)", "Oromo", "Pashto", "Persian",
            "Polish", "Portuguese", "Punjabi", "Quechua",
            "Romanian", "Russian", "Samoan", "Sanskrit",
            "Scots Gaelic", "Sepedi", "Serbian", "Sesotho",
            "Shona", "Sindhi", "Sinhala", "Slovak",
            "Slovenian", "Somali", "Spanish", "Sundanese",
            "Swahili", "Swedish", "Tajik", "Tamil", "Tatar",
            "Telugu", "Thai", "Tigrinya", "Tsonga", "Turkish",
            "Turkmen", "Twi (Akan)", "Ukrainian", "Urdu",
            "Uyghur", "Uzbek", "Vietnamese", "Welsh", "Xhosa",
            "Yiddish", "Yoruba", "Zulu"
        ]

        self.dict = dict(zip(
            self.list_codes,
            self.list_names
        ))

        self.code_of_name = dict(
            zip(
                self.list_names,
                self.list_codes
            )
        )

        self.name_of_code = self.dict.copy()

    def get_name(self, get_code):

        if not get_code:
            return ""

        return self.dict.get(
            get_code.lower(),
            ""
        )

    def get_code(self, language):

        if not language:
            return ""

        language = language.lower()

        for code, name in self.dict.items():

            if name.lower() == language:
                return code

        return ""


# ================================================================
# FFMPEG / MEDIA DETECTION
# ================================================================

class WavConverter(object):

    @staticmethod
    def which(program):

        def is_exe(file_path):

            return (
                os.path.isfile(file_path)
                and os.access(
                    file_path,
                    os.X_OK
                )
            )

        fpath, _ = os.path.split(program)

        if fpath:

            if is_exe(program):
                return program

        else:

            for path in os.environ.get(
                "PATH",
                ""
            ).split(os.pathsep):

                path = path.strip('"')

                exe_file = os.path.join(
                    path,
                    program
                )

                if is_exe(exe_file):
                    return exe_file

        return None

    @staticmethod
    def ffmpeg_check():

        if WavConverter.which("ffmpeg"):
            return "ffmpeg"

        if WavConverter.which("ffmpeg.exe"):
            return "ffmpeg.exe"

        return None

    @staticmethod
    def ffprobe_check():

        if WavConverter.which("ffprobe"):
            return "ffprobe"

        if WavConverter.which("ffprobe.exe"):
            return "ffprobe.exe"

        return None

    def __init__(
        self,
        channels=1,
        rate=48000,
        progress_callback=None,
        error_messages_callback=None
    ):

        self.channels = channels
        self.rate = rate
        self.progress_callback = progress_callback
        self.error_messages_callback = (
            error_messages_callback
        )

    def __call__(self, media_filepath):

        if not os.path.isfile(media_filepath):

            message = (
                "The given file does not exist: {}"
                .format(media_filepath)
            )

            if self.error_messages_callback:
                self.error_messages_callback(message)
            else:
                print(message)

            return None

        ffmpeg = self.ffmpeg_check()

        if not ffmpeg:

            message = (
                "ffmpeg: Executable not found on machine."
            )

            if self.error_messages_callback:
                self.error_messages_callback(message)
            else:
                print(message)

            return None

        temp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)

        temp_path = temp.name
        temp.close()

        command = [
            ffmpeg,
            "-y",
            "-i", media_filepath,
            "-ac", str(self.channels),
            "-ar", str(self.rate),
            "-loglevel", "error",
            "-hide_banner",
            temp_path
        ]

        try:

            ff = FfmpegProgress(command)

            for progress in ff.run_command_with_progress():

                if self.progress_callback:
                    self.progress_callback(
                        media_filepath,
                        progress
                    )

            return temp_path, self.rate

        except KeyboardInterrupt:

            try:
                if os.path.isfile(temp_path):
                    os.remove(temp_path)
            except OSError:
                pass

            if self.error_messages_callback:
                self.error_messages_callback(
                    "Cancelling all tasks"
                )
            else:
                print("Cancelling all tasks")

            return None

        except Exception as e:

            try:
                if os.path.isfile(temp_path):
                    os.remove(temp_path)
            except OSError:
                pass

            if self.error_messages_callback:
                self.error_messages_callback(e)
            else:
                print(
                    "WavConverter : {}".format(e)
                )

            return None


def get_media_stream_types(
    file_path,
    error_messages_callback=None
):
    """
    Detect all media streams using a single ffprobe call.

    Returns:
        set containing "video", "audio", etc.
    """

    try:

        if not os.path.isfile(file_path):
            return set()

        ffprobe = WavConverter.ffprobe_check()

        if not ffprobe:

            message = (
                "ffprobe: Executable not found on machine."
            )

            if error_messages_callback:
                error_messages_callback(message)
            else:
                print(message)

            return set()

        command = [
            ffprobe,
            "-v", "error",
            "-show_entries", "stream=codec_type",
            "-of", "default=noprint_wrappers=1:nokey=1",
            file_path
        ]

        kwargs = {
            "stderr": subprocess.STDOUT,
            "universal_newlines": True
        }

        if sys.platform == "win32":
            kwargs["creationflags"] = (
                subprocess.CREATE_NO_WINDOW
            )

        output = subprocess.check_output(
            command,
            **kwargs
        )

        stream_types = set()

        for line in output.splitlines():

            stream_type = line.strip().lower()

            if stream_type:
                stream_types.add(stream_type)

        return stream_types

    except subprocess.CalledProcessError:
        return set()

    except KeyboardInterrupt:

        if error_messages_callback:
            error_messages_callback(
                "Cancelling all tasks"
            )
        else:
            print("Cancelling all tasks")

        return set()

    except Exception as e:

        if error_messages_callback:
            error_messages_callback(
                "get_media_stream_types : {}".format(e)
            )
        else:
            print(e)

        return set()


def is_video_file(
    file_path,
    error_messages_callback=None
):

    return "video" in get_media_stream_types(
        file_path,
        error_messages_callback
    )


def is_audio_file(
    file_path,
    error_messages_callback=None
):

    return "audio" in get_media_stream_types(
        file_path,
        error_messages_callback
    )


# ================================================================
# SPEECH REGION
# ================================================================

class SpeechRegionFinder(object):

    @staticmethod
    def percentile(arr, percent):

        if not arr:
            return 0

        arr = sorted(arr)

        k = (len(arr) - 1) * percent

        f = math.floor(k)
        c = math.ceil(k)

        if f == c:
            return arr[int(k)]

        d0 = arr[int(f)] * (c - k)
        d1 = arr[int(c)] * (k - f)

        return d0 + d1

    def __init__(
        self,
        frame_width=4096,
        min_region_size=0.5,
        max_region_size=6,
        error_messages_callback=None
    ):

        self.frame_width = frame_width
        self.min_region_size = min_region_size
        self.max_region_size = max_region_size
        self.error_messages_callback = (
            error_messages_callback
        )

    def __call__(self, wav_filepath):

        reader = None

        try:

            reader = wave.open(
                wav_filepath,
                "rb"
            )

            sample_width = reader.getsampwidth()
            rate = reader.getframerate()
            n_channels = reader.getnchannels()

            if rate <= 0:
                return []

            total_duration = (
                float(reader.getnframes()) / rate
            )

            chunk_duration = (
                float(self.frame_width) / rate
            )

            n_chunks = int(
                total_duration / chunk_duration
            )

            energies = []

            for _ in range(n_chunks):

                chunk = reader.readframes(
                    self.frame_width
                )

                if not chunk:
                    break

                energies.append(audioop.rms(chunk,sample_width * n_channels))
                #energies.append(audioop.rms(chunk, sample_width))

            if not energies:
                return []

            threshold = self.percentile(
                energies,
                0.2
            )

            elapsed_time = 0
            regions = []
            region_start = None

            for energy in energies:

                is_silence = (
                    energy <= threshold
                )

                max_exceeded = (
                    region_start is not None
                    and (
                        elapsed_time - region_start
                        >= self.max_region_size
                    )
                )

                if (
                    max_exceeded
                    or is_silence
                ) and region_start is not None:

                    if (
                        elapsed_time - region_start
                        >= self.min_region_size
                    ):

                        regions.append(
                            (
                                region_start,
                                elapsed_time
                            )
                        )

                    region_start = None

                elif (
                    region_start is None
                    and not is_silence
                ):

                    region_start = elapsed_time

                elapsed_time += chunk_duration

            if region_start is not None:

                if (
                    elapsed_time - region_start
                    >= self.min_region_size
                ):

                    regions.append(
                        (
                            region_start,
                            elapsed_time
                        )
                    )

            return regions

        except KeyboardInterrupt:

            if self.error_messages_callback:
                self.error_messages_callback(
                    "Cancelling all tasks"
                )
            else:
                print("Cancelling all tasks")

            return []

        except Exception as e:

            if self.error_messages_callback:
                self.error_messages_callback(
                    "SpeechRegionFinder : {}".format(e)
                )
            else:
                print(e)

            return []

        finally:

            if reader is not None:

                try:
                    reader.close()
                except Exception:
                    pass


# ================================================================
# FLAC CONVERTER
# ================================================================

class FLACConverter(object):

    def __init__(
        self,
        wav_filepath,
        include_before=0.25,
        include_after=0.25,
        error_messages_callback=None
    ):

        self.wav_filepath = wav_filepath
        self.include_before = include_before
        self.include_after = include_after
        self.error_messages_callback = (
            error_messages_callback
        )

    def __call__(self, region):

        temp_path = None

        try:

            start, end = region

            start = max(
                0,
                start - self.include_before
            )

            end += self.include_after

            duration = end - start

            temp = tempfile.NamedTemporaryFile(suffix=".flac", delete=False)

            temp_path = temp.name
            temp.close()

            command = [
                "ffmpeg",
                "-ss", str(start),
                "-t", str(duration),
                "-y",
                "-i", self.wav_filepath,
                "-loglevel", "error",
                "-hide_banner",
                temp_path
            ]

            kwargs = {
                "stdin": open(
                    os.devnull,
                    "rb"
                )
            }

            try:

                if sys.platform == "win32":
                    kwargs["creationflags"] = (
                        subprocess.CREATE_NO_WINDOW
                    )

                subprocess.check_output(
                    command,
                    stderr=subprocess.STDOUT,
                    **kwargs
                )

            finally:

                try:
                    kwargs["stdin"].close()
                except Exception:
                    pass

            with open(
                temp_path,
                "rb"
            ) as flac_file:

                content = flac_file.read()

            try:
                os.remove(temp_path)
            except OSError:
                pass

            temp_path = None

            return content

        except KeyboardInterrupt:

            if temp_path:

                try:
                    os.remove(temp_path)
                except OSError:
                    pass

            if self.error_messages_callback:
                self.error_messages_callback(
                    "Cancelling all tasks"
                )
            else:
                print("Cancelling all tasks")

            return None

        except Exception as e:

            if temp_path:

                try:
                    os.remove(temp_path)
                except OSError:
                    pass

            if self.error_messages_callback:
                self.error_messages_callback(
                    "FLACConverter : {}".format(e)
                )
            else:
                print(e)

            return None


# ================================================================
# SPEECH RECOGNIZER
# ================================================================

class SpeechRecognizer(object):
    def __init__(self, language="en", rate=48000, retries=3, api_key="AIzaSyBOti4mM-6x9WDnZIjIeyEU21OpBXqWBgw", timeout=30, error_messages_callback=None):
        self.language = language
        self.rate = rate
        self.api_key = api_key
        self.retries = retries
        self.timeout = timeout
        self.error_messages_callback = error_messages_callback

    def __call__(self, data):
        try:
            for i in range(self.retries):
                url = f"http://www.google.com/speech-api/v2/recognize?client=chromium&lang={self.language}&key={self.api_key}"
                headers = {"Content-Type": "audio/x-flac rate=%d" % self.rate}

                try:
                    resp = requests.post(url, data=data, headers=headers, timeout=self.timeout)
                except requests.exceptions.ConnectionError:
                    try:
                        resp = httpx.post(url, data=data, headers=headers, timeout=self.timeout)
                    except httpx.exceptions.NetworkError:
                        continue

                for line in resp.content.decode('utf-8').split("\n"):
                    try:
                        line = json.loads(line)
                        line = line['result'][0]['alternative'][0]['transcript']
                        return line[:1].upper() + line[1:]
                    except:
                        # no result
                        continue

        except KeyboardInterrupt:
            if self.error_messages_callback:
                self.error_messages_callback("Cancelling all tasks")
            else:
                print("Cancelling all tasks")
            return

        except Exception as e:
            if self.error_messages_callback:
                self.error_messages_callback(e)
            else:
                print(e)
            return



class SpeechRecognizerBAK(object):

    def __init__(
        self,
        language="en",
        rate=44100,
        retries=3,
        api_key="AIzaSyBOti4mM-6x9WDnZIjIeyEU21OpBXqWBgw",
        timeout=30,
        error_messages_callback=None
    ):
        self.language = language
        self.rate = rate
        self.api_key = api_key
        self.retries = retries
        self.timeout = timeout
        self.error_messages_callback = error_messages_callback

    def __call__(self, data):

        if not data:
            self._error("SpeechRecognizer: empty FLAC data")
            return None

        url = (
            "http://www.google.com/"
            "speech-api/v2/recognize"
            "?client=chromium"
            "&lang={lang}"
            "&key={key}"
        ).format(
            lang=self.language,
            key=self.api_key
        )

        headers = {
            "Content-Type": (
                "audio/x-flac; rate=%d"
                % self.rate
            )
        }

        for attempt in range(1, self.retries + 1):

            try:

                response = requests.post(
                    url,
                    data=data,
                    headers=headers,
                    timeout=self.timeout
                )

                if response.status_code != 200:

                    self._error(
                        "SpeechRecognizer HTTP %d "
                        "(attempt %d/%d)"
                        % (
                            response.status_code,
                            attempt,
                            self.retries
                        )
                    )

                    self._error(
                        "Response: %s"
                        % response.text[:500]
                    )

                    continue

                content = response.content.decode(
                    "utf-8",
                    errors="replace"
                )

                if not content.strip():

                    self._error(
                        "SpeechRecognizer: empty response"
                    )

                    continue

                found_transcript = None

                for line in content.splitlines():

                    line = line.strip()

                    if not line:
                        continue

                    try:
                        obj = json.loads(line)
                    except ValueError:
                        continue

                    results = obj.get("result")

                    if not isinstance(results, list):
                        continue

                    for result in results:

                        if not isinstance(result, dict):
                            continue

                        alternatives = result.get(
                            "alternative"
                        )

                        if not isinstance(
                            alternatives,
                            list
                        ):
                            continue

                        for alternative in alternatives:

                            if not isinstance(
                                alternative,
                                dict
                            ):
                                continue

                            transcript = alternative.get(
                                "transcript"
                            )

                            if transcript:

                                found_transcript = (
                                    transcript.strip()
                                )

                                break

                        if found_transcript:
                            break

                    if found_transcript:
                        break

                if found_transcript:

                    return (
                        found_transcript[:1].upper()
                        + found_transcript[1:]
                    )

                self._error(
                    "SpeechRecognizer: "
                    "no transcript in response"
                )

                self._error(
                    "Response: %s"
                    % content[:1000]
                )

            except requests.exceptions.RequestException as e:

                self._error(
                    "SpeechRecognizer request error "
                    "(attempt %d/%d): %s"
                    % (
                        attempt,
                        self.retries,
                        e
                    )
                )

            except KeyboardInterrupt:

                self._error(
                    "Cancelling all tasks"
                )

                return None

            except Exception as e:

                self._error(
                    "SpeechRecognizer error: %s"
                    % e
                )

        return None

    def _error(self, message):

        if self.error_messages_callback:
            self.error_messages_callback(message)
        else:
            print(message)




# ================================================================
# GOOGLE TRANSLATE RESPONSE PARSER
# ================================================================

def parse_translate_response(
    data,
    endpoint_type
):
    """
    Extract translation from endpoint response.
    """

    try:

        if not isinstance(data, list):
            return None

        if not data:
            return None

        if endpoint_type == 1:

            first = data[0]

            if not isinstance(first, list):
                return None

            result = []

            for item in first:

                if (
                    isinstance(item, list)
                    and len(item) > 0
                    and isinstance(item[0], str)
                ):

                    result.append(item[0])

            translation = "".join(result)

            return (
                translation
                if translation
                else None
            )

        if endpoint_type == 2:

            first = data[0]

            if isinstance(first, str):
                return first

            if isinstance(first, list):

                result = []

                for item in first:

                    if isinstance(item, str):

                        result.append(item)

                    elif (
                        isinstance(item, list)
                        and len(item) > 0
                        and isinstance(item[0], str)
                    ):

                        result.append(item[0])

                translation = "".join(result)

                return (
                    translation
                    if translation
                    else None
                )

    except Exception:
        pass

    return None


# ================================================================
# SENTENCE TRANSLATOR
# ================================================================

class SentenceTranslator(object):

    def __init__(
        self,
        src,
        dst,
        endpoint_config,
        patience=-1,
        timeout=30,
        error_messages_callback=None
    ):

        self.src = src
        self.dst = dst
        self.endpoint_config = endpoint_config or {}
        self.patience = patience
        self.timeout = timeout
        self.error_messages_callback = (
            error_messages_callback
        )

    def __call__(self, sentence):

        try:

            if not sentence:
                return None

            translated_sentence = self.GoogleTranslate(
                sentence,
                src=self.src,
                dst=self.dst,
                timeout=self.timeout
            )

            if translated_sentence is None:
                return None

            translated_sentence = str(
                translated_sentence
            )

            if not translated_sentence:
                return None

            fail_to_translate = (
                translated_sentence.endswith("\n")
            )

            patience = self.patience

            while fail_to_translate and patience:

                translated_sentence = (
                    self.GoogleTranslate(
                        translated_sentence,
                        src=self.src,
                        dst=self.dst,
                        timeout=self.timeout
                    )
                )

                if translated_sentence is None:
                    return None

                translated_sentence = str(
                    translated_sentence
                )

                if translated_sentence.endswith(
                    "\n"
                ):

                    if patience == -1:
                        continue

                    patience -= 1

                else:

                    fail_to_translate = False

            return translated_sentence

        except KeyboardInterrupt:

            if self.error_messages_callback:
                self.error_messages_callback(
                    "Cancelling all tasks"
                )
            else:
                print("Cancelling all tasks")

            return None

        except Exception as e:

            if self.error_messages_callback:
                self.error_messages_callback(e)
            else:
                print(e)

            return None

    def GoogleTranslate(
        self,
        text,
        src,
        dst,
        timeout=30
    ):

        if not text:
            return None

        endpoint_type = self.endpoint_config.get(
            "type"
        )

        if endpoint_type not in (1, 2):
            return None

        url = self.endpoint_config.get("url")

        if not url:
            return None

        headers = self.endpoint_config.get(
            "headers",
            {}
        )

        base_params = self.endpoint_config.get(
            "params",
            {}
        ).copy()

        base_params["sl"] = src
        base_params["tl"] = dst
        base_params["q"] = text

        try:

            response = requests.get(
                url,
                params=base_params,
                headers=headers,
                timeout=timeout
            )

            if response.status_code != 200:

                return None

            try:
                data = response.json()
            except ValueError:
                return None

            return parse_translate_response(
                data,
                endpoint_type
            )

        except requests.exceptions.RequestException:

            # ====================================================
            # FALLBACK TO HTTPX
            # ====================================================

            try:

                with httpx.Client(
                    timeout=timeout
                ) as client:

                    response = client.get(
                        url,
                        params=base_params,
                        headers=headers
                    )

                if response.status_code != 200:
                    return None

                try:
                    data = response.json()
                except ValueError:
                    return None

                return parse_translate_response(
                    data,
                    endpoint_type
                )

            except Exception as e:

                if self.error_messages_callback:
                    self.error_messages_callback(e)

                return None

        except KeyboardInterrupt:

            if self.error_messages_callback:
                self.error_messages_callback(
                    "Cancelling all tasks"
                )
            else:
                print("Cancelling all tasks")

            return None

        except Exception as e:

            if self.error_messages_callback:
                self.error_messages_callback(e)
            else:
                print(e)

            return None


# ================================================================
# TEST TRANSLATION ENDPOINT
# ================================================================

def test_translation_endpoint(
    src,
    dst,
    error_messages_callback=None
):

    test_sentence = "Hello"

    # ============================================================
    # ENDPOINT 1
    # ============================================================

    endpoint1 = {
        "type": 1,

        "url": (
            "https://translate.googleapis.com/"
            "translate_a/single"
        ),

        "params": {
            "client": "gtx",
            "sl": src,
            "tl": dst,
            "dt": "t",
            "q": test_sentence
        },

        "headers": {
            "User-Agent": (
                "Mozilla/5.0 "
                "(Windows NT 10.0; Win64; x64)"
            ),
            "Referer": (
                "https://translate.google.com"
            )
        }
    }

    try:

        response = requests.get(
            endpoint1["url"],
            params=endpoint1["params"],
            headers=endpoint1["headers"],
            timeout=10
        )

        if response.status_code == 200:

            try:
                data = response.json()
            except ValueError:
                data = None

            translation = parse_translate_response(
                data,
                1
            )

            if translation:
                return endpoint1

    except KeyboardInterrupt:

        if error_messages_callback:
            error_messages_callback(
                "Cancelling all tasks"
            )
        else:
            print("Cancelling all tasks")

        return None

    except Exception as e:
        if error_messages_callback:
            error_messages_callback(e)
        else:
            print("SentenceTranslator endpoint 1 : FAILED")
            print("Error: %s" % e)


    # ============================================================
    # ENDPOINT 2
    # ============================================================

    endpoint2 = {
        "type": 2,

        "url": (
            "https://clients5.google.com/"
            "translate_a/t"
        ),

        "params": {
            "client": "dict-chrome-ex",
            "sl": src,
            "tl": dst,
            "q": test_sentence
        },

        "headers": {
            "User-Agent": (
                "Mozilla/5.0 "
                "(Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/139.0.0.0 "
                "Safari/537.36"
            ),
            "Accept": (
                "application/json,text/plain,*/*"
            )
        }
    }

    try:

        response = requests.get(
            endpoint2["url"],
            params=endpoint2["params"],
            headers=endpoint2["headers"],
            timeout=10
        )

        if response.status_code == 200:

            try:
                data = response.json()
            except ValueError:
                data = None

            translation = parse_translate_response(
                data,
                2
            )

            if translation:
                return endpoint2

    except KeyboardInterrupt:

        if error_messages_callback:
            error_messages_callback(
                "Cancelling all tasks"
            )
        else:
            print("Cancelling all tasks")

        return None

    except Exception as e:
        if error_messages_callback:
            error_messages_callback(e)
        else:
            print("SentenceTranslator endpoint 2 : FAILED")
            print("Error: %s" % e)

    return None


# ================================================================
# SUBTITLE FORMATTER
# ================================================================

class SubtitleFormatter(object):

    supported_formats = [
        "srt",
        "vtt",
        "json",
        "raw"
    ]

    def __init__(
        self,
        format_type,
        error_messages_callback=None
    ):

        self.format_type = (
            format_type.lower()
        )

        self.error_messages_callback = (
            error_messages_callback
        )

    def __call__(
        self,
        subtitles,
        padding_before=0,
        padding_after=0
    ):

        try:

            if self.format_type == "srt":

                return self.srt_formatter(
                    subtitles,
                    padding_before,
                    padding_after
                )

            elif self.format_type == "vtt":

                return self.vtt_formatter(
                    subtitles,
                    padding_before,
                    padding_after
                )

            elif self.format_type == "json":

                return self.json_formatter(
                    subtitles
                )

            elif self.format_type == "raw":

                return self.raw_formatter(
                    subtitles
                )

            raise ValueError(
                "Unsupported format type: {}".format(
                    self.format_type
                )
            )

        except KeyboardInterrupt:

            if self.error_messages_callback:
                self.error_messages_callback(
                    "Cancelling all tasks"
                )
            else:
                print("Cancelling all tasks")

            return ""

        except Exception as e:

            if self.error_messages_callback:
                self.error_messages_callback(
                    "SubtitleFormatter : {}".format(e)
                )
            else:
                print(e)

            return ""

    @staticmethod
    def _to_subrip_time(seconds):

        milliseconds = max(
            0,
            int(round(float(seconds) * 1000))
        )

        return pysrt.SubRipTime(
            milliseconds=milliseconds
        )

    def srt_formatter(
        self,
        subtitles,
        padding_before=0,
        padding_after=0
    ):

        sub_rip_file = pysrt.SubRipFile()

        for i, ((start, end), text) in enumerate(
            subtitles,
            start=1
        ):

            item = pysrt.SubRipItem()

            item.index = i
            item.text = six.text_type(text)

            item.start = self._to_subrip_time(
                max(
                    0,
                    start - padding_before
                )
            )

            item.end = self._to_subrip_time(
                end + padding_after
            )

            sub_rip_file.append(item)

        return "\n".join(
            six.text_type(item)
            for item in sub_rip_file
        )

    def vtt_formatter(
        self,
        subtitles,
        padding_before=0,
        padding_after=0
    ):

        text = self.srt_formatter(
            subtitles,
            padding_before,
            padding_after
        )

        return (
            "WEBVTT\n\n"
            + text.replace(",", ".")
        )

    def json_formatter(self, subtitles):

        subtitle_dicts = [
            {
                "start": start,
                "end": end,
                "content": text
            }

            for ((start, end), text)
            in subtitles
        ]

        return json.dumps(
            subtitle_dicts,
            ensure_ascii=False
        )

    def raw_formatter(self, subtitles):

        return " ".join(
            six.text_type(text)
            for (_rng, text)
            in subtitles
        )


# ================================================================
# SUBTITLE WRITER
# ================================================================

class SubtitleWriter(object):

    def __init__(
        self,
        regions,
        transcripts,
        format,
        error_messages_callback=None
    ):

        self.regions = regions
        self.transcripts = transcripts
        self.format = format

        self.timed_subtitles = [
            (r, t)
            for r, t in zip(
                self.regions,
                self.transcripts
            )
            if t
        ]

        self.error_messages_callback = (
            error_messages_callback
        )

    def get_timed_subtitles(self):
        return self.timed_subtitles

    def write(self, declared_subtitle_filepath):

        try:

            formatter = SubtitleFormatter(
                self.format,
                error_messages_callback=(
                    self.error_messages_callback
                )
            )

            formatted_subtitles = formatter(
                self.timed_subtitles
            )

            saved_subtitle_filepath = (
                declared_subtitle_filepath
            )

            if saved_subtitle_filepath:

                subtitle_file_base, subtitle_file_ext = (
                    os.path.splitext(
                        saved_subtitle_filepath
                    )
                )

                if not subtitle_file_ext:

                    saved_subtitle_filepath = (
                        "{}.{}".format(
                            subtitle_file_base,
                            self.format
                        )
                    )

            with open(
                saved_subtitle_filepath,
                "wb"
            ) as f:

                f.write(
                    formatted_subtitles.encode(
                        "utf-8"
                    )
                )

            return saved_subtitle_filepath

        except KeyboardInterrupt:

            if self.error_messages_callback:
                self.error_messages_callback(
                    "Cancelling all tasks"
                )
            else:
                print("Cancelling all tasks")

            return None

        except Exception as e:

            if self.error_messages_callback:
                self.error_messages_callback(
                    "SubtitleWriter : {}".format(e)
                )
            else:
                print(e)

            return None


# ================================================================
# SRT READER
# ================================================================

class SRTFileReader(object):

    def __init__(
        self,
        srt_file_path,
        error_messages_callback=None
    ):

        self.error_messages_callback = (
            error_messages_callback
        )

        self.timed_subtitles = self(
            srt_file_path
        )

    def __call__(self, srt_file_path):

        try:

            timed_subtitles = []

            with open(
                srt_file_path,
                "r",
                encoding="utf-8-sig"
            ) as srt_file:

                lines = srt_file.readlines()

            subtitle_blocks = []
            block = []

            for line in lines:

                if line.strip() == "":

                    if block:
                        subtitle_blocks.append(block)

                    block = []

                else:

                    block.append(
                        line.strip()
                    )

            if block:
                subtitle_blocks.append(block)

            for block in subtitle_blocks:

                if len(block) < 3:
                    continue

                try:

                    start_time_str, end_time_str = (
                        block[1].split(
                            " --> ",
                            1
                        )
                    )

                    start = pysrt.SubRipTime.from_string(
                        start_time_str.replace(
                            ".",
                            ","
                        )
                    )

                    end = pysrt.SubRipTime.from_string(
                        end_time_str.replace(
                            ".",
                            ","
                        )
                    )

                    subtitle = " ".join(
                        block[2:]
                    )

                    timed_subtitles.append(
                        (
                            (
                                start.ordinal / 1000.0,
                                end.ordinal / 1000.0
                            ),
                            subtitle
                        )
                    )

                except Exception:
                    continue

            return timed_subtitles

        except KeyboardInterrupt:

            if self.error_messages_callback:
                self.error_messages_callback(
                    "Cancelling all tasks"
                )
            else:
                print("Cancelling all tasks")

            return []

        except Exception as e:

            if self.error_messages_callback:
                self.error_messages_callback(e)
            else:
                print(e)

            return []


# ================================================================
# PROGRESS / ERROR
# ================================================================

def pBar(progress, total, prefix):

    if total <= 0:
        total = 1

    progress = max(
        0,
        min(progress, total)
    )

    bar_length = 10

    filled_up_length = int(
        round(
            bar_length
            * progress
            / float(total)
        )
    )

    percentage = round(
        100.0
        * progress
        / float(total),
        1
    )

    bar = (
        "█" * filled_up_length
        + " " * (
            bar_length
            - filled_up_length
        )
    )

    text = (
        "{} |{}| {}%\r"
        .format(
            prefix,
            bar,
            int(percentage)
        )
    )

    sys.stderr.write(text)
    sys.stderr.flush()


def show_progress(
    media_filepath,
    progress,
    prefix=None
):

    file_display_name = os.path.basename(
        media_filepath
    )

    prefix = (
        "Converting {} to a temporary WAV file         : "
        .format(
            file_display_name.center(32)
        )
    )

    pBar(
        progress,
        100,
        prefix
    )


def show_error_messages(messages):
    print(messages)


# ================================================================
# TRANSCRIBE
# ================================================================

def transcribe(
    src,
    dst,
    media_filepath,
    subtitle_format,
    event,
    n_media_filepaths
):

    global pool
    global do_translate
    global completed_tasks
    global start_time
    global end_time

    language = Language()

    wav_filepath = None
    sample_rate = None

    base, ext = os.path.splitext(
        media_filepath
    )

    subtitle_filepath = (
        "{}.{}".format(
            base,
            subtitle_format
        )
    )

    if os.path.isfile(
        subtitle_filepath
    ):

        try:
            os.remove(
                subtitle_filepath
            )
        except OSError:
            pass

    translated_subtitle_filepath = None

    if do_translate:

        translated_subtitle_filepath = (
            "{}.translated.{}".format(
                base,
                subtitle_format
            )
        )

        if os.path.isfile(
            translated_subtitle_filepath
        ):

            try:
                os.remove(
                    translated_subtitle_filepath
                )
            except OSError:
                pass

    file_display_name = os.path.basename(
        media_filepath
    )

    sys.stderr.write("\r")

    try:

        prefix = (
            "Converting {} to a temporary WAV file         : "
            .format(
                file_display_name.center(32)
            )
        )

        wav_converter = WavConverter(
            progress_callback=show_progress,
            error_messages_callback=(
                show_error_messages
            )
        )

        result = wav_converter(
            media_filepath
        )

        if not result:
            return

        wav_filepath, sample_rate = result

        pBar(
            100,
            100,
            prefix
        )

    except Exception as e:

        print(
            "wav_converter : {}".format(e)
        )

        return

    try:

        region_finder = SpeechRegionFinder(
            frame_width=4096,
            min_region_size=0.5,
            max_region_size=6,
            error_messages_callback=(
                show_error_messages
            )
        )

        regions = region_finder(
            wav_filepath
        )

        if not regions:
            print(
                "No speech regions found: {}".format(
                    file_display_name
                )
            )
            return

    except Exception as e:

        print(
            "region_finder : {}".format(e)
        )

        return

    try:

        converter = FLACConverter(
            wav_filepath=wav_filepath,
            error_messages_callback=(
                show_error_messages
            )
        )

    except Exception as e:

        print(
            "converter : {}".format(e)
        )

        return

    try:

        recognizer = SpeechRecognizer(
            language=src,
            rate=sample_rate,
            retries=3,
            error_messages_callback=(
                show_error_messages
            )
        )

    except Exception as e:

        print(
            "recognizer : {}".format(e)
        )

        return

    extracted_regions = []
    transcriptions = []

    sys.stderr.write("\r")

    try:

        total = len(regions)

        prefix = (
            "Converting {} speech regions to FLAC files    : "
            .format(
                file_display_name.center(32)
            )
        )

        current_pool = pool.get(
            media_filepath
        )

        if current_pool is None:
            raise RuntimeError(
                "Multiprocessing pool is unavailable"
            )

        for i, extracted_region in enumerate(
            current_pool.imap(
                converter,
                regions
            ),
            start=1
        ):

            if extracted_region:

                extracted_regions.append(
                    extracted_region
                )

            pBar(
                i,
                total,
                prefix
            )

        pBar(
            total,
            total,
            prefix
        )

        prefix = (
            "Creating {} transcriptions from FLAC files    : "
            .format(
                file_display_name.center(32)
            )
        )

        total_extracted = len(
            extracted_regions
        )

        for i, transcription in enumerate(
            current_pool.imap(
                recognizer,
                extracted_regions
            ),
            start=1
        ):

            transcriptions.append(
                transcription
            )

            pBar(
                i,
                total_extracted,
                prefix
            )

        pBar(
            total_extracted,
            total_extracted,
            prefix
        )

        writer = SubtitleWriter(
            regions[:len(transcriptions)],
            transcriptions,
            subtitle_format,
            error_messages_callback=(
                show_error_messages
            )
        )

        writer.write(
            subtitle_filepath
        )

        if do_translate:

            timed_subtitles = (
                writer.timed_subtitles
            )

            created_regions = []
            created_transcripts = []

            for entry in timed_subtitles:

                created_regions.append(
                    entry[0]
                )

                created_transcripts.append(
                    entry[1]
                )

            transcript_translator = (
                SentenceTranslator(
                    src=src,
                    dst=dst,
                    endpoint_config=(
                        endpoint_config
                    ),
                    error_messages_callback=(
                        show_error_messages
                    )
                )
            )

            translated_transcriptions = []

            total = len(
                created_transcripts
            )

            prefix = (
                "Translating {} from {} to {}      : "
                .format(
                    file_display_name.center(32),
                    src.center(8),
                    dst.center(8)
                )
            )

            for i, translated_transcription in enumerate(
                current_pool.imap(
                    transcript_translator,
                    created_transcripts
                ),
                start=1
            ):

                translated_transcriptions.append(
                    translated_transcription
                )

                pBar(
                    i,
                    total,
                    prefix
                )

            pBar(
                total,
                total,
                prefix
            )

            translation_writer = SubtitleWriter(
                created_regions,
                translated_transcriptions,
                subtitle_format,
                error_messages_callback=(
                    show_error_messages
                )
            )

            translation_writer.write(
                translated_subtitle_filepath
            )

        sys.stderr.write("\n")
        sys.stderr.flush()

        print("")

        if do_translate:

            print(
                "Original   subtitles file for {} created at   : {}"
                .format(
                    file_display_name.center(32),
                    subtitle_filepath
                )
            )

            print(
                "Translated subtitles file for {} created at   : {}"
                .format(
                    file_display_name.center(32),
                    translated_subtitle_filepath
                )
            )

        else:

            print(
                "Subtitles file for {} created at              : {}"
                .format(
                    file_display_name.center(32),
                    subtitle_filepath
                )
            )

        print("")

        event.set()

        completed_tasks += 1

        if completed_tasks == n_media_filepaths:
            end_time = datetime.datetime.now()
            elapsed_time = (end_time - start_time)
            print("transcribe elapsed_time = {}".format(elapsed_time))

    except KeyboardInterrupt:

        print(
            "Cancelling all tasks"
        )

    except Exception as e:

        print(
            "transcribe : {}".format(e)
        )

    finally:

        if wav_filepath:

            try:
                if os.path.isfile(
                    wav_filepath
                ):
                    os.remove(
                        wav_filepath
                    )
            except OSError:
                pass

        if event:
            event.set()

        current_pool = pool.get(
            media_filepath
        )

        if current_pool is not None:

            try:
                current_pool.close()
                current_pool.join()
            except Exception:
                pass

            pool[media_filepath] = None


# ================================================================
# MAIN
# ================================================================

def main():

    global pool
    global do_translate
    global completed_tasks
    global start_time
    global end_time
    global endpoint_config

    if sys.platform == "win32":

        stop_ffmpeg_windows(
            error_messages_callback=(
                show_error_messages
            )
        )

    else:

        stop_ffmpeg_linux(
            error_messages_callback=(
                show_error_messages
            )
        )

    remove_temp_files(
        "flac",
        error_messages_callback=(
            show_error_messages
        )
    )

    remove_temp_files(
        "wav",
        error_messages_callback=(
            show_error_messages
        )
    )

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "source_path",
        help=(
            "File path of the video or audio files "
            "to generate subtitles files "
            "(use wildcard for multiple files or "
            "separate them with a space character)"
        ),
        nargs="*"
    )

    parser.add_argument(
        "-S",
        "--src-language",
        help=(
            "Language code of the audio language "
            "spoken in video/audio source_path"
        ),
        default="en"
    )

    parser.add_argument(
        "-D",
        "--dst-language",
        help=(
            "Desired translation language code "
            "for the subtitles"
        ),
        default=None
    )

    parser.add_argument(
        "-ll",
        "--list-languages",
        help="List all supported languages",
        action="store_true"
    )

    parser.add_argument(
        "-o",
        "--output",
        help=(
            "Output file path for subtitles "
            "(by default, subtitles are saved "
            "in the same directory and named "
            "with the source_path base name)"
        )
    )

    parser.add_argument(
        "-F",
        "--format",
        help="Desired subtitle format",
        default="srt"
    )

    parser.add_argument(
        "-lf",
        "--list-formats",
        help="List all supported subtitle formats",
        action="store_true"
    )

    parser.add_argument(
        "-C",
        "--concurrency",
        help=(
            "Number of concurrent API requests to make"
        ),
        type=int,
        default=10
    )

    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=VERSION
    )

    args = parser.parse_args()

    language = Language()

    # ============================================================
    # LANGUAGES
    # ============================================================

    if args.list_languages:

        print(
            "List of supported languages:"
        )

        for code, name in sorted(
            language.name_of_code.items()
        ):

            print(
                "{:>8} : {}".format(
                    code,
                    name
                )
            )

        return 0

    if (
        args.src_language
        not in language.name_of_code
    ):

        print(
            "Source language is not supported. "
            "Run with --list-languages to see "
            "all supported languages."
        )

        return 1

    # ============================================================
    # TRANSLATION
    # ============================================================

    do_translate = False

    if args.dst_language:

        if (
            args.dst_language
            not in language.name_of_code
        ):

            print(
                "Destination language is not supported. "
                "Run with --list-languages to see "
                "all supported languages."
            )

            return 1

        do_translate = not is_same_language(
            args.src_language,
            args.dst_language,
            error_messages_callback=(
                show_error_messages
            )
        )

    # ============================================================
    # FORMATS
    # ============================================================

    if args.list_formats:

        print(
            "List of supported subtitle formats:"
        )

        for subtitle_format in (
            SubtitleFormatter.supported_formats
        ):

            print(
                subtitle_format
            )

        return 0

    args.format = args.format.lower()

    if (
        args.format
        not in SubtitleFormatter.supported_formats
    ):

        print(
            "Subtitle format is not supported. "
            "Run with --list-formats to see "
            "all supported formats."
        )

        return 1

    # ============================================================
    # SOURCE FILES
    # ============================================================

    if not args.source_path:

        parser.print_help(
            sys.stderr
        )

        return 1

    media_filepaths = []
    arg_filepaths = []

    for arg in args.source_path:

        if not os.path.isabs(arg):

            argpath = os.path.join(
                os.getcwd(),
                arg
            )

        else:

            argpath = arg

        matches = glob(argpath)

        if matches:

            arg_filepaths.extend(
                matches
            )

        elif os.path.isfile(argpath):

            arg_filepaths.append(
                argpath
            )

    # Remove duplicates while preserving order.
    seen = set()

    unique_arg_filepaths = []

    for path in arg_filepaths:

        normalized = os.path.normcase(
            os.path.abspath(path)
        )

        if normalized not in seen:

            seen.add(normalized)
            unique_arg_filepaths.append(
                path
            )

    arg_filepaths = unique_arg_filepaths

    # ============================================================
    # DETECT VIDEO / AUDIO
    # ============================================================

    for argpath in arg_filepaths:

        if not os.path.isfile(argpath):

            print(
                "{} is not exist".format(
                    argpath
                )
            )

            continue

        stream_types = get_media_stream_types(
            argpath,
            error_messages_callback=(
                show_error_messages
            )
        )

        if stream_types.intersection(
            ("video", "audio")
        ):

            media_filepaths.append(
                argpath
            )

        else:

            print(
                "{} is not a valid video or audio file"
                .format(argpath)
            )

    if not media_filepaths:

        print(
            "No valid video or audio files found."
        )

        return 1

    # ============================================================
    # TEST GOOGLE TRANSLATE ENDPOINT
    # ============================================================

    endpoint_config = None

    if do_translate:

        print(
            "Checking Google Translate endpoint..."
        )

        endpoint_config = (
            test_translation_endpoint(
                args.src_language,
                args.dst_language,
                error_messages_callback=(
                    show_error_messages
                )
            )
        )

        if endpoint_config is None:

            print(
                "Translation endpoint is unavailable."
            )

            return 1

        print(
            "Using Google Translate endpoint {}."
            .format(
                endpoint_config.get("type")
            )
        )

    # ============================================================
    # CONCURRENCY
    # ============================================================

    concurrency = max(
        1,
        int(args.concurrency)
    )

    completed_tasks = 0

    start_time = None
    end_time = None

    n_media_filepaths = len(
        media_filepaths
    )

    completion_events = {}

    pool = {}

    # ============================================================
    # CREATE POOLS
    # ============================================================

    try:

        for media_filepath in media_filepaths:

            pool[media_filepath] = (
                multiprocessing.Pool(
                    processes=concurrency
                )
            )

    except Exception as e:

        print(
            "pool : {}".format(e)
        )

        for p in pool.values():

            try:
                p.close()
                p.join()
            except Exception:
                pass

        return 1

    # ============================================================
    # CREATE EVENTS
    # ============================================================

    for media_filepath in media_filepaths:

        completion_events[
            media_filepath
        ] = threading.Event()

    start_time = datetime.datetime.now()

    # ============================================================
    # START TRANSCRIPTION THREADS
    # ============================================================

    threads = []

    for media_filepath in media_filepaths:

        thread = Thread(
            target=transcribe,
            args=(
                args.src_language,
                args.dst_language,
                media_filepath,
                args.format,
                completion_events[
                    media_filepath
                ],
                n_media_filepaths
            )
        )

        thread.daemon = True
        thread.start()

        threads.append(
            thread
        )

    # ============================================================
    # WAIT
    # ============================================================

    try:

        for completion_event in (
            completion_events.values()
        ):

            completion_event.wait()

    except KeyboardInterrupt:

        print(
            "\nCancelling all tasks..."
        )

    # Make sure worker threads have finished.
    for thread in threads:

        try:
            thread.join()
        except Exception:
            pass

    # ============================================================
    # CLEANUP POOLS
    # ============================================================

    for media_filepath, p in list(
        pool.items()
    ):

        if p is not None:

            try:
                p.close()
                p.join()
            except Exception:
                pass

            pool[media_filepath] = None

    # ============================================================
    # CLEANUP FFMPEG / TEMP FILES
    # ============================================================

    if sys.platform == "win32":

        stop_ffmpeg_windows(
            error_messages_callback=(
                show_error_messages
            )
        )

    else:

        stop_ffmpeg_linux(
            error_messages_callback=(
                show_error_messages
            )
        )

    remove_temp_files(
        "flac",
        error_messages_callback=(
            show_error_messages
        )
    )

    remove_temp_files(
        "wav",
        error_messages_callback=(
            show_error_messages
        )
    )

    if completed_tasks == n_media_filepaths:
        end_time = datetime.datetime.now()
        elapsed_time = (end_time - start_time)
        print("total elapsed_time = {}".format(elapsed_time))
        return 0

    return 0


# ================================================================
# ENTRY POINT
# ================================================================

if __name__ == "__main__":

    multiprocessing.freeze_support()

    sys.exit(
        main()
    )
