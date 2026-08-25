#!/usr/bin/env python3.8

from __future__ import absolute_import, print_function, unicode_literals

import argparse
import asyncio
import audioop
import json
import math
import multiprocessing
import os
import subprocess
import sys
import tempfile
import wave

from glob import glob

import requests
import pysrt
import six
import magic

from progressbar import ProgressBar, Percentage, Bar, ETA
from ffmpeg_progress_yield import FfmpegProgress


VERSION = "1.2.9"

# ================================================================
# DEFAULT SETTINGS
# ================================================================

DEFAULT_CONCURRENCY = 10
DEFAULT_TIMEOUT = 30

GOOGLE_SPEECH_API_KEY = (
    "AIzaSyBOti4mM-6x9WDnZIjIeyEU21OpBXqWBgw"
)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/139.0.0.0 Safari/537.36"
)


# ================================================================
# GLOBAL PROGRESS BAR
# ================================================================

pbar = None


# ================================================================
# ERROR CALLBACK
# ================================================================

def show_error_messages(messages):
    print(messages)


# ================================================================
# PROGRESS CALLBACK
# ================================================================

def show_progress(percentage):
    global pbar

    if pbar is not None:
        try:
            pbar.update(int(percentage))
        except Exception:
            pass


# ================================================================
# STOP FFMPEG - WINDOWS
# ================================================================

def stop_ffmpeg_windows(error_messages_callback=None):

    try:

        creationflags = getattr(
            subprocess,
            "CREATE_NO_WINDOW",
            0
        )

        output = subprocess.check_output(
            ["tasklist"],
            creationflags=creationflags
        ).decode(
            "utf-8",
            errors="ignore"
        )

        ffmpeg_pids = []

        for line in output.splitlines():

            if "ffmpeg.exe" in line.lower():

                parts = line.split()

                if len(parts) >= 2:

                    pid = parts[1]

                    if pid.isdigit():
                        ffmpeg_pids.append(pid)

        for pid in ffmpeg_pids:

            try:

                subprocess.run(
                    [
                        "taskkill",
                        "/F",
                        "/T",
                        "/PID",
                        pid
                    ],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=creationflags
                )

            except Exception:
                pass

    except KeyboardInterrupt:

        if error_messages_callback:
            error_messages_callback(
                "Cancelling all tasks"
            )

    except Exception as e:

        if error_messages_callback:
            error_messages_callback(e)


# ================================================================
# STOP FFMPEG - LINUX / UNIX
# ================================================================

def stop_ffmpeg_linux(error_messages_callback=None):

    try:

        subprocess.run(
            ["pkill", "-9", "-x", "ffmpeg"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

    except FileNotFoundError:
        pass

    except KeyboardInterrupt:

        if error_messages_callback:
            error_messages_callback(
                "Cancelling all tasks"
            )

    except Exception as e:

        if error_messages_callback:
            error_messages_callback(e)


# ================================================================
# REMOVE TEMP FILES
# ================================================================

def remove_temp_files(
    extension,
    error_messages_callback=None
):

    temp_dir = tempfile.gettempdir()

    try:

        extension = "." + extension.lower().lstrip(".")

        for root, dirs, files in os.walk(temp_dir):

            for filename in files:

                if filename.lower().endswith(extension):

                    filepath = os.path.join(
                        root,
                        filename
                    )

                    try:
                        os.remove(filepath)
                    except (PermissionError, FileNotFoundError):
                        pass

    except KeyboardInterrupt:

        if error_messages_callback:
            error_messages_callback(
                "Cancelling all tasks"
            )

    except Exception as e:

        if error_messages_callback:
            error_messages_callback(e)


# ================================================================
# LANGUAGE COMPARISON
# ================================================================

def is_same_language(src, dst):

    if not src or not dst:
        return False

    return (
        src.split("-")[0].lower()
        ==
        dst.split("-")[0].lower()
    )


# ================================================================
# MEDIA TYPE
# ================================================================

def is_video_file(file_path):

    try:

        mime_type = magic.from_file(
            file_path,
            mime=True
        )

        return mime_type.startswith("video/")

    except Exception:

        return False


def is_audio_file(file_path):

    try:

        mime_type = magic.from_file(
            file_path,
            mime=True
        )

        return mime_type.startswith("audio/")

    except Exception:

        return False


# ================================================================
# LANGUAGE
# ================================================================

class Language:

    LANGUAGES = {

        "af": "Afrikaans",
        "am": "Amharic",
        "ar": "Arabic",
        "as": "Assamese",
        "ay": "Aymara",
        "az": "Azerbaijani",
        "be": "Belarusian",
        "bg": "Bulgarian",
        "bho": "Bhojpuri",
        "bm": "Bambara",
        "bn": "Bengali",
        "bs": "Bosnian",
        "ca": "Catalan",
        "ceb": "Cebuano",
        "ckb": "Kurdish (Sorani)",
        "co": "Corsican",
        "cs": "Czech",
        "cy": "Welsh",
        "da": "Danish",
        "de": "German",
        "doi": "Dogri",
        "dv": "Dhivehi",
        "ee": "Ewe",
        "el": "Greek",
        "en": "English",
        "eo": "Esperanto",
        "es": "Spanish",
        "et": "Estonian",
        "eu": "Basque",
        "fa": "Persian",
        "fi": "Finnish",
        "fil": "Filipino",
        "fr": "French",
        "fy": "Frisian",
        "ga": "Irish",
        "gd": "Scots Gaelic",
        "gl": "Galician",
        "gn": "Guarani",
        "gom": "Konkani",
        "gu": "Gujarati",
        "ha": "Hausa",
        "haw": "Hawaiian",
        "he": "Hebrew",
        "hi": "Hindi",
        "hmn": "Hmong",
        "hr": "Croatian",
        "ht": "Haitian Creole",
        "hu": "Hungarian",
        "hy": "Armenian",
        "id": "Indonesian",
        "ig": "Igbo",
        "ilo": "Ilocano",
        "is": "Icelandic",
        "it": "Italian",
        "ja": "Japanese",
        "jv": "Javanese",
        "ka": "Georgian",
        "kk": "Kazakh",
        "km": "Khmer",
        "kmr": "Kurdish (Kurmanji)",
        "kn": "Kannada",
        "ko": "Korean",
        "kri": "Krio",
        "ky": "Kyrgyz",
        "la": "Latin",
        "lb": "Luxembourgish",
        "lg": "Luganda",
        "ln": "Lingala",
        "lo": "Lao",
        "lt": "Lithuanian",
        "lus": "Mizo",
        "lv": "Latvian",
        "mg": "Malagasy",
        "mi": "Maori",
        "mk": "Macedonian",
        "ml": "Malayalam",
        "mn": "Mongolian",
        "mni-Mtei": "Meiteilon (Manipuri)",
        "mr": "Marathi",
        "ms": "Malay",
        "mt": "Maltese",
        "my": "Myanmar (Burmese)",
        "ne": "Nepali",
        "nl": "Dutch",
        "no": "Norwegian",
        "nso": "Sepedi",
        "ny": "Chichewa",
        "om": "Oromo",
        "or": "Odiya (Oriya)",
        "pa": "Punjabi",
        "pl": "Polish",
        "ps": "Pashto",
        "pt": "Portuguese",
        "qu": "Quechua",
        "ro": "Romanian",
        "ru": "Russian",
        "rw": "Kinyarwanda",
        "sa": "Sanskrit",
        "sd": "Sindhi",
        "si": "Sinhala",
        "sk": "Slovak",
        "sl": "Slovenian",
        "sm": "Samoan",
        "sn": "Shona",
        "so": "Somali",
        "sq": "Albanian",
        "sr": "Serbian",
        "st": "Sesotho",
        "su": "Sundanese",
        "sv": "Swedish",
        "sw": "Swahili",
        "ta": "Tamil",
        "te": "Telugu",
        "tg": "Tajik",
        "th": "Thai",
        "ti": "Tigrinya",
        "tk": "Turkmen",
        "tr": "Turkish",
        "ts": "Tsonga",
        "tt": "Tatar",
        "tw": "Twi (Akan)",
        "ug": "Uyghur",
        "uk": "Ukrainian",
        "ur": "Urdu",
        "uz": "Uzbek",
        "vi": "Vietnamese",
        "xh": "Xhosa",
        "yi": "Yiddish",
        "yo": "Yoruba",
        "zh-CN": "Chinese (Simplified)",
        "zh-TW": "Chinese (Traditional)",
        "zu": "Zulu",
    }

    def __init__(self):

        self.dict = dict(self.LANGUAGES)

        self.list_codes = list(
            self.dict.keys()
        )

        self.list_names = list(
            self.dict.values()
        )

        self.code_of_name = {
            name: code
            for code, name
            in self.dict.items()
        }

        self.name_of_code = dict(
            self.dict
        )

    async def get_name(self, get_code):

        if not get_code:
            return ""

        return self.dict.get(
            get_code,
            self.dict.get(
                get_code.lower(),
                ""
            )
        )

    async def get_code(self, language):

        if not language:
            return ""

        language = language.lower()

        for code, name in self.dict.items():

            if name.lower() == language:
                return code

        return ""


# ================================================================
# WAV CONVERTER
# ================================================================

class WavConverter:

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

        path = WavConverter.which("ffmpeg")

        if path:
            return path

        path = WavConverter.which("ffmpeg.exe")

        if path:
            return path

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

    async def __call__(self, media_filepath):

        if not os.path.isfile(media_filepath):

            raise Exception(
                "Invalid file: {}".format(
                    media_filepath
                )
            )

        ffmpeg = self.ffmpeg_check()

        if not ffmpeg:

            raise Exception(
                "Dependency not found: ffmpeg"
            )

        fd, wav_filepath = tempfile.mkstemp(
            suffix=".wav"
        )

        os.close(fd)

        command = [

            ffmpeg,

            "-y",

            "-i",
            media_filepath,

            "-ac",
            str(self.channels),

            "-ar",
            str(self.rate),

            "-vn",

            "-loglevel",
            "error",

            "-hide_banner",

            wav_filepath
        ]

        try:

            ff = FfmpegProgress(
                command
            )

            for progress in ff.run_command_with_progress():

                if self.progress_callback:
                    self.progress_callback(
                        progress
                    )

            return (
                wav_filepath,
                self.rate
            )

        except asyncio.CancelledError:

            try:
                os.remove(wav_filepath)
            except Exception:
                pass

            raise

        except Exception as e:

            try:
                os.remove(wav_filepath)
            except Exception:
                pass

            if self.error_messages_callback:
                self.error_messages_callback(e)

            raise


# ================================================================
# SPEECH REGION FINDER
# ================================================================

class SpeechRegionFinder:

    @staticmethod
    def percentile(arr, percent):

        if not arr:
            return 0

        arr = sorted(arr)

        k = (
            len(arr) - 1
        ) * percent

        f = math.floor(k)
        c = math.ceil(k)

        if f == c:
            return arr[int(k)]

        d0 = (
            arr[int(f)]
            * (c - k)
        )

        d1 = (
            arr[int(c)]
            * (k - f)
        )

        return d0 + d1

    def __init__(
        self,
        frame_width=4096,
        min_region_size=0.5,
        max_region_size=6,
        error_messages_callback=None
    ):

        self.frame_width = frame_width
        self.min_region_size = (
            min_region_size
        )
        self.max_region_size = (
            max_region_size
        )
        self.error_messages_callback = (
            error_messages_callback
        )

    async def __call__(self, wav_filepath):

        reader = None

        try:

            reader = wave.open(
                wav_filepath,
                "rb"
            )

            sample_width = (
                reader.getsampwidth()
            )

            rate = (
                reader.getframerate()
            )

            n_channels = (
                reader.getnchannels()
            )

            total_frames = (
                reader.getnframes()
            )

            total_duration = (
                float(total_frames)
                / float(rate)
            )

            chunk_duration = (
                float(self.frame_width)
                / float(rate)
            )

            energies = []

            while True:

                chunk = reader.readframes(
                    self.frame_width
                )

                if not chunk:
                    break

                energy = audioop.rms(
                    chunk,
                    sample_width
                )

                energies.append(
                    energy
                )

            if not energies:
                return []

            threshold = (
                self.percentile(
                    energies,
                    0.20
                )
            )

            regions = []

            elapsed_time = 0.0
            region_start = None

            for energy in energies:

                is_silence = (
                    energy <= threshold
                )

                if region_start is not None:

                    region_duration = (
                        elapsed_time
                        - region_start
                    )

                    max_exceeded = (
                        region_duration
                        >= self.max_region_size
                    )

                    if (
                        max_exceeded
                        or is_silence
                    ):

                        if (
                            region_duration
                            >= self.min_region_size
                        ):

                            regions.append(
                                (
                                    region_start,
                                    elapsed_time
                                )
                            )

                        region_start = None

                elif not is_silence:

                    region_start = (
                        elapsed_time
                    )

                elapsed_time += (
                    chunk_duration
                )

            # ----------------------------------------------------
            # IMPORTANT:
            # Save final region if audio ends while speaking.
            # ----------------------------------------------------

            if region_start is not None:

                end_time = min(
                    elapsed_time,
                    total_duration
                )

                if (
                    end_time
                    - region_start
                    >= self.min_region_size
                ):

                    regions.append(
                        (
                            region_start,
                            end_time
                        )
                    )

            return regions

        except KeyboardInterrupt:

            if self.error_messages_callback:
                self.error_messages_callback(
                    "Cancelling all tasks"
                )

            return []

        except Exception as e:

            if self.error_messages_callback:
                self.error_messages_callback(e)

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

class FLACConverter:

    def __init__(
        self,
        wav_filepath,
        include_before=0.25,
        include_after=0.25,
        error_messages_callback=None
    ):

        self.wav_filepath = wav_filepath
        self.include_before = (
            include_before
        )
        self.include_after = (
            include_after
        )
        self.error_messages_callback = (
            error_messages_callback
        )

    async def __call__(self, region):

        start, end = region

        start = max(
            0,
            start - self.include_before
        )

        end += self.include_after

        duration = max(
            0,
            end - start
        )

        fd, flac_filepath = tempfile.mkstemp(
            suffix=".flac"
        )

        os.close(fd)

        command = [

            "ffmpeg",

            "-y",

            "-ss",
            str(start),

            "-t",
            str(duration),

            "-i",
            self.wav_filepath,

            "-vn",

            "-ac",
            "1",

            "-loglevel",
            "error",

            flac_filepath
        ]

        try:

            process = (
                await asyncio.create_subprocess_exec(
                    *command,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE
                )
            )

            _, stderr = (
                await process.communicate()
            )

            if process.returncode != 0:

                error_text = (
                    stderr.decode(
                        "utf-8",
                        errors="replace"
                    )
                    if stderr
                    else
                    "ffmpeg failed"
                )

                raise RuntimeError(
                    error_text
                )

            with open(
                flac_filepath,
                "rb"
            ) as f:

                content = f.read()

            return content

        except asyncio.CancelledError:

            raise

        except Exception as e:

            if self.error_messages_callback:
                self.error_messages_callback(e)

            return None

        finally:

            try:
                os.remove(
                    flac_filepath
                )
            except Exception:
                pass


# ================================================================
# SPEECH RECOGNIZER
# ================================================================

class SpeechRecognizer:

    def __init__(
        self,
        language="en",
        rate=48000,
        retries=3,
        api_key=GOOGLE_SPEECH_API_KEY,
        timeout=30,
        error_messages_callback=None
    ):

        self.language = language
        self.rate = rate
        self.api_key = api_key
        self.retries = max(
            1,
            retries
        )
        self.timeout = timeout
        self.error_messages_callback = (
            error_messages_callback
        )

    def _request(self, url, data, headers):

        return requests.post(
            url,
            data=data,
            headers=headers,
            timeout=self.timeout
        )

    async def __call__(self, data):

        if not data:
            return None

        url = (
            "https://www.google.com/"
            "speech-api/v2/recognize"
        )

        params = {

            "client": "chromium",
            "lang": self.language,
            "key": self.api_key
        }

        headers = {

            "Content-Type":
                "audio/x-flac; rate=%d"
                % self.rate
        }

        full_url = (
            url
            + "?"
            + "&".join(
                "{}={}".format(k, v)
                for k, v in params.items()
            )
        )

        for attempt in range(
            self.retries
        ):

            try:

                response = await asyncio.to_thread(
                    self._request,
                    full_url,
                    data,
                    headers
                )

                if (
                    response.status_code
                    != 200
                ):

                    if attempt + 1 < self.retries:

                        await asyncio.sleep(
                            min(
                                1.0 * (attempt + 1),
                                3.0
                            )
                        )

                        continue

                    return None

                text = response.content.decode(
                    "utf-8",
                    errors="replace"
                )

                for line in text.splitlines():

                    if not line.strip():
                        continue

                    try:

                        obj = json.loads(
                            line
                        )

                        results = obj.get(
                            "result"
                        )

                        if not results:
                            continue

                        alternatives = (
                            results[0].get(
                                "alternative",
                                []
                            )
                        )

                        if not alternatives:
                            continue

                        transcript = (
                            alternatives[0]
                            .get(
                                "transcript"
                            )
                        )

                        if transcript:

                            transcript = (
                                transcript.strip()
                            )

                            if transcript:

                                return (
                                    transcript[:1].upper()
                                    + transcript[1:]
                                )

                    except (
                        ValueError,
                        KeyError,
                        TypeError,
                        IndexError
                    ):

                        continue

                return None

            except requests.exceptions.RequestException:

                if attempt + 1 < self.retries:

                    await asyncio.sleep(
                        min(
                            1.0 * (attempt + 1),
                            3.0
                        )
                    )

                    continue

            except asyncio.CancelledError:

                raise

            except Exception as e:

                if self.error_messages_callback:
                    self.error_messages_callback(e)

                return None

        return None


# ================================================================
# GOOGLE TRANSLATE RESPONSE PARSER
# ================================================================

def parse_google_translation(
    data,
    endpoint_type
):

    if not isinstance(
        data,
        list
    ):
        return None

    if not data:
        return None

    # ============================================================
    # ENDPOINT 1
    # ============================================================

    if endpoint_type == 1:

        first = data[0]

        if not isinstance(
            first,
            list
        ):
            return None

        result = []

        for item in first:

            if (
                isinstance(item, list)
                and len(item) > 0
                and isinstance(
                    item[0],
                    str
                )
            ):

                result.append(
                    item[0]
                )

        translation = "".join(
            result
        )

        return (
            translation
            if translation
            else None
        )

    # ============================================================
    # ENDPOINT 2
    # ============================================================

    if endpoint_type == 2:

        first = data[0]

        if isinstance(
            first,
            str
        ):

            return (
                first
                if first
                else None
            )

        if isinstance(
            first,
            list
        ):

            result = []

            for item in first:

                if isinstance(
                    item,
                    str
                ):

                    result.append(
                        item
                    )

                elif (
                    isinstance(
                        item,
                        list
                    )
                    and len(item) > 0
                    and isinstance(
                        item[0],
                        str
                    )
                ):

                    result.append(
                        item[0]
                    )

            translation = "".join(
                result
            )

            return (
                translation
                if translation
                else None
            )

    return None


# ================================================================
# SENTENCE TRANSLATOR
# ================================================================

class SentenceTranslator:

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
        self.endpoint_config = (
            endpoint_config
        )
        self.patience = patience
        self.timeout = timeout
        self.error_messages_callback = (
            error_messages_callback
        )

    async def __call__(self, sentence):

        if not sentence:
            return None

        sentence = str(
            sentence
        ).strip()

        if not sentence:
            return None

        try:

            translated_sentence = (
                await self._translate(
                    sentence
                )
            )

            if translated_sentence is None:
                return None

            translated_sentence = str(
                translated_sentence
            )

            # ----------------------------------------------------
            # Preserve old retry behavior.
            # ----------------------------------------------------

            patience = self.patience

            while (
                translated_sentence.endswith("\n")
                and patience
            ):

                translated_sentence = (
                    await self._translate(
                        translated_sentence
                    )
                )

                if translated_sentence is None:
                    return None

                translated_sentence = str(
                    translated_sentence
                )

                if not translated_sentence.endswith(
                    "\n"
                ):

                    break

                if patience != -1:

                    patience -= 1

            return translated_sentence

        except asyncio.CancelledError:

            raise

        except Exception as e:

            if self.error_messages_callback:
                self.error_messages_callback(e)

            return None

    async def _translate(self, sentence):

        return await self.GoogleTranslate(
            sentence,
            self.src,
            self.dst,
            self.timeout
        )

    async def translate(self, sentence):

        return await self(
            sentence
        )

    async def GoogleTranslate(
        self,
        text,
        src,
        dst,
        timeout=30
    ):

        endpoint_type = (
            self.endpoint_config.get(
                "type"
            )
        )

        url = (
            self.endpoint_config.get(
                "url"
            )
        )

        headers = (
            self.endpoint_config.get(
                "headers",
                {}
            )
        )

        if endpoint_type == 1:

            params = {

                "client": "gtx",
                "sl": src,
                "tl": dst,
                "dt": "t",
                "q": text
            }

        elif endpoint_type == 2:

            params = {

                "client": "dict-chrome-ex",
                "sl": src,
                "tl": dst,
                "q": text
            }

        else:

            return None

        try:

            response = await asyncio.to_thread(
                requests.get,
                url,
                params=params,
                headers=headers,
                timeout=timeout
            )

            if response.status_code != 200:

                return None

            try:

                data = response.json()

            except ValueError:

                return None

            return parse_google_translation(
                data,
                endpoint_type
            )

        except requests.exceptions.RequestException as e:

            if self.error_messages_callback:
                self.error_messages_callback(e)

            return None

        except asyncio.CancelledError:

            raise

        except Exception as e:

            if self.error_messages_callback:
                self.error_messages_callback(e)

            return None


# ================================================================
# TRANSLATE MANY SUBTITLES CONCURRENTLY
# ================================================================

async def translate_subtitles(
    subtitles,
    translator,
    concurrency=10
):

    semaphore = asyncio.Semaphore(
        max(
            1,
            concurrency
        )
    )

    async def translate_one(
        index,
        text
    ):

        async with semaphore:

            result = await translator(
                text
            )

            return index, result

    tasks = [

        asyncio.create_task(
            translate_one(
                index,
                text
            )
        )

        for index, text
        in enumerate(subtitles)
    ]

    results = [
        None
        for _ in subtitles
    ]

    completed = 0

    for task in asyncio.as_completed(
        tasks
    ):

        index, result = await task

        results[index] = result

        completed += 1

        if pbar is not None:

            try:
                pbar.update(
                    completed
                )
            except Exception:
                pass

    return results


# ================================================================
# TEST TRANSLATION ENDPOINT
# ================================================================

def test_translation_endpoint(
    src,
    dst,
    error_messages_callback=None
):

    test_sentence = "Hello"

    print("")
    print(
        "CHECKING GOOGLE TRANSLATE ENDPOINT"
    )
    print(
        "==================================="
    )

    # ============================================================
    # ENDPOINT 1
    # ============================================================

    endpoint1 = {

        "type": 1,

        "url":
            "https://translate.googleapis.com/"
            "translate_a/single",

        "headers": {

            "User-Agent":
                USER_AGENT,

            "Referer":
                "https://translate.google.com"
        }
    }

    params1 = {

        "client": "gtx",
        "sl": src,
        "tl": dst,
        "dt": "t",
        "q": test_sentence
    }

    print(
        "Testing endpoint 1..."
    )

    print(
        endpoint1["url"]
    )

    try:

        response = requests.get(
            endpoint1["url"],
            params=params1,
            headers=endpoint1["headers"],
            timeout=10
        )

        if response.status_code == 200:

            try:

                data = response.json()

                translation = (
                    parse_google_translation(
                        data,
                        1
                    )
                )

            except ValueError:

                translation = None

            if translation:

                print(
                    "Endpoint 1 : OK"
                )

                print(
                    "Translation : {}"
                    .format(
                        translation
                    )
                )

                print(
                    "Using endpoint 1"
                )

                print("")

                endpoint1["params"] = params1

                return endpoint1

        print(
            "Endpoint 1 : FAILED "
            "(HTTP {})"
            .format(
                response.status_code
            )
        )

    except Exception as e:

        print(
            "Endpoint 1 : FAILED"
        )

        print(
            "Error: {}"
            .format(e)
        )

    # ============================================================
    # ENDPOINT 2
    # ============================================================

    endpoint2 = {

        "type": 2,

        "url":
            "https://clients5.google.com/"
            "translate_a/t",

        "headers": {

            "User-Agent":
                USER_AGENT,

            "Accept":
                "application/json,"
                "text/plain,*/*"
        }
    }

    params2 = {

        "client": "dict-chrome-ex",
        "sl": src,
        "tl": dst,
        "q": test_sentence
    }

    print(
        "Testing endpoint 2..."
    )

    print(
        endpoint2["url"]
    )

    try:

        response = requests.get(
            endpoint2["url"],
            params=params2,
            headers=endpoint2["headers"],
            timeout=10
        )

        if response.status_code == 200:

            try:

                data = response.json()

                translation = (
                    parse_google_translation(
                        data,
                        2
                    )
                )

            except ValueError:

                translation = None

            if translation:

                print(
                    "Endpoint 2 : OK"
                )

                print(
                    "Translation : {}"
                    .format(
                        translation
                    )
                )

                print(
                    "Using endpoint 2"
                )

                print("")

                endpoint2["params"] = params2

                return endpoint2

        print(
            "Endpoint 2 : FAILED "
            "(HTTP {})"
            .format(
                response.status_code
            )
        )

    except Exception as e:

        print(
            "Endpoint 2 : FAILED"
        )

        print(
            "Error: {}"
            .format(e)
        )

    print("")

    print(
        "ERROR: Both Google Translate endpoints "
        "are unavailable."
    )

    print("")

    return None


# ================================================================
# SUBTITLE FORMATTER
# ================================================================

class SubtitleFormatter:

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

    async def __call__(
        self,
        subtitles,
        padding_before=0,
        padding_after=0
    ):

        if self.format_type == "srt":

            return self.srt_formatter(
                subtitles,
                padding_before,
                padding_after
            )

        if self.format_type == "vtt":

            return self.vtt_formatter(
                subtitles,
                padding_before,
                padding_after
            )

        if self.format_type == "json":

            return self.json_formatter(
                subtitles
            )

        if self.format_type == "raw":

            return self.raw_formatter(
                subtitles
            )

        raise ValueError(
            "Unsupported format type: {}"
            .format(
                self.format_type
            )
        )

    @staticmethod
    def _seconds_to_milliseconds(
        seconds
    ):

        return int(
            round(
                float(seconds)
                * 1000
            )
        )

    def srt_formatter(
        self,
        subtitles,
        padding_before=0,
        padding_after=0
    ):

        sub_rip_file = (
            pysrt.SubRipFile()
        )

        for index, (
            (start, end),
            text
        ) in enumerate(
            subtitles,
            start=1
        ):

            item = (
                pysrt.SubRipItem()
            )

            item.index = index

            item.text = six.text_type(
                text
            )

            start_ms = max(
                0,
                self._seconds_to_milliseconds(
                    start - padding_before
                )
            )

            end_ms = (
                self._seconds_to_milliseconds(
                    end + padding_after
                )
            )

            item.start = (
                pysrt.SubRipTime(
                    milliseconds=start_ms
                )
            )

            item.end = (
                pysrt.SubRipTime(
                    milliseconds=end_ms
                )
            )

            sub_rip_file.append(
                item
            )

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
            + text.replace(
                ",",
                "."
            )
        )

    def json_formatter(
        self,
        subtitles
    ):

        subtitle_dicts = [

            {

                "start": start,
                "end": end,
                "content": text

            }

            for (
                (start, end),
                text
            )
            in subtitles
        ]

        return json.dumps(
            subtitle_dicts,
            ensure_ascii=False
        )

    def raw_formatter(
        self,
        subtitles
    ):

        return " ".join(
            six.text_type(text)
            for (
                _rng,
                text
            )
            in subtitles
        )


# ================================================================
# SUBTITLE WRITER
# ================================================================

class SubtitleWriter:

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

            (
                region,
                transcript
            )

            for region, transcript
            in zip(
                regions,
                transcripts
            )

            if transcript
            and str(
                transcript
            ).strip()
        ]

        self.error_messages_callback = (
            error_messages_callback
        )

    async def get_timed_subtitles(
        self
    ):

        return self.timed_subtitles

    async def write(
        self,
        declared_subtitle_filepath
    ):

        formatter = SubtitleFormatter(
            self.format,
            self.error_messages_callback
        )

        formatted_subtitles = await formatter(
            self.timed_subtitles
        )

        saved_subtitle_filepath = (
            declared_subtitle_filepath
        )

        base, ext = os.path.splitext(
            saved_subtitle_filepath
        )

        if not ext:

            saved_subtitle_filepath = (
                "{}.{}"
                .format(
                    base,
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


# ================================================================
# PROCESS ONE MEDIA FILE
# ================================================================

async def process_media_file(
    media_filepath,
    args,
    endpoint_config
):

    global pbar

    print(
        "Processing {} :".format(
            media_filepath
        )
    )

    # ============================================================
    # WAV
    # ============================================================

    widgets = [

        "Converting to a temporary WAV file      : ",
        Percentage(),
        " ",
        Bar(),
        " ",
        ETA()
    ]

    pbar = ProgressBar(
        widgets=widgets,
        maxval=100
    ).start()

    wav_converter = WavConverter(
        channels=1,
        rate=48000,
        progress_callback=show_progress,
        error_messages_callback=show_error_messages
    )

    try:

        wav_filepath, sample_rate = (
            await wav_converter(
                media_filepath
            )
        )

    finally:

        if pbar is not None:
            pbar.finish()

        pbar = None

    # ============================================================
    # FIND SPEECH REGIONS
    # ============================================================

    region_finder = SpeechRegionFinder(
        frame_width=4096,
        min_region_size=0.5,
        max_region_size=6,
        error_messages_callback=show_error_messages
    )

    regions = await region_finder(
        wav_filepath
    )

    if not regions:

        print(
            "No speech regions found."
        )

        try:
            os.remove(wav_filepath)
        except Exception:
            pass

        return

    # ============================================================
    # FLAC EXTRACTION
    # ============================================================

    flac_converter = FLACConverter(
        wav_filepath=wav_filepath,
        error_messages_callback=show_error_messages
    )

    widgets = [

        "Converting speech regions to FLAC files : ",
        Percentage(),
        " ",
        Bar(),
        " ",
        ETA()
    ]

    pbar = ProgressBar(
        widgets=widgets,
        maxval=len(regions)
    ).start()

    semaphore = asyncio.Semaphore(
        max(
            1,
            args.concurrency
        )
    )

    async def extract_one(
        index,
        region
    ):

        async with semaphore:

            result = await flac_converter(
                region
            )

            return index, result

    flac_tasks = [

        asyncio.create_task(
            extract_one(
                index,
                region
            )
        )

        for index, region
        in enumerate(regions)
    ]

    extracted_regions = [
        None
        for _ in regions
    ]

    completed = 0

    for task in asyncio.as_completed(
        flac_tasks
    ):

        index, data = await task

        extracted_regions[index] = data

        completed += 1

        pbar.update(
            completed
        )

    pbar.finish()
    pbar = None

    # ============================================================
    # SPEECH RECOGNITION
    # ============================================================

    recognizer = SpeechRecognizer(
        language=args.src_language,
        rate=sample_rate,
        api_key=GOOGLE_SPEECH_API_KEY,
        retries=3,
        timeout=30,
        error_messages_callback=show_error_messages
    )

    widgets = [

        "Performing speech recognition           : ",
        Percentage(),
        " ",
        Bar(),
        " ",
        ETA()
    ]

    pbar = ProgressBar(
        widgets=widgets,
        maxval=len(regions)
    ).start()

    async def recognize_one(
        index,
        data
    ):

        async with semaphore:

            if not data:
                result = None
            else:
                result = await recognizer(
                    data
                )

            return index, result

    recognition_tasks = [

        asyncio.create_task(
            recognize_one(
                index,
                data
            )
        )

        for index, data
        in enumerate(
            extracted_regions
        )
    ]

    transcripts = [
        None
        for _ in regions
    ]

    completed = 0

    for task in asyncio.as_completed(
        recognition_tasks
    ):

        index, transcript = (
            await task
        )

        transcripts[index] = transcript

        completed += 1

        pbar.update(
            completed
        )

    pbar.finish()
    pbar = None

    # ============================================================
    # WRITE ORIGINAL SUBTITLE
    # ============================================================

    subtitle_format = (
        args.format.lower()
    )

    if args.output:

        subtitle_file_base, subtitle_ext = (
            os.path.splitext(
                args.output
            )
        )

        if subtitle_ext:

            subtitle_filepath = (
                args.output
            )

        else:

            subtitle_filepath = (
                "{}.{}"
                .format(
                    args.output,
                    subtitle_format
                )
            )

    else:

        base, _ = os.path.splitext(
            media_filepath
        )

        subtitle_filepath = (
            "{}.{}"
            .format(
                base,
                subtitle_format
            )
        )

    writer = SubtitleWriter(
        regions,
        transcripts,
        subtitle_format,
        error_messages_callback=show_error_messages
    )

    await writer.write(
        subtitle_filepath
    )

    # ============================================================
    # TRANSLATION
    # ============================================================

    translated_subtitle_filepath = None

    if (
        args.dst_language
        and endpoint_config
        and not is_same_language(
            args.src_language,
            args.dst_language
        )
    ):

        timed_subtitles = (
            writer.timed_subtitles
        )

        created_regions = [
            entry[0]
            for entry
            in timed_subtitles
        ]

        created_subtitles = [
            entry[1]
            for entry
            in timed_subtitles
        ]

        prompt = "Translating from %8s to %8s   : " %(args.src_language, args.dst_language)

        pbar = ProgressBar(
                widgets=[
                prompt,
                Percentage(),
                " ",
                Bar(),
                " ",
                ETA()
            ],
            maxval=len(
                created_subtitles
            )
        ).start()

        # --------------------------------------------------------
        # IMPORTANT:
        #
        # SOURCE = args.src_language
        # DESTINATION = args.dst_language
        #
        # This fixes the reversed src/dst bug in the old code.
        # --------------------------------------------------------

        translator = SentenceTranslator(
            src=args.src_language,
            dst=args.dst_language,
            endpoint_config=endpoint_config,
            patience=-1,
            timeout=30,
            error_messages_callback=show_error_messages
        )

        translated_subtitles = (
            await translate_subtitles(
                created_subtitles,
                translator,
                args.concurrency
            )
        )

        pbar.finish()
        pbar = None

        subtitle_file_base, _ = (
            os.path.splitext(
                subtitle_filepath
            )
        )

        translated_subtitle_filepath = (
            "{}.translated.{}"
            .format(
                subtitle_file_base,
                subtitle_format
            )
        )

        translation_writer = SubtitleWriter(
            created_regions,
            translated_subtitles,
            subtitle_format,
            error_messages_callback=show_error_messages
        )

        await translation_writer.write(
            translated_subtitle_filepath
        )

    # ============================================================
    # CLEAN WAV
    # ============================================================

    try:
        os.remove(
            wav_filepath
        )
    except Exception:
        pass

    # ============================================================
    # DONE
    # ============================================================

    print(
        "Done."
    )

    if translated_subtitle_filepath:

        print(
            "Original subtitles file created at      : {}"
            .format(
                subtitle_filepath
            )
        )

        print(
            "Translated subtitles file created at    : {}"
            .format(
                translated_subtitle_filepath
            )
        )

    else:

        print(
            "Subtitles file created at               : {}"
            .format(
                subtitle_filepath
            )
        )


# ================================================================
# MAIN
# ================================================================

async def main():

    global pbar

    # ============================================================
    # CLEAN OLD FFMPEG PROCESSES
    # ============================================================

    if sys.platform == "win32":

        stop_ffmpeg_windows(
            error_messages_callback=
                show_error_messages
        )

    else:

        stop_ffmpeg_linux(
            error_messages_callback=
                show_error_messages
        )

    # ============================================================
    # ARGUMENT PARSER
    # ============================================================

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "source_path",
        help=(
            "File path of the video or audio files "
            "to generate subtitles"
        ),
        nargs="*"
    )

    parser.add_argument(
        "-S",
        "--src-language",
        help=(
            "Language code of the audio language "
            "spoken in source"
        ),
        default="en"
    )

    parser.add_argument(
        "-D",
        "--dst-language",
        help=(
            "Desired translation language code"
        ),
        default=None
    )

    parser.add_argument(
        "-ll",
        "--list-languages",
        help=(
            "List all supported languages"
        ),
        action="store_true"
    )

    parser.add_argument(
        "-o",
        "--output",
        help=(
            "Output file path for subtitles"
        )
    )

    parser.add_argument(
        "-F",
        "--format",
        help=(
            "Desired subtitle format"
        ),
        default="srt"
    )

    parser.add_argument(
        "-lf",
        "--list-formats",
        help=(
            "List all supported subtitle formats"
        ),
        action="store_true"
    )

    parser.add_argument(
        "-C",
        "--concurrency",
        help=(
            "Number of concurrent API/FFmpeg "
            "requests"
        ),
        type=int,
        default=DEFAULT_CONCURRENCY
    )

    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=VERSION
    )

    args = parser.parse_args()

    # ============================================================
    # VALIDATE CONCURRENCY
    # ============================================================

    if args.concurrency < 1:

        print(
            "Concurrency must be at least 1."
        )

        return 1

    # ============================================================
    # LANGUAGE
    # ============================================================

    language = Language()

    if args.list_languages:

        print(
            "List of supported languages:"
        )

        for code, name in sorted(
            language.name_of_code.items()
        ):

            print(
                "%8s : %s"
                % (
                    code,
                    name
                )
            )

        return 0

    # ============================================================
    # SOURCE LANGUAGE
    # ============================================================

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
    # DESTINATION LANGUAGE
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

        if not is_same_language(
            args.src_language,
            args.dst_language
        ):

            do_translate = True

    # ============================================================
    # FORMAT
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
    # SOURCE FILE
    # ============================================================

    if not args.source_path:

        parser.print_help(
            sys.stderr
        )

        return 1

    # ============================================================
    # EXPAND WILDCARDS
    # ============================================================

    media_filepaths = []

    for arg in args.source_path:

        matches = glob(
            arg
        )

        # If wildcard does not match anything,
        # retain original path so useful error
        # can be printed below.

        if not matches:

            matches = [arg]

        for filepath in matches:

            if not os.path.isfile(
                filepath
            ):

                print(
                    "{} does not exist"
                    .format(
                        filepath
                    )
                )

                continue

            if (
                is_video_file(filepath)
                or
                is_audio_file(filepath)
            ):

                media_filepaths.append(
                    filepath
                )

            else:

                print(
                    "{} is not a valid "
                    "video or audio file"
                    .format(
                        filepath
                    )
                )

    if not media_filepaths:

        print(
            "No valid media files found."
        )

        return 1

    # ============================================================
    # TEST GOOGLE TRANSLATE ENDPOINT
    #
    # ONLY WHEN TRANSLATION IS ACTUALLY NEEDED.
    # ============================================================

    endpoint_config = None

    if do_translate:

        endpoint_config = (
            test_translation_endpoint(
                args.src_language,
                args.dst_language,
                error_messages_callback=
                    show_error_messages
            )
        )

        if endpoint_config is None:

            print(
                "Translation endpoint is unavailable."
            )

            return 1

    # ============================================================
    # PROCESS ALL MEDIA FILES
    # ============================================================

    try:

        for media_filepath in media_filepaths:

            try:

                await process_media_file(
                    media_filepath,
                    args,
                    endpoint_config
                )

            except KeyboardInterrupt:

                print(
                    "Cancelling all tasks"
                )

                return 1

            except Exception as e:

                print(
                    "Error processing {}:"
                    .format(
                        media_filepath
                    )
                )

                print(e)

                return 1

    finally:

        # --------------------------------------------------------
        # Cleanup
        # --------------------------------------------------------

        if sys.platform == "win32":

            stop_ffmpeg_windows(
                error_messages_callback=
                    show_error_messages
            )

        else:

            stop_ffmpeg_linux(
                error_messages_callback=
                    show_error_messages
            )

        remove_temp_files(
            "flac",
            error_messages_callback=
                show_error_messages
        )

        remove_temp_files(
            "wav",
            error_messages_callback=
                show_error_messages
        )

    return 0


# ================================================================
# ENTRY POINT
# ================================================================

if __name__ == "__main__":

    multiprocessing.freeze_support()

    try:

        exit_code = asyncio.run(
            main()
        )

        sys.exit(
            exit_code
        )

    except KeyboardInterrupt:

        print(
            "\nCancelling all tasks"
        )

        sys.exit(1)
