#!/usr/bin/env python
from __future__ import absolute_import, print_function, unicode_literals

import argparse
import audioop
import math
import multiprocessing
import os
import subprocess
import sys
import tempfile
import wave
import json
import requests
try:
    from json.decoder import JSONDecodeError
except ImportError:
    JSONDecodeError = ValueError

from googleapiclient.discovery import build
from progressbar import ProgressBar, Percentage, Bar, ETA
from googletrans import Translator
import pysrt
import six

GOOGLE_SPEECH_API_KEY = "AIzaSyBOti4mM-6x9WDnZIjIeyEU21OpBXqWBgw"
GOOGLE_SPEECH_API_URL = "http://www.google.com/speech-api/v2/recognize?client=chromium&lang={lang}&key={key}" # pylint: disable=line-too-long
DEFAULT_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'

LANGUAGES = {
    'af': 'afrikaans',
    'sq': 'albanian',
    'am': 'amharic',
    'ar': 'arabic',
    'hy': 'armenian',
    'az': 'azerbaijani',
    'eu': 'basque',
    'be': 'belarusian',
    'bn': 'bengali',
    'bs': 'bosnian',
    'bg': 'bulgarian',
    'ca': 'catalan',
    'ceb': 'cebuano',
    'ny': 'chichewa',
    'zh-cn': 'chinese (simplified)',
    'zh-tw': 'chinese (traditional)',
    'co': 'corsican',
    'hr': 'croatian',
    'cs': 'czech',
    'da': 'danish',
    'nl': 'dutch',
    'en': 'english',
    'eo': 'esperanto',
    'et': 'estonian',
    'tl': 'filipino',
    'fi': 'finnish',
    'fr': 'french',
    'fy': 'frisian',
    'gl': 'galician',
    'ka': 'georgian',
    'de': 'german',
    'el': 'greek',
    'gu': 'gujarati',
    'ht': 'haitian creole',
    'ha': 'hausa',
    'haw': 'hawaiian',
    'iw': 'hebrew',
    'he': 'hebrew',
    'hi': 'hindi',
    'hmn': 'hmong',
    'hu': 'hungarian',
    'is': 'icelandic',
    'ig': 'igbo',
    'id': 'indonesian',
    'ga': 'irish',
    'it': 'italian',
    'ja': 'japanese',
    'jw': 'javanese',
    'kn': 'kannada',
    'kk': 'kazakh',
    'km': 'khmer',
    'ko': 'korean',
    'ku': 'kurdish (kurmanji)',
    'ky': 'kyrgyz',
    'lo': 'lao',
    'la': 'latin',
    'lv': 'latvian',
    'lt': 'lithuanian',
    'lb': 'luxembourgish',
    'mk': 'macedonian',
    'mg': 'malagasy',
    'ms': 'malay',
    'ml': 'malayalam',
    'mt': 'maltese',
    'mi': 'maori',
    'mr': 'marathi',
    'mn': 'mongolian',
    'my': 'myanmar (burmese)',
    'ne': 'nepali',
    'no': 'norwegian',
    'or': 'odia',
    'ps': 'pashto',
    'fa': 'persian',
    'pl': 'polish',
    'pt': 'portuguese',
    'pa': 'punjabi',
    'ro': 'romanian',
    'ru': 'russian',
    'sm': 'samoan',
    'gd': 'scots gaelic',
    'sr': 'serbian',
    'st': 'sesotho',
    'sn': 'shona',
    'sd': 'sindhi',
    'si': 'sinhala',
    'sk': 'slovak',
    'sl': 'slovenian',
    'so': 'somali',
    'es': 'spanish',
    'su': 'sundanese',
    'sw': 'swahili',
    'sv': 'swedish',
    'tg': 'tajik',
    'ta': 'tamil',
    'te': 'telugu',
    'th': 'thai',
    'tr': 'turkish',
    'uk': 'ukrainian',
    'ur': 'urdu',
    'ug': 'uyghur',
    'uz': 'uzbek',
    'vi': 'vietnamese',
    'cy': 'welsh',
    'xh': 'xhosa',
    'yi': 'yiddish',
    'yo': 'yoruba',
    'zu': 'zulu',
}

LANGUAGE_CODES = {
    'af': 'Afrikaans',
    'ar': 'Arabic',
    'az': 'Azerbaijani',
    'be': 'Belarusian',
    'bg': 'Bulgarian',
    'bn': 'Bengali',
    'bs': 'Bosnian',
    'ca': 'Catalan',
    'ceb': 'Cebuano',
    'cs': 'Czech',
    'cy': 'Welsh',
    'da': 'Danish',
    'de': 'German',
    'el': 'Greek',
    'en': 'English',
    'eo': 'Esperanto',
    'es': 'Spanish',
    'et': 'Estonian',
    'eu': 'Basque',
    'fa': 'Persian',
    'fi': 'Finnish',
    'fr': 'French',
    'ga': 'Irish',
    'gl': 'Galician',
    'gu': 'Gujarati',
    'ha': 'Hausa',
    'hi': 'Hindi',
    'hmn': 'Hmong',
    'hr': 'Croatian',
    'ht': 'Haitian Creole',
    'hu': 'Hungarian',
    'hy': 'Armenian',
    'id': 'Indonesian',
    'ig': 'Igbo',
    'is': 'Icelandic',
    'it': 'Italian',
    'iw': 'Hebrew',
    'ja': 'Japanese',
    'jw': 'Javanese',
    'ka': 'Georgian',
    'kk': 'Kazakh',
    'km': 'Khmer',
    'kn': 'Kannada',
    'ko': 'Korean',
    'la': 'Latin',
    'lo': 'Lao',
    'lt': 'Lithuanian',
    'lv': 'Latvian',
    'mg': 'Malagasy',
    'mi': 'Maori',
    'mk': 'Macedonian',
    'ml': 'Malayalam',
    'mn': 'Mongolian',
    'mr': 'Marathi',
    'ms': 'Malay',
    'mt': 'Maltese',
    'my': 'Myanmar (Burmese)',
    'ne': 'Nepali',
    'nl': 'Dutch',
    'no': 'Norwegian',
    'ny': 'Chichewa',
    'pa': 'Punjabi',
    'pl': 'Polish',
    'pt': 'Portuguese',
    'ro': 'Romanian',
    'ru': 'Russian',
    'si': 'Sinhala',
    'sk': 'Slovak',
    'sl': 'Slovenian',
    'so': 'Somali',
    'sq': 'Albanian',
    'sr': 'Serbian',
    'st': 'Sesotho',
    'su': 'Sudanese',
    'sv': 'Swedish',
    'sw': 'Swahili',
    'ta': 'Tamil',
    'te': 'Telugu',
    'tg': 'Tajik',
    'th': 'Thai',
    'tl': 'Filipino',
    'tr': 'Turkish',
    'uk': 'Ukrainian',
    'ur': 'Urdu',
    'uz': 'Uzbek',
    'vi': 'Vietnamese',
    'yi': 'Yiddish',
    'yo': 'Yoruba',
    'zh-CN': 'Chinese (Simplified)',
    'zh-TW': 'Chinese (Traditional)',
    'zu': 'Zulu',
}

def srt_formatter(subtitles, padding_before=0, padding_after=0):
    """
    Serialize a list of subtitles according to the SRT format, with optional time padding.
    """
    sub_rip_file = pysrt.SubRipFile()
    for i, ((start, end), text) in enumerate(subtitles, start=1):
        item = pysrt.SubRipItem()
        item.index = i
        item.text = six.text_type(text)
        item.start.seconds = max(0, start - padding_before)
        item.end.seconds = end + padding_after
        sub_rip_file.append(item)
    return '\n'.join(six.text_type(item) for item in sub_rip_file)


FORMATTERS = {
    'srt': srt_formatter,
}


def percentile(arr, percent):
    arr = sorted(arr)
    k = (len(arr) - 1) * percent
    f = math.floor(k)
    c = math.ceil(k)
    if f == c: return arr[int(k)]
    d0 = arr[int(f)] * (c - k)
    d1 = arr[int(c)] * (k - f)
    return d0 + d1


def is_same_language(lang1, lang2):
    return lang1.split("-")[0] == lang2.split("-")[0]


class FLACConverter(object):
    def __init__(self, source_path, include_before=0.25, include_after=0.25):
        self.source_path = source_path
        self.include_before = include_before
        self.include_after = include_after

    def __call__(self, region):
        try:
            start, end = region
            start = max(0, start - self.include_before)
            end += self.include_after
            temp = tempfile.NamedTemporaryFile(suffix='.flac', delete=False)
            command = ["ffmpeg","-ss", str(start), "-t", str(end - start), "-y", "-i", self.source_path, "-loglevel", "error", temp.name]
            subprocess.check_output(command, stdin=open(os.devnull))
            return temp.read()

        except KeyboardInterrupt:
            return


class SpeechRecognizer(object):
    def __init__(self, language="en", rate=44100, retries=3, api_key=GOOGLE_SPEECH_API_KEY):
        self.language = language
        self.rate = rate
        self.api_key = api_key
        self.retries = retries

    def __call__(self, data):
        try:
            for i in range(self.retries):
                url = GOOGLE_SPEECH_API_URL.format(lang=self.language, key=self.api_key)
                headers = {"Content-Type": "audio/x-flac; rate=%d" % self.rate}

                try:
                    resp = requests.post(url, data=data, headers=headers)
                except requests.exceptions.ConnectionError:
                    continue

                #for line in resp.content.split("\n"):
                for line in resp.content.decode('utf-8').split("\n"):
                    try:
                        line = json.loads(line)
                        line = line['result'][0]['alternative'][0]['transcript']
                        return line[:1].upper() + line[1:]
                    except:
                        # no result
                        continue

        except KeyboardInterrupt:
            return


def which(program):
    """
    Return the path for a given executable.
    """
    def is_exe(file_path):
        """
        Checks whether a file is executable.
        """
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


def ffmpeg_check():
    """
    Return the ffmpeg executable name. "None" returned when no executable exists.
    """
    if which("ffmpeg"):
        return "ffmpeg"
    if which("ffmpeg.exe"):
        return "ffmpeg.exe"
    return None


def extract_audio(filename, channels=1, rate=16000):
    temp = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
    if not os.path.isfile(filename):
        print("The given file does not exist: {0}".format(filename))
        raise Exception("Invalid filepath: {0}".format(filename))
    if not ffmpeg_check():
        print("ffmpeg: Executable not found on machine.")
        raise Exception("Dependency not found: ffmpeg")
    command = ["ffmpeg", "-y", "-i", filename, "-ac", str(channels), "-ar", str(rate), "-loglevel", "error", temp.name]
    subprocess.check_output(command, stdin=open(os.devnull))
    return temp.name, rate


def find_speech_regions(filename, frame_width=4096, min_region_size=0.5, max_region_size=6):
    reader = wave.open(filename)
    sample_width = reader.getsampwidth()
    rate = reader.getframerate()
    n_channels = reader.getnchannels()

    total_duration = reader.getnframes() / rate
    chunk_duration = float(frame_width) / rate

    n_chunks = int(total_duration / chunk_duration)
    energies = []

    for i in range(n_chunks):
        chunk = reader.readframes(frame_width)
        energies.append(audioop.rms(chunk, sample_width * n_channels))

    threshold = percentile(energies, 0.2)

    elapsed_time = 0

    regions = []
    region_start = None

    for energy in energies:
        is_silence = energy <= threshold
        max_exceeded = region_start and elapsed_time - region_start >= max_region_size

        if (max_exceeded or is_silence) and region_start:
            if elapsed_time - region_start >= min_region_size:
                regions.append((region_start, elapsed_time))
                region_start = None

        elif (not region_start) and (not is_silence):
            region_start = elapsed_time
        elapsed_time += chunk_duration
    return regions


def CountEntries(srt_file):
    e=0
    with open(srt_file, 'r', encoding='utf-8') as srt:
        while True:
            e += 1
            # read lines in order
            number_in_sequence = srt.readline()
            timecode = srt.readline()
            # whether it's the end of the file.
            if not number_in_sequence:
                break
            # put all subtitles seperated by newline into a list.
            subtitles = []
            while True:
                subtitle = srt.readline()
                # whether it's the end of a entry.
                if subtitle == '\n':
                    break
                subtitles.append(subtitle)
    total_entries = e - 1
    #print('Total Entries', total_entries)
    return total_entries


def entries_generator(srt_file):
    """Generate a entries queue.

    input:
        srt_file: The original filename. [*.srt]

    output:
        entries: A queue generator.
    """
    with open(srt_file, 'r', encoding='utf-8') as srt:
        while True:
            # read lines in order
            number_in_sequence = srt.readline()
            timecode = srt.readline()
            # whether it's the end of the file.
            if not number_in_sequence:
                break
            # put all subtitles seperated by newline into a list.
            subtitles = []
            while True:
                subtitle = srt.readline()
                # whether it's the end of a entry.
                if subtitle == '\n':
                    break
                subtitles.append(subtitle)
            yield number_in_sequence, timecode, subtitles


def translate(entries, src, dest, patience, verbose):
    """Generate the translated entries.

    args:
        entries: The entries queue.
        src: The source language.
        dest: The target language.
    """
    translator = Translator()
    count_failure = 0
    count_entries = 0

    for number_in_sequence, timecode, subtitles in entries:
        count_entries += 1
        translated_subtitles = []

        for i, subtitle in enumerate(subtitles, 1):
            # handle the special case: empty string.
            if not subtitle:
                translated_subtitles.append(subtitle)
                continue
            translated_subtitle = translator.translate(subtitle, src=src, dest=dest).text
            # handle the fail to translate case.
            fail_to_translate = translated_subtitle[-1] == '\n'
            while fail_to_translate and patience:
                if verbose:
                    print('[Failure] Retry to translate...')
                    print('The translated subtitle: {}', end=''.format(translated_subtitle))

                translated_subtitle = translator.translate(translated_subtitle, src=src, dest=dest).text
                if translated_subtitle[-1] == '\n':
                    if patience == -1:
                        continue
                    if patience == 1:
                        if verbose:
                            print('This subtitle failed to translate... [Position] entry {0} line {1}'.format(count_entries,i))
                    patience -= 1
                else:
                    fail_to_translate = False
                    if verbose:
                        print('Translate successfully. The result: {}'.format(translated_subtitle))

            translated_subtitles.append(translated_subtitle if fail_to_translate else translated_subtitle + '\n')

        if verbose:
            print('Current number in sequence: {}'.format(count_entries))
            print('The translation result:', end=' ')
            #print(f"{''.join(translated_subtitles)}")
            print("{}".join(translated_subtitles), end='')
        else:
            if fail_to_translate:
                count_failure += 1
                print('[{}] Failure to translate current entry...'.format(count_entries))
            #else:
                #print('[{}] Current entry has been translated...'.format(count_entries))
            #print('Total failures: {0}/{1}'.format(count_failure,count_entries))

        yield number_in_sequence, timecode, translated_subtitles, count_failure, count_entries


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('source_path', help="Path to the video or audio file to subtitle", nargs='?')
    parser.add_argument('-C', '--concurrency', help="Number of concurrent API requests to make", type=int, default=10)
    parser.add_argument('-o', '--output', help="Output path for subtitles (by default, subtitles are saved in the same directory and name as the source path)")
    parser.add_argument('-F', '--format', help="Destination subtitle format", default="srt")
    parser.add_argument('-S', '--src-language', help="Language spoken in source file", default="en")
    parser.add_argument('-D', '--dst-language', help="Desired language for the subtitles", default="en")
    parser.add_argument('-n', '--rename', type=str, help='rename the output file.')
    parser.add_argument('-p', '--patience', type=int, help='the patience of retrying to translate. Expect a positive number.  If -1 is assigned, the program will try for infinite times until there is no failures happened in the output.')
    parser.add_argument('-V', '--verbose', action="store_true", help='logs the translation process to console.')
    parser.add_argument('-v', '--version', action='version', version='0.0.2')
    parser.add_argument('--list-formats', help="List all available subtitle formats", action='store_true')
    parser.add_argument('--list-languages', help="List all available source/destination languages", action='store_true')

    args = parser.parse_args()

    if args.list_formats:
        print("List of formats:")
        for subtitle_format in FORMATTERS.keys():
            print("{format}".format(format=subtitle_format))
        return 0

    if args.list_languages:
        print("List of all languages:")
        for code, language in sorted(LANGUAGE_CODES.items()):
            print("{code}\t{language}".format(code=code, language=language))
        return 0

    if args.format not in FORMATTERS.keys():
        print("Subtitle format not supported. Run with --list-formats to see all supported formats.")
        return 1

    if args.src_language not in LANGUAGE_CODES.keys():
        print("Source language not supported. Run with --list-languages to see all supported languages.")
        return 1

    if args.dst_language not in LANGUAGE_CODES.keys():
        print("Destination language not supported. Run with --list-languages to see all supported languages.")
        return 1

    if not args.source_path:
        parser.print_help(sys.stderr)
        return 1

    audio_filename, audio_rate = extract_audio(args.source_path)

    regions = find_speech_regions(audio_filename)

    pool = multiprocessing.Pool(args.concurrency)
    converter = FLACConverter(source_path=audio_filename)
    recognizer = SpeechRecognizer(language=args.src_language, rate=audio_rate, api_key=GOOGLE_SPEECH_API_KEY)

    transcripts = []
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

            for i, transcript in enumerate(pool.imap(recognizer, extracted_regions)):
                transcripts.append(transcript)
                pbar.update(i)
            pbar.finish()

        except KeyboardInterrupt:
            pbar.finish()
            pool.terminate()
            pool.join()
            print("Cancelling transcription")
            return 1

    timed_subtitles = [(r, t) for r, t in zip(regions, transcripts) if t]
    formatter = FORMATTERS.get(args.format)
    formatted_subtitles = formatter(timed_subtitles)

    dest = args.output

    if not dest:
        base, ext = os.path.splitext(args.source_path)
        dest = "{base}.{format}".format(base=base, format=args.format)

    with open(dest, 'wb') as f:
        f.write(formatted_subtitles.encode("utf-8"))

    with open(dest, 'a') as f:
        f.write("\n")

    #print("Subtitles file created at {}".format(dest))

    os.remove(audio_filename)


    if not is_same_language(args.src_language, args.dst_language):

        srt_file = dest
        entries = entries_generator(srt_file)
        translated_file = args.rename if args.rename else srt_file[ :-4] + '_translated.srt'

        if args.verbose:
            print("Translating from %5s to %5s         : " %(args.src_language, args.dst_language))
            total_entries = CountEntries(srt_file)
            print('Total Entries', total_entries)
            with open(translated_file, 'w', encoding='utf-8') as f:
                for number_in_sequence, timecode, subtitles, count_failure, count_entries in translate(entries, src=args.src_language, dest=args.dst_language, patience=args.patience, verbose=args.verbose):
                    f.write(number_in_sequence)
                    f.write(timecode)
                    for subtitle in subtitles:
                        f.write(subtitle)
                        f.write('\n')

        if not args.verbose:
            total_entries = CountEntries(srt_file)
            e=0
            prompt = "Translating from %5s to %5s         : " %(args.src_language, args.dst_language)
            widgets = [prompt, Percentage(), ' ', Bar(), ' ', ETA()]
            pbar = ProgressBar(widgets=widgets, maxval=total_entries).start()

            with open(translated_file, 'w', encoding='utf-8') as f:
                for number_in_sequence, timecode, subtitles, count_failure, count_entries in translate(entries, src=args.src_language, dest=args.dst_language, patience=args.patience, verbose=args.verbose):
                    f.write(number_in_sequence)
                    f.write(timecode)
                    for subtitle in subtitles:
                        f.write(subtitle)
                        f.write('\n')
                        e += 1
                        pbar.update(e)
                pbar.finish()

        print('Done.')
        print("Original subtitles file created at      : {}".format(dest))
        print('Translated subtitles file created at    : {}' .format(translated_file))
        print('Total failure to translate entries      : {0}/{1}'.format(count_failure, count_entries))
        failure_ratio = count_failure / count_entries
        if failure_ratio > 0:
            print('If you expect a lower failure ratio or completed translate, please check out the usage of [-p | --postion] argument.')

    return 0

if __name__ == '__main__':
    multiprocessing.freeze_support()
    sys.exit(main())
