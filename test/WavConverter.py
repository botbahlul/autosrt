from __future__ import absolute_import, print_function, unicode_literals
import os
import tempfile
import subprocess
from ffmpeg_progress_yield import FfmpegProgress
from progressbar import ProgressBar, Percentage, Bar, ETA

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

    def __call__(self, video_filepath, progress_callback=None):
        temp = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        if not os.path.isfile(video_filepath):
            print("The given file does not exist: {0}".format(video_filepath))
            raise Exception("Invalid filepath: {0}".format(video_filepath))
        if not self.ffmpeg_check():
            print("ffmpeg: Executable not found on machine.")
            raise Exception("Dependency not found: ffmpeg")
        command = ["ffmpeg", "-y", "-i", video_filepath, "-ac", str(self.channels), "-ar", str(self.rate), "-loglevel", "error", "-hide_banner", temp.name]
        use_shell = True if os.name == "nt" else False

        #subprocess.check_output(command, stdin=open(os.devnull), shell=use_shell)

        ff = FfmpegProgress(command)
        percentage = 0
        for progress in ff.run_command_with_progress():
            percentage = progress
            if progress_callback:
                progress_callback(percentage)

        return temp.name, self.rate

def show_progress(percentage):
    global pbar
    pbar.update(percentage)

video_filepath = "balas budi.mp4"
#wav_converter = WavConverter(channels=1, rate=48000)
wav_converter = WavConverter()
widgets = ["Converting to a temporary WAV file      : ", Percentage(), ' ', Bar(), ' ', ETA()]
pbar = ProgressBar(widgets=widgets, maxval=100).start()
wav_filepath, SampleRate = wav_converter(video_filepath, progress_callback=show_progress)
pbar.finish()
print(wav_filepath, SampleRate)

