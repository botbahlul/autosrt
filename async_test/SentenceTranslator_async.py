import requests
import json
import sys
import asyncio
from functools import partial
try:
    from json.decoder import JSONDecodeError
except ImportError:
    JSONDecodeError = ValueError
from progressbar import ProgressBar, Percentage, Bar, ETA
import multiprocessing


class SentenceTranslator:
    def __init__(self, src, dst, patience=-1, timeout=30, error_messages_callback=None):
        self.src = src
        self.dst = dst
        self.patience = patience
        self.timeout = timeout
        self.error_messages_callback = error_messages_callback

    async def __call__(self, sentence):
        try:
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

    async def _translate(self, sentence):
        return await self.GoogleTranslate(sentence, src=self.src, dst=self.dst)

    async def translate(self, sentence):
        return await self(sentence)

    def translate_async(self, sentence):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(self(sentence))


def show_error_messages(messages):
    print(messages)


async def main():
    timed_subtitles = [((0.08533333333333333, 0.8533333333333335), '考前的鸟'), ((1.0240000000000002, 1.7066666666666663), '你没看错'), ((2.0479999999999996, 2.901333333333332), '他嘴里叼着的'), ((2.9866666666666655, 4.351999999999999), '是一张百元的人民币'), ((4.437333333333333, 5.97333333333334), '他每天出门觅食回来'), ((6.485333333333342, 7.253333333333345), '从来都不会空'), ((7.338666666666679, 7.936000000000015), '会空手而归'), ((8.277333333333347, 9.984000000000004), '一个大抽屉都会被装满了'), ((10.069333333333336, 11.861333333333326), '让主人既惊喜又担忧'), ((11.946666666666658, 13.994666666666646), '由本机大板牙跟大家聊聊'), ((14.250666666666644, 15.530666666666637), '这支针头发的小鸟'), ((16.469333333333307, 17.49333333333332), '这句会稿前的鸟'), ((17.919999999999995, 18.432000000000002), '脚皮力'), ((18.60266666666667, 19.797333333333356), '是一个黑色的八个'), ((20.138666666666694, 21.504000000000048), '是主人在乡下捡来的'), ((21.845333333333386, 23.637333333333412), '当时体力不支倒是什么原因'), ((23.893333333333416, 24.832000000000097), '翅膀受了伤'), ((25.25866666666677, 26.02666666666678), '奄奄一息'), ((26.36800000000012, 27.64800000000014), '是主人把它带回家'), ((27.904000000000142, 29.440000000000165), '经过一个多月悉心的照料'), ((29.781333333333503, 30.976000000000187), '体力的伤势得以恢复'), ((31.061333333333522, 31.57333333333353), '回复'), ((31.7440000000002, 33.280000000000165), '主人想要将它放归自然'), ((33.53600000000016, 34.81600000000012), '谁料比例始终都不肯'), ((34.901333333333454, 35.41333333333344), '不肯离去'), ((35.5840000000001, 37.97333333333337), '没想到霹雳已经和主人难舍难分了'), ((38.57066666666669, 40.618666666666634), '于是主人就把它当成宠物养了'), ((41.30133333333328, 43.0079999999999), '主人没有把他圈养在笼子里'), ((43.263999999999896, 44.799999999999855), '反让他自由自在的飞翔'), ((45.05599999999985, 46.8479999999998), '每天霹雳都是飞出去觅食'), ((47.10399999999979, 49.06666666666641), '可能是为报答主人的救命之恩'), ((49.57866666666639, 50.94399999999969), '有一天霹雳回来时'), ((51.02933333333302, 52.223999999999656), '竟然标着10元钱'), ((52.39466666666632, 53.845333333332945), '当时主人也没在意'), ((54.10133333333294, 55.12533333333291), '以为是家里人掉的'), ((55.29599999999957, 55.80799999999956), '可是'), ((55.97866666666622, 57.002666666666194), '从此以后批'), ((57.087999999999525, 58.19733333333283), '头皮里每天都会叼着笑'), ((58.28266666666616, 58.794666666666146), '抢回来'), ((58.96533333333281, 59.73333333333279), '小到1元'), ((60.07466666666611, 60.84266666666609), '大道百元'), ((61.01333333333275, 62.037333333332725), '有时体里会反复'), ((62.122666666666056, 62.97599999999937), '目标前数次'), ((63.23199999999936, 64.51199999999936), '这时可把主人吓到'), ((64.68266666666604, 66.30399999999946), '不知道这钱是怎么来'), ((66.47466666666614, 68.60799999999959), '赶忙询问家里人是否少了钱'), ((68.8639999999996, 69.37599999999964), '请问号'), ((69.71733333333299, 70.91199999999972), '家里人都说自己没有用'), ((70.99733333333306, 71.50933333333309), '有钱'), ((71.93599999999978, 72.70399999999982), '主人又跑到服'), ((72.78933333333316, 73.81333333333322), '找附近的商家询问'), ((73.9839999999999, 74.58133333333326), '也都说没'), ((74.6666666666666, 76.11733333333335), '没有见过小鸟来标签'), ((76.20266666666669, 77.65333333333344), '主人想了好几天都'), ((77.73866666666677, 78.42133333333348), '都搞不明白'), ((78.6773333333335, 80.38400000000026), '所以pve每次调回来的钱'), ((80.98133333333362, 82.00533333333368), '主人也不敢乱动'), ((82.43200000000037, 83.79733333333378), '一直都保存在一个抽屉'), ((84.13866666666713, 85.8453333333339), '想着哪天要是有人找上门'), ((86.10133333333391, 87.46666666666732), '就把这些钱物归原主'), ((88.06400000000069, 89.25866666666742), '可时间一天天过去'), ((89.60000000000078, 90.96533333333419), '如今整整一个抽屉'), ((91.05066666666752, 91.81866666666757), '都被装满了'), ((91.9040000000009, 93.18400000000098), '差不多有70000元了'), ((93.52533333333433, 95.06133333333442), '以前去到八个会学说话'), ((95.57333333333445, 96.5973333333345), '可从没听说过吧'), ((96.68266666666784, 97.45066666666789), '八个还会搞成'), ((97.53600000000122, 98.04800000000125), '前的'), ((98.13333333333459, 99.07200000000131), 'TV这搞钱的本事'), ((99.15733333333465, 101.20533333333476), '很是让主人都不得不叫他大哥'), ((101.54666666666812, 103.0826666666682), '我家大哥刘德华回来了'), ((103.25333333333488, 109.31200000000189), '我要祷告'), ((111.18933333333533, 112.55466666666874), '昨晚主人和朋友喝酒'), ((113.06666666666877, 114.09066666666882), '没等体力回来'), ((114.17600000000216, 115.11466666666888), '有关超睡觉'), ((115.3706666666689, 116.0533333333356), '没想到这一刻'), ((116.13866666666894, 116.65066666666897), '你开窗'), ((116.82133333333564, 118.18666666666905), '满满的都是惊喜呀'), ((118.69866666666908, 119.97866666666916), '自从霹雳搞笑回来'), ((120.32000000000251, 121.51466666666924), '在家的地位都提高了'), ((121.8560000000026, 123.81866666666937), '连家里的大猫都不放在眼里'), ((123.98933333333605, 125.18400000000278), '都可以站在猫身上了'), ((125.78133333333615, 126.89066666666955), '主人的家人和朋友'), ((126.97600000000288, 127.57333333333625), '有猜测的说'), ((127.82933333333627, 128.5973333333362), '这只八个针筒'), ((128.68266666666952, 129.2800000000028), '虎豹骑'), ((129.3653333333361, 130.389333333336), '骑的是你当时就的他'), ((130.47466666666932, 132.43733333333577), '有的标签给你这是在报恩啊'), ((132.94933333333572, 133.9733333333356), '至于钱的来历'), ((134.05866666666893, 134.9973333333355), '谁也说不出来'), ((135.25333333333546, 135.7653333333354), '主人把皮'), ((135.85066666666873, 136.61866666666864), '马蹄里的视频发'), ((136.70400000000197, 137.47200000000188), '发布到网上'), ((137.81333333333518, 138.83733333333507), '想找到钱的施主')]

    src = "zh-CN"
    dst = "id"
    created_regions = []
    created_subtitles = []
    for entry in timed_subtitles:
        created_regions.append(entry[0])
        created_subtitles.append(entry[1])

    pool = multiprocessing.Pool(10)

    prompt = "Translating from %8s to %8s         : " %(src, dst)
    widgets = [prompt, Percentage(), ' ', Bar(), ' ', ETA()]
    pbar = ProgressBar(widgets=widgets, maxval=len(timed_subtitles)).start()

    transcript_translator = SentenceTranslator(src=src, dst=dst, patience=3, error_messages_callback=show_error_messages)
    transcript_translator_partial = partial(transcript_translator.translate_async)

    translated_subtitles = []
    for i, translated_subtitle in enumerate(pool.imap(transcript_translator_partial, created_subtitles)):
        translated_subtitles.append(translated_subtitle)
        pbar.update(i)
    pbar.finish()
    print(translated_subtitles)

    pool.close()
    pool.join()

if __name__ == '__main__':
    multiprocessing.freeze_support()
    sys.exit(asyncio.run(main()))

