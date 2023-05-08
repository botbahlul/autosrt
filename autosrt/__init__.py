#!/usr/bin/env python3.8
from __future__ import absolute_import, print_function, unicode_literals
import argparse
import os
import sys
import multiprocessing
from glob import glob
from progressbar import ProgressBar, Percentage, Bar, ETA

from .autosrt import VERSION, Language, WavConverter,  SpeechRegionFinder, FLACConverter, SpeechRecognizer, SentenceTranslator, \
    SubtitleFormatter,  SubtitleWriter, \
    stop_ffmpeg_windows, stop_ffmpeg_linux, remove_temp_files, is_same_language, is_video_file, is_audio_file

def show_progress(media_filepath, progress):
    global pbar
    pbar.update(progress)

def show_error_messages(messages):
    print(messages)

def main():
    global pbar

    if sys.platform == "win32":
        stop_ffmpeg_windows(error_messages_callback=show_error_messages)
    else:
        stop_ffmpeg_linux(error_messages_callback=show_error_messages)

    remove_temp_files("flac", error_messages_callback=show_error_messages)
    remove_temp_files("wav", error_messages_callback=show_error_messages)

    parser = argparse.ArgumentParser()
    parser.add_argument('source_path', help="Path to the video or audio files to generate subtitles files (use wildcard for multiple files or separate them with a space character e.g. \"file 1.mp4\" \"file 2.mp4\")", nargs='*')
    parser.add_argument('-S', '--src-language', help="Language code of the audio language spoken in video/audio source_path", default="en")
    parser.add_argument('-D', '--dst-language', help="Desired translation language code for the subtitles", default=None)
    parser.add_argument('-ll', '--list-languages', help="List all supported languages", action='store_true')
    parser.add_argument('-o', '--output', help="Output file path for subtitles (by default, subtitles are saved in the same directory and named with the source_path base name)")
    parser.add_argument('-F', '--format', help="Desired subtitle format", default="srt")
    parser.add_argument('-lf', '--list-formats', help="List all supported subtitle formats", action='store_true')
    parser.add_argument('-C', '--concurrency', help="Number of concurrent API requests to make", type=int, default=10)
    parser.add_argument('-v', '--version', action='version', version=VERSION)

    args = parser.parse_args()

    language = Language()

    if args.list_languages:
        print("List of supported languages:")
        for code, language in sorted(language.name_of_code.items()):
            #print("{code}\t{language}".format(code=code, language=language))
            #print("%8s\t%s" %(code, language))
            print("%8s : %s" %(code, language))
        return 0

    #if args.src_language not in language.dict:
    if args.src_language not in language.name_of_code.keys():
        print("Source language is not supported. Run with --list-languages to see all supported languages.")
        return 1

    if args.dst_language:
        #if not args.dst_language in language.dict:
        if not args.dst_language in language.name_of_code.keys():
            print("Destination language is not supported. Run with --list-languages to see all supported languages.")
            return 1
        if not is_same_language(args.src_language, args.dst_language, error_messages_callback=show_error_messages):
            do_translate = True
        else:
            do_translate = False
    else:
        do_translate = False

    if args.list_formats:
        print("List of supported subtitle formats:")
        for subtitle_format in SubtitleFormatter.supported_formats:
            print("{format}".format(format=subtitle_format))
        return 0

    if args.format not in SubtitleFormatter.supported_formats:
        print("Subtitle format is not supported. Run with --list-formats to see all supported formats.")
        return 1

    if not args.source_path:
        parser.print_help(sys.stderr)
        return 1

    media_filepaths = []
    arg_filepaths = []

    for arg in args.source_path:
        if not os.sep in arg:
            argpath = os.path.join(os.getcwd(),arg)
        else:
            argpath = arg
        arg_filepaths += glob(argpath)

    for argpath in arg_filepaths:
        if os.path.isfile(argpath):
            if is_video_file(argpath, error_messages_callback=show_error_messages) or is_audio_file(argpath, error_messages_callback=show_error_messages):
                media_filepaths.append(argpath)
            else:
                print("{} is not a valid video or audio file".format(argpath))
        else:
            print("{} is not exist".format(argpath))

    pool = multiprocessing.Pool(args.concurrency)

    for media_filepath in media_filepaths:
        print("Processing {} :".format(media_filepath))

        try:
            widgets = ["Converting to a temporary WAV file      : ", Percentage(), ' ', Bar(), ' ', ETA()]
            pbar = ProgressBar(widgets=widgets, maxval=100).start()
            wav_converter = WavConverter(progress_callback=show_progress, error_messages_callback=show_error_messages)
            wav_filepath, sample_rate = wav_converter(media_filepath)
            pbar.finish()

            region_finder = SpeechRegionFinder(frame_width=4096, min_region_size=0.5, max_region_size=6, error_messages_callback=show_error_messages)
            regions = region_finder(wav_filepath)

            converter = FLACConverter(wav_filepath=wav_filepath, error_messages_callback=show_error_messages)
            recognizer = SpeechRecognizer(language=args.src_language, rate=sample_rate, api_key="AIzaSyBOti4mM-6x9WDnZIjIeyEU21OpBXqWBgw", error_messages_callback=show_error_messages)

            if regions:
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

                subtitle_filepath = args.output
                subtitle_format = args.format
                # HANDLE IF THERE ARE SOME TYPOS IN SUBTITLE FILENAME
                if subtitle_filepath:
                    subtitle_file_base, subtitle_file_ext = os.path.splitext(args.output)
                    if not subtitle_file_ext:
                        subtitle_filepath = "{base}.{format}".format(base=subtitle_file_base, format=subtitle_format)
                    else:
                        subtitle_filepath = args.output
                else:
                    base, ext = os.path.splitext(media_filepath)
                    subtitle_filepath = "{base}.{format}".format(base=base, format=subtitle_format)

                writer = SubtitleWriter(regions, transcripts, subtitle_format, error_messages_callback=show_error_messages)
                writer.write(subtitle_filepath)

                if do_translate:
                    # CONCURRENT TRANSLATION USING class SentenceTranslator(object)
                    # NO NEED TO TRANSLATE ALL transcript IN transcripts
                    # BECAUSE SOME region IN regions MAY JUST HAVE transcript WITH EMPTY STRING
                    # JUST TRANSLATE ALREADY CREATED subtitles ENTRIES FROM timed_subtitles
                    timed_subtitles = writer.timed_subtitles
                    created_regions = []
                    created_subtitles = []
                    for entry in timed_subtitles:
                        created_regions.append(entry[0])
                        created_subtitles.append(entry[1])

                    prompt = "Translating from %8s to %8s   : " %(args.src_language, args.dst_language)
                    widgets = [prompt, Percentage(), ' ', Bar(), ' ', ETA()]
                    pbar = ProgressBar(widgets=widgets, maxval=len(timed_subtitles)).start()

                    transcript_translator = SentenceTranslator(src=args.src_language, dst=args.dst_language, error_messages_callback=show_error_messages)

                    translated_subtitles = []
                    for i, translated_subtitle in enumerate(pool.imap(transcript_translator, created_subtitles)):
                        translated_subtitles.append(translated_subtitle)
                        pbar.update(i)
                    pbar.finish()

                    translated_subtitle_filepath = subtitle_filepath[ :-4] + '.translated.' + subtitle_format
                    translation_writer = SubtitleWriter(created_regions, translated_subtitles, subtitle_format, error_messages_callback=show_error_messages)
                    translation_writer.write(translated_subtitle_filepath)

                print('Done.')
                if do_translate:
                    print("Original subtitles file created at      : {}".format(subtitle_filepath))
                    print('Translated subtitles file created at    : {}' .format(translated_subtitle_filepath))
                else:
                    print("Subtitles file created at               : {}".format(subtitle_filepath))

        except KeyboardInterrupt:
            pbar.finish()
            pool.terminate()
            pool.close()
            pool.join()
            print("Cancelling all tasks")

            if sys.platform == "win32":
                stop_ffmpeg_windows(error_messages_callback=show_error_messages)
            else:
                stop_ffmpeg_linux(error_messages_callback=show_error_messages)

            remove_temp_files("flac")
            remove_temp_files("wav")
            return 1

        except Exception as e:
            if not KeyboardInterrupt in e:
                pbar.finish()
                pool.terminate()
                pool.close()
                pool.join()
                print(e)

                if sys.platform == "win32":
                    stop_ffmpeg_windows(error_messages_callback=show_error_messages)
                else:
                    stop_ffmpeg_linux(error_messages_callback=show_error_messages)

                remove_temp_files("flac")
                remove_temp_files("wav")
                return 1

    if pool:
        pool.close()
        pool.join()
        pool = None

    if sys.platform == "win32":
        stop_ffmpeg_windows(error_messages_callback=show_error_messages)
    else:
        stop_ffmpeg_linux(error_messages_callback=show_error_messages)

    remove_temp_files("flac")
    remove_temp_files("wav")

if __name__ == '__main__':
    multiprocessing.freeze_support()
    sys.exit(main())
