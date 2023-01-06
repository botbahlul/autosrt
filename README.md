# autosrt <a href="https://pypi.org/project/autosrt/0.0.3/"><img src="https://img.shields.io/pypi/v/autosrt.svg"></img></a>

### auto generate subtitle for any video or audio file and translate it for free using pygoogletranslation 
autosrt is a utility for automatic speech recognition and subtitle generation. It takes a video or an audio file as input, 
performs voice activity detection to find speech regions, makes parallel requests to Google Web Speech API to generate 
transcriptions for those regions, (optionally) translates them to a different language, and finally saves the resulting 
subtitles to disk. It supports a variety of input and output languages (to see which, run the utility with --list-languages 
as argument respectively) and can currently produce subtitles in SRT format.

this script is a modified and combined version of original autosub made by Anastasis Germanidis at https://github.com/agermanidis/autosub
and translate-srt-subtitles.py made by jaredyam at https://gist.github.com/jaredyam/4fe7527ccf6981595a879c9705e56c51

### Installation
if you don't have python on your system you can get compiled version from this release asset https://github.com/botbahlul/autosrt/releases/download/autosrt-0.0.3/autosrt-0.0.3.zip

in Windows just extract those ffmpeg.exe and autosrt.exe (in this rar windows folder) into a folder that has been added to PATH ENVIRONTMET
for example in C:\Windows\system32

you can get original ffmpeg from https://www.ffmpeg.org/

make sure ffmpeg.exe can be reached from any folder by adding its location folder into PATH ENVIRONTMENT

in Linux you're still need ffmpeg, so install it first then extract autosrt file (from this rar linux folder) into 
/usr/bin/ or /usr/local/bin/ or /usr/sbin/ or /usr/local/sbin/


if python has already installed on your system you can install this script with pip

```
pip install ffmpeg
pip install autosrt
```

you can compile this script into a single executable file with pyinstaller by downloading
```__init__.py``` file, rename it to ```autosrt.py``` and type :

```
pip install pyinstaller
pyinstaller --onefile autosrt.py
```

the executable compiled file will be placed by pyinstaller into dist subfolder of your current working folder, then you can 
just rename and put that compiled file into a folder that has been added to your PATH ENVIRONTMENT so you can execute it from anywhere

I was succesfuly compiled it in Windows 10 with pyinstaller-5.1 and Pyhton-3.10.4, and python-3.8.12 in Debian 9

other alternative way you can install this script with python by cloning this git (or downloading this git as zip then extract it into 
a folder), and then just type :

```
python setup.py build
python setup.py install
```

Simple usage example :
  
```
autosrt --list-languages
autosrt -S zh-CN -D en "file name.mp4"
```  

You can also install this script (or any pip package) in android via python package in termux app

https://github.com/termux/termux-app/releases/tag/v0.118.0

choose the right apk for your device, install it, then open it

type these commands to get python, pip, this autosrt, (and any other pip packages) :

```
termux-setup-storage
pkg update -y
pkg install -y python
pkg install -y ffmpeg
pip install autosrt
```

After that download your video via any online video downloader

Usualy that video will be placed into /sdcard/Download folder

Now open termux then type:

```
cd /sdcard/Download
autosrt -S <source language code> -D <translation language code> <filename.mp4>
```

### Usage
```
autosrt [-h] [-C CONCURRENCY] [-o OUTPUT] [-F FORMAT] [-S SRC_LANGUAGE] [-D DST_LANGUAGE]
             [-n RENAME] [-p PATIENCE] [-v] [--list-formats] [--list-languages] [source_path]

positional arguments:
  source_path           Path to the video or audio file to subtitle

options:

  -h, --help            show this help message and exit
  
  -C CONCURRENCY, --concurrency CONCURRENCY
                        Number of concurrent API requests to make
                        
  -o OUTPUT, --output OUTPUT
                        Output path for subtitles (by default, subtitles are saved in the same directory 
                        and name as the source path)
                        
  -F FORMAT, --format FORMAT
                        Destination subtitle format
                        
  -S SRC_LANGUAGE, --src-language SRC_LANGUAGE
                        Language spoken in source file
                        
  -D DST_LANGUAGE, --dst-language DST_LANGUAGE
                        Desired language for the subtitles
                        
  -n RENAME, --rename RENAME
                        rename the output file.
                        
  -p PATIENCE, --patience PATIENCE
                        the patience of retrying to translate. Expect a positive number. 
                        If -1 is assigned, the program will try for infinite times until 
                        there is no failures happened in the output.
                        
  -v, --verbose         logs the translation process to console.
  
  -lf, --list-formats   List all available subtitle formats
  
  -ll, --list-languages List all available source/destination languages
```

### License
MIT

Check my other SPEECH RECOGNITIION + TRANSLATE PROJECTS in https://botbahlul.github.io
