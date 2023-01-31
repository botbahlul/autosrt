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

from progressbar import ProgressBar, Percentage, Bar, ETA
from pygoogletranslation import Translator
import pysrt
import six

GOOGLE_SPEECH_API_KEY = "AIzaSyBOti4mM-6x9WDnZIjIeyEU21OpBXqWBgw"
GOOGLE_SPEECH_API_URL = "http://www.google.com/speech-api/v2/recognize?client=chromium&lang={lang}&key={key}" # pylint: disable=line-too-long
DEFAULT_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'

arraylist_language_code = []
arraylist_language_code.append("af");
arraylist_language_code.append("sq");
arraylist_language_code.append("am");
arraylist_language_code.append("ar");
arraylist_language_code.append("hy");
arraylist_language_code.append("as");
arraylist_language_code.append("ay");
arraylist_language_code.append("az");
arraylist_language_code.append("bm");
arraylist_language_code.append("eu");
arraylist_language_code.append("be");
arraylist_language_code.append("bn");
arraylist_language_code.append("bho");
arraylist_language_code.append("bs");
arraylist_language_code.append("bg");
arraylist_language_code.append("ca");
arraylist_language_code.append("ceb");
arraylist_language_code.append("ny");
arraylist_language_code.append("zh-CN");
arraylist_language_code.append("zh-TW");
arraylist_language_code.append("co");
arraylist_language_code.append("cr");
arraylist_language_code.append("cs");
arraylist_language_code.append("da");
arraylist_language_code.append("dv");
arraylist_language_code.append("nl");
arraylist_language_code.append("doi");
arraylist_language_code.append("en");
arraylist_language_code.append("eo");
arraylist_language_code.append("et");
arraylist_language_code.append("ee");
arraylist_language_code.append("fil");
arraylist_language_code.append("fi");
arraylist_language_code.append("fr");
arraylist_language_code.append("fy");
arraylist_language_code.append("gl");
arraylist_language_code.append("ka");
arraylist_language_code.append("de");
arraylist_language_code.append("el");
arraylist_language_code.append("gn");
arraylist_language_code.append("gu");
arraylist_language_code.append("ht");
arraylist_language_code.append("ha");
arraylist_language_code.append("haw");
arraylist_language_code.append("he");
arraylist_language_code.append("hi");
arraylist_language_code.append("hmn");
arraylist_language_code.append("hu");
arraylist_language_code.append("is");
arraylist_language_code.append("ig");
arraylist_language_code.append("ilo");
arraylist_language_code.append("id");
arraylist_language_code.append("ga");
arraylist_language_code.append("it");
arraylist_language_code.append("ja");
arraylist_language_code.append("jv");
arraylist_language_code.append("kn");
arraylist_language_code.append("kk");
arraylist_language_code.append("km");
arraylist_language_code.append("rw");
arraylist_language_code.append("kok");
arraylist_language_code.append("ko");
arraylist_language_code.append("kri");
arraylist_language_code.append("kmr");
arraylist_language_code.append("ckb");
arraylist_language_code.append("ky");
arraylist_language_code.append("lo");
arraylist_language_code.append("la");
arraylist_language_code.append("lv");
arraylist_language_code.append("ln");
arraylist_language_code.append("lt");
arraylist_language_code.append("lg");
arraylist_language_code.append("lb");
arraylist_language_code.append("mk");
arraylist_language_code.append("mg");
arraylist_language_code.append("ms");
arraylist_language_code.append("ml");
arraylist_language_code.append("mt");
arraylist_language_code.append("mi");
arraylist_language_code.append("mr");
arraylist_language_code.append("mni");
arraylist_language_code.append("lus");
arraylist_language_code.append("mn");
arraylist_language_code.append("mmr");
arraylist_language_code.append("ne");
arraylist_language_code.append("no");
arraylist_language_code.append("or");
arraylist_language_code.append("om");
arraylist_language_code.append("ps");
arraylist_language_code.append("fa");
arraylist_language_code.append("pl");
arraylist_language_code.append("pt");
arraylist_language_code.append("pa");
arraylist_language_code.append("qu");
arraylist_language_code.append("ro");
arraylist_language_code.append("ru");
arraylist_language_code.append("sm");
arraylist_language_code.append("sa");
arraylist_language_code.append("gd");
arraylist_language_code.append("nso");
arraylist_language_code.append("sr");
arraylist_language_code.append("st");
arraylist_language_code.append("sn");
arraylist_language_code.append("sd");
arraylist_language_code.append("si");
arraylist_language_code.append("sk");
arraylist_language_code.append("sl");
arraylist_language_code.append("so");
arraylist_language_code.append("es");
arraylist_language_code.append("su");
arraylist_language_code.append("sw");
arraylist_language_code.append("sv");
arraylist_language_code.append("tg");
arraylist_language_code.append("ta");
arraylist_language_code.append("tt");
arraylist_language_code.append("te");
arraylist_language_code.append("th");
arraylist_language_code.append("ti");
arraylist_language_code.append("ts");
arraylist_language_code.append("tr");
arraylist_language_code.append("tk");
arraylist_language_code.append("tw");
arraylist_language_code.append("ug");
arraylist_language_code.append("uk");
arraylist_language_code.append("ur");
arraylist_language_code.append("uz");
arraylist_language_code.append("vi");
arraylist_language_code.append("cy");
arraylist_language_code.append("xh");
arraylist_language_code.append("yi");
arraylist_language_code.append("yo");
arraylist_language_code.append("zu");

arraylist_language = []
arraylist_language.append("Afrikaans");
arraylist_language.append("Albanian");
arraylist_language.append("Amharic");
arraylist_language.append("Arabic");
arraylist_language.append("Armenian");
arraylist_language.append("Assamese");
arraylist_language.append("Aymara");
arraylist_language.append("Azerbaijani");
arraylist_language.append("Bambara");
arraylist_language.append("Basque");
arraylist_language.append("Belarusian");
arraylist_language.append("Bengali (Bangla)");
arraylist_language.append("Bhojpuri");
arraylist_language.append("Bosnian");
arraylist_language.append("Bulgarian");
arraylist_language.append("Catalan");
arraylist_language.append("Cebuano");
arraylist_language.append("Chichewa, Nyanja");
arraylist_language.append("Chinese (Simplified)");
arraylist_language.append("Chinese (Traditional)");
arraylist_language.append("Corsican");
arraylist_language.append("Croatian");
arraylist_language.append("Czech");
arraylist_language.append("Danish");
arraylist_language.append("Divehi, Maldivian");
arraylist_language.append("Dogri");
arraylist_language.append("Dutch");
arraylist_language.append("English");
arraylist_language.append("Esperanto");
arraylist_language.append("Estonian");
arraylist_language.append("Ewe");
arraylist_language.append("Filipino");
arraylist_language.append("Finnish");
arraylist_language.append("French");
arraylist_language.append("Frisian");
arraylist_language.append("Galician");
arraylist_language.append("Georgian");
arraylist_language.append("German");
arraylist_language.append("Greek");
arraylist_language.append("Guarani");
arraylist_language.append("Gujarati");
arraylist_language.append("Haitian Creole");
arraylist_language.append("Hausa");
arraylist_language.append("Hawaiian");
arraylist_language.append("Hebrew");
arraylist_language.append("Hindi");
arraylist_language.append("Hmong");
arraylist_language.append("Hungarian");
arraylist_language.append("Icelandic");
arraylist_language.append("Igbo");
arraylist_language.append("Ilocano");
arraylist_language.append("Indonesian");
arraylist_language.append("Irish");
arraylist_language.append("Italian");
arraylist_language.append("Japanese");
arraylist_language.append("Javanese");
arraylist_language.append("Kannada");
arraylist_language.append("Kazakh");
arraylist_language.append("Khmer");
arraylist_language.append("Kinyarwanda (Rwanda)");
arraylist_language.append("Konkani");
arraylist_language.append("Korean");
arraylist_language.append("Krio");
arraylist_language.append("Kurdish (Kurmanji)");
arraylist_language.append("Kurdish (Sorani)");
arraylist_language.append("Kyrgyz");
arraylist_language.append("Lao");
arraylist_language.append("Latin");
arraylist_language.append("Latvian (Lettish)");
arraylist_language.append("Lingala");
arraylist_language.append("Lithuanian");
arraylist_language.append("Luganda, Ganda");
arraylist_language.append("Luxembourgish");
arraylist_language.append("Macedonian");
arraylist_language.append("Malagasy");
arraylist_language.append("Malay");
arraylist_language.append("Malayalam");
arraylist_language.append("Maltese");
arraylist_language.append("Maori");
arraylist_language.append("Marathi");
arraylist_language.append("Meiteilon (Manipuri)");
arraylist_language.append("Mizo");
arraylist_language.append("Mongolian");
arraylist_language.append("Myanmar (Burmese)");
arraylist_language.append("Nepali");
arraylist_language.append("Norwegian");
arraylist_language.append("Oriya");
arraylist_language.append("Oromo (Afaan Oromo)");
arraylist_language.append("Pashto, Pushto");
arraylist_language.append("Persian (Farsi)");
arraylist_language.append("Polish");
arraylist_language.append("Portuguese");
arraylist_language.append("Punjabi (Eastern)");
arraylist_language.append("Quechua");
arraylist_language.append("Romanian, Moldavian");
arraylist_language.append("Russian");
arraylist_language.append("Samoan");
arraylist_language.append("Sanskrit");
arraylist_language.append("Scots Gaelic");
arraylist_language.append("Sepedi");
arraylist_language.append("Serbian");
arraylist_language.append("Sesotho");
arraylist_language.append("Shona");
arraylist_language.append("Sindhi");
arraylist_language.append("Sinhalese");
arraylist_language.append("Slovak");
arraylist_language.append("Slovenian");
arraylist_language.append("Somali");
arraylist_language.append("Spanish");
arraylist_language.append("Sundanese");
arraylist_language.append("Swahili (Kiswahili)");
arraylist_language.append("Swedish");
arraylist_language.append("Tajik");
arraylist_language.append("Tamil");
arraylist_language.append("Tatar");
arraylist_language.append("Telugu");
arraylist_language.append("Thai");
arraylist_language.append("Tigrinya");
arraylist_language.append("Tsonga");
arraylist_language.append("Turkish");
arraylist_language.append("Turkmen");
arraylist_language.append("Twi");
arraylist_language.append("Ukrainian");
arraylist_language.append("Urdu");
arraylist_language.append("Uyghur");
arraylist_language.append("Uzbek");
arraylist_language.append("Vietnamese");
arraylist_language.append("Welsh");
arraylist_language.append("Xhosa");
arraylist_language.append("Yiddish");
arraylist_language.append("Yoruba");
arraylist_language.append("Zulu");

map_code_of_language = dict(zip(arraylist_language, arraylist_language_code))
map_language_of_code = dict(zip(arraylist_language_code, arraylist_language))

LANGUAGE_CODES = map_language_of_code

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


class SubtitleTranslator(object):
    def __init__(self, src, dest):
        self.src = src
        self.dest = dest

    def __call__(self, entries):
        translator = Translator()
        translated_subtitles = []
        number_in_sequence, timecode, subtitles = entries

        for i, subtitle in enumerate(subtitles, 1):
            # handle the special case: empty string.
            if not subtitle:
                translated_subtitles.append(subtitle)
            translated_subtitle = translator.translate(subtitle, src=self.src, dest=self.dest).text
            translated_subtitle = translator.translate(translated_subtitle, src=self.src, dest=self.dest).text
            translated_subtitles.append(translated_subtitle + '\n')

        return number_in_sequence, timecode, translated_subtitles


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


#def find_speech_regions(filename, frame_width=4096, min_region_size=0.5, max_region_size=6):
def find_speech_regions(filename, frame_width=4096, min_region_size=0.3, max_region_size=8):
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
    #parser.add_argument('-D', '--dst-language', help="Desired language for the subtitles", default="en")
    parser.add_argument('-D', '--dst-language', help="Desired language for the subtitles")
    parser.add_argument('-n', '--rename', type=str, help='rename the output file.')
    parser.add_argument('-p', '--patience', type=int, help='the patience of retrying to translate. Expect a positive number.  If -1 is assigned, the program will try for infinite times until there is no failures happened in the output.')
    parser.add_argument('-V', '--verbose', action="store_true", help='logs the translation process to console.')
    parser.add_argument('-v', '--version', action='version', version='0.0.9')
    parser.add_argument('-lf', '--list-formats', help="List all available subtitle formats", action='store_true')
    parser.add_argument('-ll', '--list-languages', help="List all available source/destination languages", action='store_true')

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

    if args.dst_language:
        if not args.dst_language in LANGUAGE_CODES.keys():
            print("Destination language not supported. Run with --list-languages to see all supported languages.")
            return 1
        if not is_same_language(args.src_language, args.dst_language):
            do_translate = True
        else:
            do_translate = False

    if not args.dst_language:
        do_translate = False

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

    srt_file = args.output

    if not srt_file:
        base, ext = os.path.splitext(args.source_path)
        srt_file = "{base}.{format}".format(base=base, format=args.format)

    with open(srt_file, 'wb') as f:
        f.write(formatted_subtitles.encode("utf-8"))

    with open(srt_file, 'a') as f:
        f.write("\n")

    #print("Subtitles file created at {}".format(srt_file))

    os.remove(audio_filename)

    if do_translate:
        entries = entries_generator(srt_file)
        translated_srt_file = args.rename if args.rename else srt_file[ :-4] + '_translated.srt'
        total_entries = CountEntries(srt_file)

        if args.verbose:
            print("Translating from %5s to %5s         : " %(args.src_language, args.dst_language))
            print('Total Entries', total_entries)

            with open(translated_srt_file, 'w', encoding='utf-8') as f:
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

            '''
            with open(translated_srt_file, 'w', encoding='utf-8') as f:
                for number_in_sequence, timecode, subtitles, count_failure, count_entries in translate(entries, src=args.src_language, dest=args.dst_language, patience=args.patience, verbose=args.verbose):
                    f.write(number_in_sequence)
                    f.write(timecode)
                    for subtitle in subtitles:
                        f.write(subtitle)
                        f.write('\n')
                        e += 1
                        pbar.update(e)
                pbar.finish()
            '''

            subtitle_translator = SubtitleTranslator(src=args.src_language, dest=args.dst_language)
            translated_entries = []
            for i, translated_entry in enumerate(pool.imap(subtitle_translator, entries)):
                translated_entries.append(translated_entry)
                pbar.update(i)
            pbar.finish()

            with open(translated_srt_file, 'w', encoding='utf-8') as f:
                for number_in_sequence, timecode, translated_subtitles in translated_entries:
                    f.write(number_in_sequence)
                    f.write(timecode)
                    for translated_subtitle in translated_subtitles:
                        f.write(translated_subtitle)
                        f.write('\n')

    print('Done.')
    if do_translate:
        print("Original subtitles file created at      : {}".format(srt_file))
        print('Translated subtitles file created at    : {}' .format(translated_srt_file))
        if args.verbose:
            print('Total failure to translate entries      : {0}/{1}'.format(count_failure, count_entries))
            failure_ratio = count_failure / count_entries
            if failure_ratio > 0:
                print('If you expect a lower failure ratio or completed translate, please check out the usage of [-p | --postion] argument.')
    else:
        print("Subtitles file created at      : {}".format(srt_file))

    pool.close()
    pool.join()

    return 0

if __name__ == '__main__':
    multiprocessing.freeze_support()
    sys.exit(main())
