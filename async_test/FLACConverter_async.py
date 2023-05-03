import asyncio
import os
import sys
import wave
import audioop
import math
import subprocess
import tempfile
from progressbar import ProgressBar, Percentage, Bar, ETA
from ffmpeg_progress_yield import FfmpegProgress
import multiprocessing
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

    def __init__(self, frame_width=4096, min_region_size=0.5, max_region_size=6, error_messages_callback=None):
        self.frame_width = frame_width
        self.min_region_size = min_region_size
        self.max_region_size = max_region_size
        self.error_messages_callback = error_messages_callback

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


class FLACConverter:
    def __init__(self, wav_filepath, include_before=0.25, include_after=0.25, error_messages_callback=None):
        self.wav_filepath = wav_filepath
        self.include_before = include_before
        self.include_after = include_after
        self.error_messages_callback = error_messages_callback

    async def __call__(self, region):
        try:
            start, end = region
            start = max(0, start - self.include_before)
            end += self.include_after
            temp = tempfile.NamedTemporaryFile(suffix='.flac', delete=False)
            command = [
                        "ffmpeg",
                        "-ss", str(start),
                        "-t", str(end - start),
                        "-y",
                        "-i", self.wav_filepath,
                        "-loglevel", "error",
                        temp.name
                      ]
            process = await asyncio.create_subprocess_exec(*command, stdin=subprocess.DEVNULL)
            await process.communicate()
            content = temp.read()
            temp.close()
            return content

        except asyncio.CancelledError:
            if self.error_messages_callback:
                self.error_messages_callback("Cancelling all tasks")
            else:
                print("Cancelling all tasks")
            return

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


    async def convert(regions, flac_converter):
        return await flac_converter(regions)

    @staticmethod
    def convert_async(regions, flac_converter):
        return asyncio.run(FLACConverter.convert(regions, flac_converter))


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

    region_finder = SpeechRegionFinder(frame_width=4096, min_region_size=0.5, max_region_size=6, error_messages_callback=show_error_messages)
    regions = await region_finder(wav_filepath)
    print("regions = {}".format(regions))
    #regions = [(0.08533333333333333, 0.8533333333333335), (1.0240000000000002, 1.7066666666666663), (2.0479999999999996, 2.901333333333332), (2.9866666666666655, 4.351999999999999), (4.437333333333333, 5.97333333333334), (6.485333333333342, 7.253333333333345), (7.338666666666679, 7.936000000000015), (8.277333333333347, 9.984000000000004), (10.069333333333336, 11.861333333333326), (11.946666666666658, 13.994666666666646), (14.250666666666644, 15.530666666666637), (16.469333333333307, 17.49333333333332), (17.919999999999995, 18.432000000000002), (18.60266666666667, 19.797333333333356), (20.138666666666694, 21.504000000000048), (21.845333333333386, 23.637333333333412), (23.893333333333416, 24.832000000000097), (25.25866666666677, 26.02666666666678), (26.36800000000012, 27.64800000000014), (27.904000000000142, 29.440000000000165), (29.781333333333503, 30.976000000000187), (31.061333333333522, 31.57333333333353), (31.7440000000002, 33.280000000000165), (33.53600000000016, 34.81600000000012), (34.901333333333454, 35.41333333333344), (35.5840000000001, 37.97333333333337), (38.57066666666669, 40.618666666666634), (41.30133333333328, 43.0079999999999), (43.263999999999896, 44.799999999999855), (45.05599999999985, 46.8479999999998), (47.10399999999979, 49.06666666666641), (49.57866666666639, 50.94399999999969), (51.02933333333302, 52.223999999999656), (52.39466666666632, 53.845333333332945), (54.10133333333294, 55.12533333333291), (55.29599999999957, 55.80799999999956), (55.97866666666622, 57.002666666666194), (57.087999999999525, 58.19733333333283), (58.28266666666616, 58.794666666666146), (58.96533333333281, 59.73333333333279), (60.07466666666611, 60.84266666666609), (61.01333333333275, 62.037333333332725), (62.122666666666056, 62.97599999999937), (63.23199999999936, 64.51199999999936), (64.68266666666604, 66.30399999999946), (66.47466666666614, 68.60799999999959), (68.8639999999996, 69.37599999999964), (69.71733333333299, 70.91199999999972), (70.99733333333306, 71.50933333333309), (71.93599999999978, 72.70399999999982), (72.78933333333316, 73.81333333333322), (73.9839999999999, 74.58133333333326), (74.6666666666666, 76.11733333333335), (76.20266666666669, 77.65333333333344), (77.73866666666677, 78.42133333333348), (78.6773333333335, 80.38400000000026), (80.98133333333362, 82.00533333333368), (82.43200000000037, 83.79733333333378), (84.13866666666713, 85.8453333333339), (86.10133333333391, 87.46666666666732), (88.06400000000069, 89.25866666666742), (89.60000000000078, 90.96533333333419), (91.05066666666752, 91.81866666666757), (91.9040000000009, 93.18400000000098), (93.52533333333433, 95.06133333333442), (95.57333333333445, 96.5973333333345), (96.68266666666784, 97.45066666666789), (97.53600000000122, 98.04800000000125), (98.13333333333459, 99.07200000000131), (99.15733333333465, 101.20533333333476), (101.54666666666812, 103.0826666666682), (103.25333333333488, 109.31200000000189), (109.39733333333523, 110.59200000000196), (111.18933333333533, 112.55466666666874), (113.06666666666877, 114.09066666666882), (114.17600000000216, 115.11466666666888), (115.3706666666689, 116.0533333333356), (116.13866666666894, 116.65066666666897), (116.82133333333564, 118.18666666666905), (118.69866666666908, 119.97866666666916), (120.32000000000251, 121.51466666666924), (121.8560000000026, 123.81866666666937), (123.98933333333605, 125.18400000000278), (125.78133333333615, 126.89066666666955), (126.97600000000288, 127.57333333333625), (127.82933333333627, 128.5973333333362), (128.68266666666952, 129.2800000000028), (129.3653333333361, 130.389333333336), (130.47466666666932, 132.43733333333577), (132.94933333333572, 133.9733333333356), (134.05866666666893, 134.9973333333355), (135.25333333333546, 135.7653333333354), (135.85066666666873, 136.61866666666864), (136.70400000000197, 137.47200000000188), (137.81333333333518, 138.83733333333507)]

    flac_converter = FLACConverter(wav_filepath=wav_filepath, error_messages_callback=show_error_messages)
    flac_converter_partial = partial(flac_converter.convert_async, flac_converter=flac_converter)

    pool = multiprocessing.Pool(10)
    widgets = ["Converting speech regions to FLAC files : ", Percentage(), ' ', Bar(), ' ', ETA()]
    pbar = ProgressBar(widgets=widgets, maxval=len(regions)).start()
    extracted_regions = []
    for i, extracted_region in enumerate(pool.imap(flac_converter_partial, regions)):
        extracted_regions.append(extracted_region)
        pbar.update(i)
    pbar.finish()
    print("Done.")

    pool.close()
    pool.join()


if __name__ == '__main__':
    multiprocessing.freeze_support()
    sys.exit(asyncio.run(main()))
