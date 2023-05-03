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

    def __init__(self, channels=1, rate=48000, progress_callback=None, error_messages_callback=None):
        self.channels = channels
        self.rate = rate
        self.progress_callback = progress_callback
        self.error_messages_callback = error_messages_callback

    async def __call__(self, media_filepath):
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
                if self.progress_callback:
                    self.progress_callback(percentage)
            temp.close()

            return temp.name, self.rate

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

    async def convert(self, media_filepath):
        return await self(media_filepath, self.progress_callback)

    @staticmethod
    async def convert_async(media_filepath, wav_converter):
        loop = asyncio.get_running_loop()
        return await loop.create_task(wav_converter(media_filepath))


def show_progress(percentage):
    global pbar
    pbar.update(percentage)

def show_error_messages(messages):
    print(messages)

async def main():
    global pbar

    media_filepath = "balas budi.mp4"

    widgets = ["Converting to a temporary WAV file      : ", Percentage(), ' ', Bar(), ' ', ETA()]
    pbar = ProgressBar(widgets=widgets, maxval=100).start()
    wav_converter = WavConverter(channels=1, rate=48000, progress_callback=show_progress, error_messages_callback=show_error_messages)
    wav_converter_partial = partial(wav_converter.convert_async, wav_converter=wav_converter)
    wav_filepath, sample_rate = await asyncio.create_task(wav_converter_partial(media_filepath))
    pbar.finish()
    print("wav_filepath = {}".format(wav_filepath))
    print("sample_rate = {}".format(sample_rate))

if __name__ == '__main__':
    asyncio.run(main())
