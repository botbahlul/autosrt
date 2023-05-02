import sys
import requests
import asyncio
from functools import partial
import multiprocessing

class SentenceTranslator:
    def __init__(self, src, dst, patience=-1, timeout=30):
        self.src = src
        self.dst = dst
        self.patience = patience
        self.timeout = timeout

    async def __call__(self, sentence):
        translated_sentence = []
        if not sentence:
            return None

        translated_sentence = await self._translate(sentence)

        fail_to_translate = translated_sentence[-1] == '\n'
        while fail_to_translate and self.patience:
            translated_sentence = await self._translate(translated_sentence)
            if translated_sentence[-1] == '\n':
                if self.patience == -1:
                    continue
                self.patience -= 1
            else:
                fail_to_translate = False
        return translated_sentence

    async def GoogleTranslate(self, text, src, dst, timeout=30):
        url = 'https://translate.googleapis.com/translate_a/'
        params = 'single?client=gtx&sl='+src+'&tl='+dst+'&dt=t&q='+text;
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)', 'Referer': 'https://translate.google.com',}

        try:
            response = requests.get(url+params, headers=headers, timeout=self.timeout)
            if response.status_code == 200:
                response_json = response.json()[0]
                length = len(response_json)
                translation = ""
                for i in range(length):
                    translation = translation + response_json[i][0]
                return translation
            return

        except requests.exceptions.ConnectionError:
            with httpx.Client() as client:
                response = client.get(url+params, headers=headers, timeout=timeout)
                if response.status_code == 200:
                    response_json = response.json()[0]
                    length = len(response_json)
                    translation = ""
                    for i in range(length):
                        translation = translation + response_json[i][0]
                    return translation
                return

        except KeyboardInterrupt:
            print("Cancelling transcription")
            return

        except Exception as e:
            print(e)
            return

    async def _translate(self, sentence):
        return await self.GoogleTranslate(sentence, src=self.src, dst=self.dst)

    async def translate(self, sentence):
        return await self(sentence)

    def translate_async(self, sentence):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(self(sentence))


async def main():
    translator = SentenceTranslator(src='en', dst='fr', patience=3)
    translated_sentence = await translator.translate('Hello, how are you?')
    print(translated_sentence)

if __name__ == '__main__':
    multiprocessing.freeze_support()
    sys.exit(asyncio.run(main()))

