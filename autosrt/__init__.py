#!/usr/bin/env python
# ORIGINAL AUTOSUB IMPORTS
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
import pysrt
import six
# ADDITIONAL IMPORT FOR GoogleTranslate()
import asyncio
import httpx
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

GOOGLE_SPEECH_API_KEY = "AIzaSyBOti4mM-6x9WDnZIjIeyEU21OpBXqWBgw"
GOOGLE_SPEECH_API_URL = "http://www.google.com/speech-api/v2/recognize?client=chromium&lang={lang}&key={key}" # pylint: disable=line-too-long

arraylist_language_code = []
arraylist_language_code.append("af")
arraylist_language_code.append("sq")
arraylist_language_code.append("am")
arraylist_language_code.append("ar")
arraylist_language_code.append("hy")
arraylist_language_code.append("as")
arraylist_language_code.append("ay")
arraylist_language_code.append("az")
arraylist_language_code.append("bm")
arraylist_language_code.append("eu")
arraylist_language_code.append("be")
arraylist_language_code.append("bn")
arraylist_language_code.append("bho")
arraylist_language_code.append("bs")
arraylist_language_code.append("bg")
arraylist_language_code.append("ca")
arraylist_language_code.append("ceb")
arraylist_language_code.append("ny")
arraylist_language_code.append("zh-CN")
arraylist_language_code.append("zh-TW")
arraylist_language_code.append("co")
arraylist_language_code.append("hr")
arraylist_language_code.append("cs")
arraylist_language_code.append("da")
arraylist_language_code.append("dv")
arraylist_language_code.append("doi")
arraylist_language_code.append("nl")
arraylist_language_code.append("en")
arraylist_language_code.append("eo")
arraylist_language_code.append("et")
arraylist_language_code.append("ee")
arraylist_language_code.append("fil")
arraylist_language_code.append("fi")
arraylist_language_code.append("fr")
arraylist_language_code.append("fy")
arraylist_language_code.append("gl")
arraylist_language_code.append("ka")
arraylist_language_code.append("de")
arraylist_language_code.append("el")
arraylist_language_code.append("gn")
arraylist_language_code.append("gu")
arraylist_language_code.append("ht")
arraylist_language_code.append("ha")
arraylist_language_code.append("haw")
arraylist_language_code.append("he")
arraylist_language_code.append("hi")
arraylist_language_code.append("hmn")
arraylist_language_code.append("hu")
arraylist_language_code.append("is")
arraylist_language_code.append("ig")
arraylist_language_code.append("ilo")
arraylist_language_code.append("id")
arraylist_language_code.append("ga")
arraylist_language_code.append("it")
arraylist_language_code.append("ja")
arraylist_language_code.append("jv")
arraylist_language_code.append("kn")
arraylist_language_code.append("kk")
arraylist_language_code.append("km")
arraylist_language_code.append("rw")
arraylist_language_code.append("gom")
arraylist_language_code.append("ko")
arraylist_language_code.append("kri")
arraylist_language_code.append("kmr")
arraylist_language_code.append("ckb")
arraylist_language_code.append("ky")
arraylist_language_code.append("lo")
arraylist_language_code.append("la")
arraylist_language_code.append("lv")
arraylist_language_code.append("ln")
arraylist_language_code.append("lt")
arraylist_language_code.append("lg")
arraylist_language_code.append("lb")
arraylist_language_code.append("mk")
arraylist_language_code.append("mg")
arraylist_language_code.append("ms")
arraylist_language_code.append("ml")
arraylist_language_code.append("mt")
arraylist_language_code.append("mi")
arraylist_language_code.append("mr")
arraylist_language_code.append("mni-Mtei")
arraylist_language_code.append("lus")
arraylist_language_code.append("mn")
arraylist_language_code.append("my")
arraylist_language_code.append("ne")
arraylist_language_code.append("no")
arraylist_language_code.append("or")
arraylist_language_code.append("om")
arraylist_language_code.append("ps")
arraylist_language_code.append("fa")
arraylist_language_code.append("pl")
arraylist_language_code.append("pt")
arraylist_language_code.append("pa")
arraylist_language_code.append("qu")
arraylist_language_code.append("ro")
arraylist_language_code.append("ru")
arraylist_language_code.append("sm")
arraylist_language_code.append("sa")
arraylist_language_code.append("gd")
arraylist_language_code.append("nso")
arraylist_language_code.append("sr")
arraylist_language_code.append("st")
arraylist_language_code.append("sn")
arraylist_language_code.append("sd")
arraylist_language_code.append("si")
arraylist_language_code.append("sk")
arraylist_language_code.append("sl")
arraylist_language_code.append("so")
arraylist_language_code.append("es")
arraylist_language_code.append("su")
arraylist_language_code.append("sw")
arraylist_language_code.append("sv")
arraylist_language_code.append("tg")
arraylist_language_code.append("ta")
arraylist_language_code.append("tt")
arraylist_language_code.append("te")
arraylist_language_code.append("th")
arraylist_language_code.append("ti")
arraylist_language_code.append("ts")
arraylist_language_code.append("tr")
arraylist_language_code.append("tk")
arraylist_language_code.append("tw")
arraylist_language_code.append("uk")
arraylist_language_code.append("ur")
arraylist_language_code.append("ug")
arraylist_language_code.append("uz")
arraylist_language_code.append("vi")
arraylist_language_code.append("cy")
arraylist_language_code.append("xh")
arraylist_language_code.append("yi")
arraylist_language_code.append("yo")
arraylist_language_code.append("zu")

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
arraylist_language.append("Bengali");
arraylist_language.append("Bhojpuri");
arraylist_language.append("Bosnian");
arraylist_language.append("Bulgarian");
arraylist_language.append("Catalan");
arraylist_language.append("Cebuano");
arraylist_language.append("Chichewa");
arraylist_language.append("Chinese (Simplified)");
arraylist_language.append("Chinese (Traditional)");
arraylist_language.append("Corsican");
arraylist_language.append("Croatian");
arraylist_language.append("Czech");
arraylist_language.append("Danish");
arraylist_language.append("Dhivehi");
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
arraylist_language.append("Kinyarwanda");
arraylist_language.append("Konkani");
arraylist_language.append("Korean");
arraylist_language.append("Krio");
arraylist_language.append("Kurdish (Kurmanji)");
arraylist_language.append("Kurdish (Sorani)");
arraylist_language.append("Kyrgyz");
arraylist_language.append("Lao");
arraylist_language.append("Latin");
arraylist_language.append("Latvian");
arraylist_language.append("Lingala");
arraylist_language.append("Lithuanian");
arraylist_language.append("Luganda");
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
arraylist_language.append("Odiya (Oriya)");
arraylist_language.append("Oromo");
arraylist_language.append("Pashto");
arraylist_language.append("Persian");
arraylist_language.append("Polish");
arraylist_language.append("Portuguese");
arraylist_language.append("Punjabi");
arraylist_language.append("Quechua");
arraylist_language.append("Romanian");
arraylist_language.append("Russian");
arraylist_language.append("Samoan");
arraylist_language.append("Sanskrit");
arraylist_language.append("Scots Gaelic");
arraylist_language.append("Sepedi");
arraylist_language.append("Serbian");
arraylist_language.append("Sesotho");
arraylist_language.append("Shona");
arraylist_language.append("Sindhi");
arraylist_language.append("Sinhala");
arraylist_language.append("Slovak");
arraylist_language.append("Slovenian");
arraylist_language.append("Somali");
arraylist_language.append("Spanish");
arraylist_language.append("Sundanese");
arraylist_language.append("Swahili");
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
arraylist_language.append("Twi (Akan)");
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


def vtt_formatter(subtitles, padding_before=0, padding_after=0):
    """
    Serialize a list of subtitles according to the VTT format, with optional time padding.
    """
    text = srt_formatter(subtitles, padding_before, padding_after)
    text = 'WEBVTT\n\n' + text.replace(',', '.')
    return text


def json_formatter(subtitles):
    """
    Serialize a list of subtitles as a JSON blob.
    """
    subtitle_dicts = [
        {
            'start': start,
            'end': end,
            'content': text,
        }
        for ((start, end), text)
        in subtitles
    ]
    return json.dumps(subtitle_dicts)


def raw_formatter(subtitles):
    """
    Serialize a list of subtitles as a newline-delimited string.
    """
    return ' '.join(text for (_rng, text) in subtitles)


FORMATTERS = {
    'srt': srt_formatter,
    'vtt': vtt_formatter,
    'json': json_formatter,
    'raw': raw_formatter,
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


async def GoogleTranslate(text, src, dst):
    url = 'https://translate.googleapis.com/translate_a/'
    params = 'single?client=gtx&sl='+src+'&tl='+dst+'&dt=t&q='+text;
    async with httpx.AsyncClient() as client:
        response = await client.get(url+params)
        #print('response = {}'.format(response))
        response_json = response.json()[0]
        #print('response_json = {}'.format(response_json))
        length = len(response_json)
        #print('length = {}'.format(length))
        translation = ""
        for i in range(length):
            #print("{} {}".format(i, response_json[i][0]))
            translation = translation + response_json[i][0]
        return translation


class SentenceTranslator(object):
    def __init__(self, src, dest, patience=-1):
        self.src = src
        self.dest = dest
        self.patience = patience

    def __call__(self, sentence):
        translated_sentence = []
        # handle the special case: empty string.
        if not sentence:
            return None
        translated_sentence = asyncio.get_event_loop().run_until_complete(GoogleTranslate(sentence, src=self.src, dst=self.dest)) # using self made GoogleTranslate()
        fail_to_translate = translated_sentence[-1] == '\n'
        while fail_to_translate and patience:
            translated_sentence = translator.translate(translated_sentence, src=self.src, dest=self.dest).text
            if translated_sentence[-1] == '\n':
                if patience == -1:
                    continue
                patience -= 1
            else:
                fail_to_translate = False
        return translated_sentence


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

#def extract_audio(filename, channels=1, rate=16000):
def extract_audio(filename, channels=1, rate=48000):
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
#def find_speech_regions(filename, frame_width=4096, min_region_size=0.3, max_region_size=8):
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('source_path', help="Path to the video or audio file to subtitle", nargs='?')
    parser.add_argument('-C', '--concurrency', help="Number of concurrent API requests to make", type=int, default=10)
    parser.add_argument('-o', '--output', help="Output path for subtitles (by default, subtitles are saved in the same directory and name as the source path)")
    parser.add_argument('-F', '--format', help="Destination subtitle format", default="srt")
    parser.add_argument('-S', '--src-language', help="Language spoken in source file", default="en")
    parser.add_argument('-D', '--dst-language', help="Desired language for the subtitles")
    parser.add_argument('-v', '--version', action='version', version='1.0.7')
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
            pool.close()
            pool.join()
            print("Cancelling transcription")
            return 1

    timed_subtitles = [(r, t) for r, t in zip(regions, transcripts) if t]
    formatter = FORMATTERS.get(args.format)
    formatted_subtitles = formatter(timed_subtitles)

    subtitle_file = args.output

    if not subtitle_file:
        base, ext = os.path.splitext(args.source_path)
        subtitle_file = "{base}.{format}".format(base=base, format=args.format)

    with open(subtitle_file, 'wb') as f:
        f.write(formatted_subtitles.encode("utf-8"))

    with open(subtitle_file, 'a') as f:
        f.write("\n")

    if do_translate:
        translated_subtitle_file = subtitle_file[ :-4] + '.translated.' + args.format

        # CONCURRENT TRANSLATION USING class SentenceTranslator(object)
        # NO NEED TO TRANSLATE ALL transcript IN transcripts BECAUSE SOME region IN regions MAY JUST HAVE EMPTY STRING transcript
        # JUST TRANSLATE ALREADY CREATED subtitles ENTRIES FROM timed_subtitles
        created_regions = []
        created_subtitles = []
        for entry in timed_subtitles:
            created_regions.append(entry[0])
            created_subtitles.append(entry[1])

        prompt = "Translating from %5s to %5s         : " %(args.src_language, args.dst_language)
        widgets = [prompt, Percentage(), ' ', Bar(), ' ', ETA()]
        pbar = ProgressBar(widgets=widgets, maxval=len(timed_subtitles)).start()
        transcript_translator = SentenceTranslator(src=args.src_language, dest=args.dst_language)
        translated_subtitles = []
        for i, translated_subtitle in enumerate(pool.imap(transcript_translator, created_subtitles)):
            translated_subtitles.append(translated_subtitle)
            pbar.update(i)
        pbar.finish()

        timed_translated_subtitles = [(r, t) for r, t in zip(created_regions, translated_subtitles) if t]
        formatter = FORMATTERS.get(args.format)
        formatted_translated_subtitles = formatter(timed_translated_subtitles)

        with open(translated_subtitle_file, 'wb') as tf:
            tf.write(formatted_translated_subtitles.encode("utf-8"))

        with open(translated_subtitle_file, 'a') as tf:
            tf.write("\n")

    os.remove(audio_filename)

    print('Done.')
    if do_translate:
        print("Original subtitles file created at      : {}".format(subtitle_file))
        print('Translated subtitles file created at    : {}' .format(translated_subtitle_file))
    else:
        print("Subtitles file created at      : {}".format(subtitle_file))

    pool.close()
    pool.join()

    return 0

if __name__ == '__main__':
    multiprocessing.freeze_support()
    sys.exit(main())
