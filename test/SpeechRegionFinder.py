import wave
import audioop
import math

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

    def __call__(self, wav_filepath):
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


region_finder = SpeechRegionFinder(frame_width=4096, min_region_size=0.5, max_region_size=6)
wav_filepath = '/tmp/tmpscxc5z6o.wav'
regions = region_finder(wav_filepath)
print(regions)
