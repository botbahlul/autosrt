import sys
import multiprocessing
from progressbar import ProgressBar, Percentage, Bar, ETA


from autosrt import Language, WavConverter,  SpeechRegionFinder, FLACConverter, SpeechRecognizer, SentenceTranslator, \
    SubtitleFormatter,  SubtitleWriter

# CREATE A progress_callback FUNCTION TO SHOW PROGRESS WHEN CONVERT TO A TEMPORARY WAV FILE
def show_progress(progress):
   global pbar
   pbar.update(progress)


def show_error_messages(messages):
    print(messages)


def main():
    global pbar

    media_filepath = "balas budi.mp4"

    language = Language()

    # ALTERNATIVE 1
    print("List of supported languages:")
    for code in language.dict:
        #print(code, language.get_name(code))
        #print("%8s\t%s" %(code, language.get_name(code)))
        print("%8s : %s" %(code, language.get_name(code)))

    # ALTERNATIVE 2
    #print("List of supported languages:")
    #for code, name in sorted(language.name_of_code.items()):
        #print("{}\t{}".format(code, name))
        #print("%8s %s" %(code, name))


    # ALTERNATIVE 1
    src = "zh-CN"
    src_language_name = language.get_name(src)
    print("src_language_name = {}".format(src_language_name))

    # ALTERNATIVE 2
    #src = "zh-CN"
    #src_language_name = language.name_of_code[src]
    #print("src_language_name = {}".format(src_language_name))


    # ALTERNATIVE 1
    src_language_name = "Chinese (Simplified)"
    src_language_code = language.get_code(src_language_name)
    print("src_language_code = {}".format(src_language_code))

    # ALTERNATIVE 2
    #src_language_name = "Chinese (Simplified)"
    #src_language_code = language.code_of_name[src_language_name]
    #print("src_language_code = {}".format(src_language_code))


    # ALTERNATIVE 1
    dst = "id"
    dst_language_name = language.get_name(dst)
    print("dst_language_name = {}".format(dst_language_name))

    # ALTERNATIVE 2
    #dst = "id"
    #dst_language_name = language.name_of_code[dst]
    #print("dst_language_name = {}".format(dst_language_name))


    # ALTERNATIVE 1
    dst_language_name = "Indonesian"
    dst_language_code = language.get_code(dst_language_name)
    print("dst_language_code = {}".format(dst_language_code))

    # ALTERNATIVE 2
    #dst_language_name = "Indonesian"
    #dst_language_code = language.code_of_name[dst_language_name]
    #print("dst_language_code = {}".format(dst_language_code))


    # CONVERT MEDIA FILE TO A TEMPORARY WAV FILE

    # CONVERT WITHOUT SHOWING THE PROGRESS
    #wav_converter = WavConverter(channels=1, rate=48000, progress_callback=None, error_messages_callback=show_error_messages)
    #wav_filepath, sample_rate = wav_converter(media_filepath)

    # CONVERT WITH SHOWING THE PROGRESS
    wav_converter = WavConverter(channels=1, rate=48000, progress_callback=show_progress, error_messages_callback=show_error_messages)
    widgets = ["Converting to a temporary WAV file      : ", Percentage(), ' ', Bar(), ' ', ETA()]
    pbar = ProgressBar(widgets=widgets, maxval=100).start()
    wav_filepath, sample_rate = wav_converter(media_filepath)
    pbar.finish()

    print("wav_filepath = {}".format(wav_filepath))
    print("sample_rate = {}".format(sample_rate))


    # FIND SPEECH REGIONS OF TEMPORARY WAV FILE
    region_finder = SpeechRegionFinder(frame_width=4096, min_region_size=0.5, max_region_size=6, error_messages_callback=show_error_messages)
    regions = region_finder(wav_filepath)
    print("regions = {}".format(regions))


    # PREPARE FOR SPEECH RECOGNITION PROGRESS
    converter = FLACConverter(wav_filepath=wav_filepath, error_messages_callback=show_error_messages)
    recognizer = SpeechRecognizer(language=src, rate=sample_rate, api_key="AIzaSyBOti4mM-6x9WDnZIjIeyEU21OpBXqWBgw", error_messages_callback=show_error_messages)

    pool = multiprocessing.Pool(10)

    # GET AUDIO DATA OF EACH REGIONS (CONTENT OF TEMPORARY FLAC FILES)
    extracted_regions = []
    for i, extracted_region in enumerate(pool.imap(converter, regions)):
        print("Get region {} audio data".format(i))
        extracted_regions.append(extracted_region)

    # GET TRANSCRIPTIONS OF EACH FLAC FILES
    transcripts = []
    for i, transcript in enumerate(pool.imap(recognizer, extracted_regions)):
        print("region[{}] transcript = {}".format(i, transcript))
        transcripts.append(transcript)


    # WRITING SUBTITLE FILES
    print("List of supported subtitle format")
    for subtitle_format in SubtitleFormatter.supported_formats:
        print(subtitle_format)

    # CREATING SUBTITLES TUPLE = [((start_time1, elapsed_time1), transcripts1), ((start_time2, elapsed_time2), transcripts2), ...]
    timed_subtitles = [(r, t) for r, t in zip(regions, transcripts) if t]
    for timed_subtitle in timed_subtitles:
        print(timed_subtitle)


    # ALTERNATIVE 1 TO WRITE SUBTITLE FILE
    subtitle_format = "srt"
    formatter = SubtitleFormatter(subtitle_format)
    formatted_subtitles = formatter(timed_subtitles)

    subtitle_filepath = "harry.srt"
    with open(subtitle_filepath, 'wb') as f:
        f.write(formatted_subtitles.encode("utf-8"))
    with open(subtitle_filepath, 'a') as f:
        f.write("\n")


    # ALTERNATIVE 2 TO WRITE SUBTITLE FILE, USING SubtitleWriter CLASS
    #writer = SubtitleWriter(regions, transcripts, subtitle_format)
    #writer.write(subtitle_filepath)
    #timed_subtitles = writer.timed_subtitles


    # CREATING TRANSLATED SUBTITLE FILE
    created_regions = []
    created_subtitles = []
    for entry in timed_subtitles:
        created_regions.append(entry[0])
        created_subtitles.append(entry[1])

    transcript_translator = SentenceTranslator(src=src, dst=dst)
    translated_subtitles = []
    for i, translated_subtitle in enumerate(pool.imap(transcript_translator, created_subtitles)):
        print("created_regions[{}] translated_subtitle = {}".format(i, translated_subtitle))
        translated_subtitles.append(translated_subtitle)

    # ALTERNATIVE 1 TO WRITE TRANSLATED SUBTITLE FILE
    timed_translated_subtitles = [(r, t) for r, t in zip(created_regions, translated_subtitles) if t]
    for timed_translated_subtitle in timed_translated_subtitles:
        print(timed_translated_subtitle)
    formatter = SubtitleFormatter(subtitle_format)
    formatted_translated_subtitles = formatter(timed_translated_subtitles)

    translated_subtitle_filepath = subtitle_filepath[ :-4] + '.translated.' + subtitle_format
    with open(translated_subtitle_filepath, 'wb') as tf:
        tf.write(formatted_translated_subtitles.encode("utf-8"))
    with open(translated_subtitle_filepath, 'a') as tf:
        tf.write("\n")

    # ALTERNATIVE 2 TO WRITE TRANSLATED SUBTITLE FILE USING SubtitleWriter CLASS
    #translation_writer = SubtitleWriter(created_regions, translated_subtitles, subtitle_format)
    #translation_writer.write(translated_subtitle_filepath)

    print('Done.')
    print("Original subtitles file created at      : {}".format(subtitle_filepath))
    print('Translated subtitles file created at    : {}' .format(translated_subtitle_filepath))


if __name__ == '__main__':
    multiprocessing.freeze_support()
    sys.exit(main())
