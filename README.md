# autosrt <a href="https://pypi.python.org/pypi/autosrt"><img src="https://img.shields.io/pypi/v/autosrt.svg"></img></a>
  
### Auto-generated subtitles for any video
autosrt is a simple command line tool made with python to auto generate subtitle/closed caption for any video or audio file and translate it automaticly for free using googletrans-4.0.0rc1 https://pypi.org/project/googletrans/4.0.0rc1/

This script is a modified version of original autosub made by Anastasis Germanidis at https://github.com/agermanidis/autosub

### Installation
If you don't have python on your Windows system you can get compiled version from this git release assets
https://github.com/botbahlul/autosrt/releases

Just extract those ffmpeg.exe and autosrt.exe into a folder that has been added to PATH ENVIRONTMET for example in C:\Windows\system32

You can get latest version of ffmpeg from https://www.ffmpeg.org/

In Linux you have to install this script with python (version minimal 3.8 ) and install ffmpeg with your linux package manager for example in debian based linux distribution you can type :

```
apt update
apt install -y ffmpeg
```

To install this autosrt, just type :
```
pip install autosrt
```

You can compile this script into a single executable file with pyinstaller by downloading __init__.py file, rename it to autosrt.py and type :
```
pip install pyinstaller
pyinstaller --onefile autosrt.py
```

The executable compiled file will be placed by pyinstaller into dist subfolder of your current working folder, so you can just rename and put that compiled file into a folder that has been added to your PATH ENVIRONTMENT so you can execute it from anywhere

I was succesfuly compiled it in Windows 10 with pyinstaller-5.1 and Pyhton-3.10.4, and python-3.8.12 in Debian 9

Another alternative way to install this script with python is by cloning this git (or downloading this git as zip then extract it into a folder), and then just type :

```
python setup.py build
python setup.py install
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

If you don't need translations just type :
```
autosrt -S zh-CN "Episode 1.mp4"
```

### Usage

```
autosrt [-h] [-C CONCURRENCY] [-o OUTPUT] [-F FORMAT] [-S SRC_LANGUAGE] [-D DST_LANGUAGE] [-v] [-lf] [-ll] [source_path]

positional arguments:
  source_path           Path to the video or audio file to subtitle

options:
  -h, --help            show this help message and exit
  -C CONCURRENCY, --concurrency CONCURRENCY
                        Number of concurrent API requests to make
  -o OUTPUT, --output OUTPUT
                        Output path for subtitles (by default, subtitles are saved in the same directory and name as the source path)
  -F FORMAT, --format FORMAT
                        Destination subtitle format
  -S SRC_LANGUAGE, --src-language SRC_LANGUAGE
                        Language spoken in source file
  -D DST_LANGUAGE, --dst-language DST_LANGUAGE
                        Desired language for the subtitles
  -v, --version         show program's version number and exit
  -lf, --list-formats   List all available subtitle formats
  -ll, --list-languages
                        List all available source/destination languages
```

### License

MIT

Check my other SPEECH RECOGNITIION + TRANSLATE PROJECTS in https://botbahlul.github.io
