# autosrt <a href="https://pypi.python.org/pypi/autosrt"><img src="https://img.shields.io/pypi/v/autosrt.svg"></img></a>
  
### Auto generate subtitle files for any video / audio files
autosrt is a simple command line tool made with python to auto generate subtitle/closed caption for any video or audio files and translate it automatically for free using a simple unofficial online Google Translate API.

This script is a modified version of original autosub made by Anastasis Germanidis at https://github.com/agermanidis/autosub

### UPDATE NOTES
Since version 1.2.2 I tried to make some class modules, so in case you want to use them in your own project you can just import them. They are Language, WavConverter, SpeechRegionFinder, FLACConverter, SpeechRecognizer, SentenceTranslator, SubtitleFormatter, and SubtitleWriter. You can import them like this :
```
from autosrt import Language, WavConverter, SpeechRegionFinder, FLACConverter, SpeechRecognizer, SentenceTranslator, \
    SubtitleFormatter,  SubtitleWriter
```

You can learn how to use them by playing around with those scripts inside test folder. Check every def function on each class to know how to use them. They are not to difficult to understand.

If you are on Linux OS don't forget to install libmagic C library to make python_magic modules work properly by typing this at console terminal :
```
sudo apt install -y libmagic1
```

### Installation
If you don't have python on your Windows system you can get compiled version from this git release assets
https://github.com/botbahlul/autosrt/releases

Just extract those ffmpeg.exe and autosrt.exe into a folder that has been added to PATH ENVIRONTMET for example in C:\Windows\system32

You can get latest version of ffmpeg from https://www.ffmpeg.org/

In Linux you have to install this script with python (version minimal 3.8 ) and install ffmpeg with your linux package manager for example in debian based linux distribution you can type :

```
sudo apt update
sudo apt install -y ffmpeg
```

To install this autosrt, just type :
```
pip install autosrt
```

You can try to compile that autosrt.py script in win/linux folder into a single executable file with pyinstaller by typing these :
```
pip install pyinstaller
pyinstaller --onefile autosrt.py
```

The executable compiled file will be placed by pyinstaller into dist subfolder of your current working folder, so you can just rename and put that compiled file into a folder that has been added to your PATH ENVIRONTMENT so you can execute it from anywhere

I was succesfuly compiled it in Windows 10 with pyinstaller-5.1 and Pyhton-3.10.4, and python-3.8.12 in Debian 9

Another alternative way to install this script with python is by cloning this git (or downloading this git as zip then extract it into a folder), and then just type :

```
pip install wheel
python setup.py build
python setup.py bdist_wheel
```

Then check the name of the whl file created in dist folder. In case the filename is autosrt-1.2.2-py2.py3-none-any.whl then you can install that whl file with pip :
```
cd dist
pip install autosrt-1.2.2-py2.py3-none-any.whl
```

You can also install this script (or any pip package) in ANDROID DEVICES via PYTHON package in TERMUX APP

https://github.com/termux/termux-app/releases/tag/v0.118.0

Choose the right apk for your device, install it, then open it

Type these commands to get python, pip, this autosrt, (and any other pip packages) :

```
termux-setup-storage
pkg update -y
pkg install -y python
pkg install -y ffmpeg
pip install autosrt
```

### Simple usage example 

```
autosrt --list-languages
autosrt -S zh-CN -D en "Episode 1.mp4"
```

For multiple video/audio files (starts from version 1.1.0), you can use wildcard
```
autosrt -S zh-CN -D en "C:\Movies\*.mp4"
```

If you don't need translations just type :
```
autosrt -S zh-CN "Episode 1.mp4"
```

### Usage

```
usage: autosrt [-h] [-S SRC_LANGUAGE] [-D DST_LANGUAGE] [-ll] [-o OUTPUT] [-F FORMAT] [-lf] [-C CONCURRENCY] [-v] [source_path ...]

positional arguments:
  source_path           File path of the video or audio files to generate subtitles files (use wildcard for multiple files or
                        separate them with a space character)

options:
  -h, --help            show this help message and exit
  -S SRC_LANGUAGE, --src-language SRC_LANGUAGE
                        Language code of the audio language spoken in video/audio source_path
  -D DST_LANGUAGE, --dst-language DST_LANGUAGE
                        Desired translation language code for the subtitles
  -ll, --list-languages
                        List all supported languages
  -o OUTPUT, --output OUTPUT
                        Output file path for subtitles (by default, subtitles are saved in the same directory and named with the
                        source_path base name)
  -F FORMAT, --format FORMAT
                        Desired subtitle format
  -lf, --list-formats   List all supported subtitle formats
  -C CONCURRENCY, --concurrency CONCURRENCY
                        Number of concurrent API requests to make
  -v, --version         show program's version number and exit
```

### License

MIT

Check my other SPEECH RECOGNITIION + TRANSLATE PROJECTS in https://botbahlul.github.io
