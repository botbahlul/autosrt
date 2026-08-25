import requests
import json
import sys
import asyncio
from functools import partial
from progressbar import ProgressBar, Percentage, Bar, ETA
import multiprocessing


class SentenceTranslator(object):

    def __init__(
        self,
        src,
        dst,
        endpoint_config,
        patience=-1,
        timeout=30,
        error_messages_callback=None
    ):

        self.src = src
        self.dst = dst
        self.endpoint_config = endpoint_config
        self.patience = patience
        self.timeout = timeout
        self.error_messages_callback = error_messages_callback


    async def __call__(self, sentence):

        try:

            if not sentence:
                return None

            translated_sentence = await self._translate(sentence)

            if translated_sentence is None:
                return None

            translated_sentence = str(translated_sentence)

            if not translated_sentence:
                return None

            fail_to_translate = translated_sentence.endswith('\n')

            patience = self.patience

            while fail_to_translate and patience:

                translated_sentence = await self._translate(
                    translated_sentence
                )

                if translated_sentence is None:
                    return None

                translated_sentence = str(translated_sentence)

                if translated_sentence.endswith('\n'):

                    if patience == -1:
                        continue

                    patience -= 1

                else:

                    fail_to_translate = False

            return translated_sentence

        except KeyboardInterrupt:

            if self.error_messages_callback:
                self.error_messages_callback(
                    "Cancelling all tasks"
                )
            else:
                print("Cancelling all tasks")

            return None

        except Exception as e:

            if self.error_messages_callback:
                self.error_messages_callback(e)
            else:
                print(e)

            return None


    async def _translate(self, sentence):

        return await self.GoogleTranslate(
            sentence,
            src=self.src,
            dst=self.dst,
            timeout=self.timeout
        )


    async def translate(self, sentence):

        return await self(sentence)


    def translate_async(self, sentence):

        loop = asyncio.new_event_loop()

        try:

            asyncio.set_event_loop(loop)

            return loop.run_until_complete(
                self(sentence)
            )

        finally:

            loop.close()


    async def GoogleTranslate(
        self,
        text,
        src,
        dst,
        timeout=30
    ):

        endpoint_type = self.endpoint_config.get("type")

        try:

            # ========================================================
            # ENDPOINT 1
            # ========================================================

            if endpoint_type == 1:

                url = self.endpoint_config["url"]

                params = {
                    "client": "gtx",
                    "sl": src,
                    "tl": dst,
                    "dt": "t",
                    "q": text
                }

                headers = self.endpoint_config["headers"]

                response = requests.get(
                    url,
                    params=params,
                    headers=headers,
                    timeout=timeout
                )

                if response.status_code != 200:

                    print(
                        "Google Translate HTTP error: %s"
                        % response.status_code
                    )

                    return None

                try:

                    data = response.json()

                except ValueError:

                    print(
                        "Google Translate returned invalid JSON:"
                    )

                    print(response.text[:500])

                    return None

                if not isinstance(data, list):
                    return None

                if len(data) == 0:
                    return None

                response_json = data[0]

                if not isinstance(response_json, list):
                    return None

                translation = ""

                for item in response_json:

                    if (
                        isinstance(item, list)
                        and len(item) > 0
                        and isinstance(item[0], str)
                    ):

                        translation += item[0]

                if translation:
                    return translation

                return None


            # ========================================================
            # ENDPOINT 2
            # ========================================================

            elif endpoint_type == 2:

                url = self.endpoint_config["url"]

                params = {
                    "client": "dict-chrome-ex",
                    "sl": src,
                    "tl": dst,
                    "q": text
                }

                headers = self.endpoint_config["headers"]

                response = requests.get(
                    url,
                    params=params,
                    headers=headers,
                    timeout=timeout
                )

                if response.status_code != 200:

                    print(
                        "Google Translate HTTP error: %s"
                        % response.status_code
                    )

                    return None

                try:

                    data = response.json()

                except ValueError:

                    print(
                        "Google Translate returned invalid JSON:"
                    )

                    print(response.text[:500])

                    return None

                if not isinstance(data, list):
                    return None

                if len(data) == 0:
                    return None

                first = data[0]

                # ----------------------------------------------------
                # Response:
                #
                # ["Halo"]
                # ----------------------------------------------------

                if isinstance(first, str):

                    if first:
                        return first

                    return None

                # ----------------------------------------------------
                # Nested response
                # ----------------------------------------------------

                if isinstance(first, list):

                    translation = ""

                    for item in first:

                        if isinstance(item, str):

                            translation += item

                        elif (
                            isinstance(item, list)
                            and len(item) > 0
                            and isinstance(item[0], str)
                        ):

                            translation += item[0]

                    if translation:
                        return translation

                return None


            else:

                print(
                    "Invalid Google Translate endpoint configuration."
                )

                return None


        except requests.exceptions.ConnectionError as e:

            # ========================================================
            # CONNECTION ERROR
            #
            # Tidak pindah endpoint di sini.
            #
            # Endpoint sudah ditentukan melalui
            # test_translation_endpoint().
            # ========================================================

            if self.error_messages_callback:

                self.error_messages_callback(e)

            else:

                print(
                    "Google Translate connection error: %s"
                    % e
                )

            return None


        except KeyboardInterrupt:

            if self.error_messages_callback:

                self.error_messages_callback(
                    "Cancelling all tasks"
                )

            else:

                print("Cancelling all tasks")

            return None


        except Exception as e:

            if self.error_messages_callback:

                self.error_messages_callback(e)

            else:

                print(e)

            return None


# ================================================================
# ERROR CALLBACK
# ================================================================

def show_error_messages(messages):

    print(messages)


# ================================================================
# TEST GOOGLE TRANSLATE ENDPOINT
# ================================================================

def test_translation_endpoint(
    src,
    dst,
    error_messages_callback=None
):

    """
    Menguji endpoint Google Translate.

    Urutan:

        1. translate.googleapis.com
        2. clients5.google.com

    Return:

        endpoint configuration yang berhasil

    atau:

        None

    """

    test_sentence = "Hello"


    # ============================================================
    # ENDPOINT 1
    # ============================================================

    endpoint1 = {

        "type": 1,

        "url": (
            "https://translate.googleapis.com/"
            "translate_a/single"
        ),

        "params": {

            "client": "gtx",
            "sl": src,
            "tl": dst,
            "dt": "t",
            "q": test_sentence

        },

        "headers": {

            "User-Agent": (
                "Mozilla/5.0 "
                "(Windows NT 10.0; Win64; x64)"
            ),

            "Referer": (
                "https://translate.google.com"
            )

        }

    }


    try:

        print("")
        print("CHECKING GOOGLE TRANSLATE ENDPOINT")
        print("===================================")
        print("Testing endpoint 1...")
        print(endpoint1["url"])


        response = requests.get(

            endpoint1["url"],

            params=endpoint1["params"],

            headers=endpoint1["headers"],

            timeout=10

        )


        if response.status_code == 200:

            try:

                data = response.json()

            except ValueError:

                data = None


            translation = None


            if (
                isinstance(data, list)
                and len(data) > 0
            ):

                response_json = data[0]


                if isinstance(response_json, list):

                    result = ""


                    for item in response_json:

                        if (
                            isinstance(item, list)
                            and len(item) > 0
                            and isinstance(item[0], str)
                        ):

                            result += item[0]


                    if result:

                        translation = result


            if translation:

                print(
                    "Endpoint 1 : OK"
                )

                print(
                    "Translation : %s"
                    % translation
                )

                print(
                    "Using endpoint 1"
                )

                print("")

                return endpoint1


        print(
            "Endpoint 1 : FAILED "
            "(HTTP %s)"
            % response.status_code
        )


    except Exception as e:

        print(
            "Endpoint 1 : FAILED"
        )

        print(
            "Error: %s"
            % e
        )


    # ============================================================
    # ENDPOINT 2
    # ============================================================

    endpoint2 = {

        "type": 2,

        "url": (
            "https://clients5.google.com/"
            "translate_a/t"
        ),

        "params": {

            "client": "dict-chrome-ex",
            "sl": src,
            "tl": dst,
            "q": test_sentence

        },

        "headers": {

            "User-Agent": (
                "Mozilla/5.0 "
                "(Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/139.0.0.0 "
                "Safari/537.36"
            ),

            "Accept": (
                "application/json,"
                "text/plain,*/*"
            )

        }

    }


    try:

        print(
            "Testing endpoint 2..."
        )

        print(
            endpoint2["url"]
        )


        response = requests.get(

            endpoint2["url"],

            params=endpoint2["params"],

            headers=endpoint2["headers"],

            timeout=10

        )


        if response.status_code == 200:

            try:

                data = response.json()

            except ValueError:

                data = None


            translation = None


            if (
                isinstance(data, list)
                and len(data) > 0
            ):

                first = data[0]


                # ------------------------------------------------
                # Response:
                #
                # ["Hello"]
                # ------------------------------------------------

                if isinstance(first, str):

                    translation = first


                # ------------------------------------------------
                # Nested response
                # ------------------------------------------------

                elif isinstance(first, list):

                    result = ""


                    for item in first:

                        if isinstance(item, str):

                            result += item

                        elif (
                            isinstance(item, list)
                            and len(item) > 0
                            and isinstance(item[0], str)
                        ):

                            result += item[0]


                    if result:

                        translation = result


            if translation:

                print(
                    "Endpoint 2 : OK"
                )

                print(
                    "Translation : %s"
                    % translation
                )

                print(
                    "Using endpoint 2"
                )

                print("")

                return endpoint2


        print(
            "Endpoint 2 : FAILED "
            "(HTTP %s)"
            % response.status_code
        )


    except Exception as e:

        print(
            "Endpoint 2 : FAILED"
        )

        print(
            "Error: %s"
            % e
        )


    # ============================================================
    # BOTH FAILED
    # ============================================================

    print("")
    print(
        "ERROR: Both Google Translate endpoints "
        "are unavailable."
    )
    print("")

    return None


# ================================================================
# MAIN
# ================================================================

async def main():

    # ============================================================
    # TIMED SUBTITLES
    #
    # Gunakan timed_subtitles Anda yang sekarang di sini.
    # ============================================================

    timed_subtitles = [
        # --------------------------------------------------------
        # TEMPEL timed_subtitles ANDA YANG SEKARANG DI SINI
        # --------------------------------------------------------
    ]


    # ============================================================
    # LANGUAGE
    # ============================================================

    src = "zh-CN"
    dst = "id"


    # ============================================================
    # CREATE SUBTITLE DATA
    # ============================================================

    created_regions = []
    created_subtitles = []


    for entry in timed_subtitles:

        created_regions.append(
            entry[0]
        )

        created_subtitles.append(
            entry[1]
        )


    # ============================================================
    # TEST ENDPOINT
    #
    # HANYA DILAKUKAN SATU KALI.
    # ============================================================

    endpoint_config = test_translation_endpoint(

        src=src,

        dst=dst,

        error_messages_callback=show_error_messages

    )


    # ============================================================
    # JIKA KEDUA ENDPOINT GAGAL
    # ============================================================

    if endpoint_config is None:

        print(
            "Translation cancelled."
        )

        return


    # ============================================================
    # SHOW SELECTED ENDPOINT
    # ============================================================

    print(
        "Selected Google Translate endpoint: %d"
        % endpoint_config["type"]
    )

    print(
        endpoint_config["url"]
    )

    print("")


    # ============================================================
    # MULTIPROCESSING POOL
    # ============================================================

    pool = multiprocessing.Pool(10)


    # ============================================================
    # PROGRESS BAR
    # ============================================================

    prompt = (
        "Translating from %8s to %8s         : "
        % (src, dst)
    )

    widgets = [
        prompt,
        Percentage(),
        ' ',
        Bar(),
        ' ',
        ETA()
    ]


    pbar = ProgressBar(

        widgets=widgets,

        maxval=len(timed_subtitles)

    ).start()


    # ============================================================
    # SENTENCE TRANSLATOR
    #
    # endpoint_config hasil test digunakan di sini.
    # ============================================================

    transcript_translator = SentenceTranslator(

        src=src,

        dst=dst,

        endpoint_config=endpoint_config,

        patience=3,

        timeout=30,

        error_messages_callback=show_error_messages

    )


    transcript_translator_partial = partial(

        transcript_translator.translate_async

    )


    # ============================================================
    # TRANSLATE
    # ============================================================

    translated_subtitles = []


    for i, translated_subtitle in enumerate(

        pool.imap(
            transcript_translator_partial,
            created_subtitles
        )

    ):

        translated_subtitles.append(
            translated_subtitle
        )

        pbar.update(i + 1)


    # ============================================================
    # FINISH
    # ============================================================

    pbar.finish()


    print(
        translated_subtitles
    )


    # ============================================================
    # CLOSE POOL
    # ============================================================

    pool.close()
    pool.join()


# ================================================================
# PROGRAM ENTRY
# ================================================================

if __name__ == '__main__':

    multiprocessing.freeze_support()

    sys.exit(
        asyncio.run(main())
    )
