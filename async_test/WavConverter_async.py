import os
import sys
import tempfile
from progressbar import ProgressBar, Percentage, Bar, ETA
from ffmpeg_progress_yield import FfmpegProgress
import asyncio
from functools import partial

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

    async def __call__(self, media_filepath, progress_callback=None):
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

    async def convert(self, media_filepath, progress_callback):
        return await self(media_filepath, progress_callback)

    @staticmethod
    async def convert_async(media_filepath, wav_converter, progress_callback):
        loop = asyncio.get_running_loop()
        return await loop.create_task(wav_converter(media_filepath, progress_callback))

def show_progress(percentage):
    global pbar
    pbar.update(percentage)

async def main():
    global pbar

    media_filepath = "balas budi.mp4"

    widgets = ["Converting to a temporary WAV file      : ", Percentage(), ' ', Bar(), ' ', ETA()]
    pbar = ProgressBar(widgets=widgets, maxval=100).start()

    wav_converter = WavConverter()
    wav_converter_partial = partial(wav_converter.convert_async, wav_converter=wav_converter, progress_callback=show_progress)
    wav_filepath, audio_rate = await asyncio.create_task(wav_converter_partial(media_filepath, progress_callback=show_progress))

    pbar.finish()

    print("wav_filepath = {}".format(wav_filepath))
    print("audio_rate = {}".format(audio_rate))

if __name__ == '__main__':
    asyncio.run(main())
