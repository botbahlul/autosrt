import sys
import multiprocessing
from progressbar import ProgressBar, Percentage, Bar, ETA

from autosrt import Language, WavConverter,  SpeechRegionFinder, FLACConverter, SpeechRecognizer, SentenceTranslator, \
    SubtitleFormatter,  SubtitleWriter

def show_progress(percentage):
    global pbar
    pbar.update(percentage)

def show_error_messages(messages):
    print(messages)

def main():
    global pbar

    media_filepath = "balas budi.mp4"
    src = "zh-CN"
    dst = "id"
    subtitle_format = "srt"

    widgets = ["Converting to a temporary WAV file      : ", Percentage(), ' ', Bar(), ' ', ETA()]
    pbar = ProgressBar(widgets=widgets, maxval=100).start()
    wav_converter = WavConverter(channels=1, rate=48000, progress_callback=show_progress, error_messages_callback=show_error_messages)
    wav_filepath, sample_rate = wav_converter(media_filepath)
    pbar.finish()

    region_finder = SpeechRegionFinder(frame_width=4096, min_region_size=0.5, max_region_size=6, error_messages_callback=show_error_messages)
    regions = region_finder(wav_filepath)

    converter = FLACConverter(wav_filepath=wav_filepath, error_messages_callback=show_error_messages)
    recognizer = SpeechRecognizer(language=src, rate=sample_rate, api_key="AIzaSyBOti4mM-6x9WDnZIjIeyEU21OpBXqWBgw", error_messages_callback=show_error_messages)

    pool = multiprocessing.Pool(10)

    if regions:
        try:
            widgets = ["Converting speech regions to FLAC files : ", Percentage(), ' ', Bar(), ' ', ETA()]
            pbar = ProgressBar(widgets=widgets, maxval=len(regions)).start()
            extracted_regions = []
            for i, extracted_region in enumerate(pool.imap(converter, regions)):
                extracted_regions.append(extracted_region)
                pbar.update(i)
            pbar.finish()

            widgets = ["Performing speech recognition           : ", Percentage(), ' ', Bar(), ' ', ETA()]
            pbar = ProgressBar(widgets=widgets, maxval=len(regions)).start()
            transcripts = []
            for i, transcript in enumerate(pool.imap(recognizer, extracted_regions)):
                transcripts.append(transcript)
                pbar.update(i)
            pbar.finish()

            subtitle_filepath = "harry.srt"
            subtitle_format = "srt"

            writer = SubtitleWriter(regions, transcripts, subtitle_format, error_messages_callback=show_error_messages)
            writer.write(subtitle_filepath)
            timed_subtitles = writer.timed_subtitles

            created_regions = []
            created_subtitles = []
            for entry in timed_subtitles:
                created_regions.append(entry[0])
                created_subtitles.append(entry[1])

            prompt = "Translating from %8s to %8s   : " %(src, dst)
            widgets = [prompt, Percentage(), ' ', Bar(), ' ', ETA()]
            pbar = ProgressBar(widgets=widgets, maxval=len(timed_subtitles)).start()
            transcript_translator = SentenceTranslator(src=src, dst=dst, error_messages_callback=show_error_messages)
            translated_subtitles = []
            for i, translated_subtitle in enumerate(pool.imap(transcript_translator, created_subtitles)):
                translated_subtitles.append(translated_subtitle)
                pbar.update(i)
            pbar.finish()

            translated_subtitle_filepath = subtitle_filepath[ :-4] + '.translated.' + subtitle_format
            translation_writer = SubtitleWriter(created_regions, translated_subtitles, subtitle_format, error_messages_callback=show_error_messages)
            translation_writer.write(translated_subtitle_filepath)

            print('Done.')
            print("Original subtitles file created at      : {}".format(subtitle_filepath))
            print('Translated subtitles file created at    : {}' .format(translated_subtitle_filepath))

        except KeyboardInterrupt:
            pbar.finish()
            pool.terminate()
            pool.close()
            pool.join()
            print("Cancelling transcription")
            sys.exit(1)

        except Exception as e:
            pbar.finish()
            pool.terminate()
            pool.close()
            pool.join()
            print(e)
            sys.exit(1)

if __name__ == '__main__':
    multiprocessing.freeze_support()
    sys.exit(main())
