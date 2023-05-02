import os
import sys
import tempfile
from progressbar import ProgressBar, Percentage, Bar, ETA
from ffmpeg_progress_yield import FfmpegProgress
import wave
import audioop
import math
import asyncio
from functools import partial
import multiprocessing
import subprocess

class WavConverter:
    @staticmethod
    def which(program):
        def is_exe(file_path):
            return os.path.isfile(file_path) and os.access(file_path, os.X_OK)
        fpath, _ = os.path.split(program)
        if fpath:
            if is_exe(program):
                return program
        else:
            for path in os.environ["PATH"].split(os.pathsep):
                path = path.strip('"')
                exe_file = os.path.join(path, program)
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

    def __init__(self, channels=1, rate=48000):
        self.channels = channels
        self.rate = rate

    def __call__(self, media_filepath, progress_callback=None):
        temp = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        if not os.path.isfile(media_filepath):
            print("The given file does not exist: {0}".format(media_filepath))
            raise Exception("Invalid file: {0}".format(media_filepath))
        if not self.ffmpeg_check():
            print("ffmpeg: Executable not found on machine.")
            raise Exception("Dependency not found: ffmpeg")

        command = [
                    "ffmpeg",
                    "-y",
                    "-i", media_filepath,
                    "-ac", str(self.channels),
                    "-ar", str(self.rate),
                    "-loglevel", "error",
                    "-hide_banner",
                    temp.name
                  ]

        try:
            # RUNNING ffmpeg WITHOUT SHOWING PROGRESSS
            #use_shell = True if os.name == "nt" else False
            #subprocess.check_output(command, stdin=open(os.devnull), shell=use_shell)

            # RUNNING ffmpeg WITH PROGRESSS
            ff = FfmpegProgress(command)
            percentage = 0
            for progress in ff.run_command_with_progress():
                percentage = progress
                if progress_callback:
                    progress_callback(percentage)
            temp.close()
        
            return temp.name, self.rate

        except KeyboardInterrupt:
            print("Cancelling transcription")
            return

        except Exception as e:
            print(e)
            return


class SpeechRegionFinder:
    @staticmethod
    def percentile(arr, percent):
        arr = sorted(arr)
        k = (len(arr) - 1) * percent
        f = math.floor(k)
        c = math.ceil(k)
        if f == c: return arr[int(k)]
        d0 = arr[int(f)] * (c - k)
        d1 = arr[int(c)] * (k - f)
        return d0 + d1

    def __init__(self, frame_width=4096, min_region_size=0.5, max_region_size=6):
        self.frame_width = frame_width
        self.min_region_size = min_region_size
        self.max_region_size = max_region_size

    async def __call__(self, wav_filepath):
        try:
            reader = wave.open(wav_filepath)
            sample_width = reader.getsampwidth()
            rate = reader.getframerate()
            n_channels = reader.getnchannels()
            total_duration = reader.getnframes() / rate
            chunk_duration = float(self.frame_width) / rate
            n_chunks = int(total_duration / chunk_duration)
            energies = []
            for i in range(n_chunks):
                chunk = reader.readframes(self.frame_width)
                energies.append(audioop.rms(chunk, sample_width * n_channels))
            threshold = SpeechRegionFinder.percentile(energies, 0.2)
            elapsed_time = 0
            regions = []
            region_start = None
            for energy in energies:
                is_silence = energy <= threshold
                max_exceeded = region_start and elapsed_time - region_start >= self.max_region_size
                if (max_exceeded or is_silence) and region_start:
                    if elapsed_time - region_start >= self.min_region_size:
                        regions.append((region_start, elapsed_time))
                        region_start = None
                elif (not region_start) and (not is_silence):
                    region_start = elapsed_time
                elapsed_time += chunk_duration
            return regions

        except KeyboardInterrupt:
            print("Cancelling transcription")
            return

        except Exception as e:
            print(e)
            return


def show_progress(percentage):
    global pbar
    pbar.update(percentage)


async def main():
    global pbar

    video_filepath = "balas budi.mp4"

    #wav_converter = WavConverter(channels=1, rate=48000)
    wav_converter = WavConverter()
    widgets = ["Converting to a temporary WAV file      : ", Percentage(), ' ', Bar(), ' ', ETA()]
    pbar = ProgressBar(widgets=widgets, maxval=100).start()
    wav_filepath, audio_rate = wav_converter(video_filepath, progress_callback=show_progress)
    pbar.finish()

    print("wav_filepath = {}".format(wav_filepath))
    print("audio_rate = {}".format(audio_rate))

    region_finder = SpeechRegionFinder(frame_width=4096, min_region_size=0.5, max_region_size=6)

    regions = await region_finder(wav_filepath)
    print("regions = {}".format(regions))


if __name__ == '__main__':
    asyncio.run(main())
