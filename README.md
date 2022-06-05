# autosrt <a href="https://pypi.org/project/autosrt/0.0.1/"><img src="https://img.shields.io/pypi/v/autosrt.svg"></img></a>

### auto generate subtitle for any video or audio file and translate it for free using googletrans-4.0.0-rc1

this script is a modified and combined version of original autosub made by Anastasis Germanidis at https://github.com/agermanidis/autosub
and translate-srt-subtitles.py made by jaredyam at https://gist.github.com/jaredyam/4fe7527ccf6981595a879c9705e56c51

### Installation

if you don't have python on your Windows system you can get compiled version from
https://github.com/botbahlul/autosrt/releases/download/autosrt/autosrt.zip

just extract those ffmpeg.exe and autosrt.exe into a folder that has been added to PATH ENVIRONTMET
for example in C:\Windows\system32

you can get latest version of ffmpeg from https://www.ffmpeg.org/

in Linux you have to install this script with python>=3.8 and install ffmpeg with pip or with your linux package manager
for example in debian based linux distribution you can type

```
apt update
apt install -y ffmpeg
```

to install this autosrt, just type

```
pip install autosrt
```

you can compile this script into a single executable file with pyinstaller by downloading
```__init__.py``` file, rename it to ```autosrt.py``` and type :

```
pip install pyinstaller
pyinstaller --onefile autosrt.py
```

the executable compiled file will be placed by pyinstaller into dist
subfolder of your current working folder, so you can just rename and
put  that compiled file into  a folder that  has been added to  your
PATH ENVIRONTMENT so you can execute it from anywhere

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
autosrt -S zh-CN -D en filename.mp4
```  

you can also install this script (or any pip package) in android via python package in termux app

https://github.com/termux/termux-app/releases/tag/v0.118.0

choose the right apk for your device, install it, then open it

type these commands to get python, pip, this autosrt, and any other pip packages :

```
termux-setup-storage
pkg update -y
pkg install -y python
pkg install -y ffmpeg
pip install autosrt
```

### Usage

```
autosrt [-h] [-C CONCURRENCY] [-o OUTPUT] [-F FORMAT]
             [-S SRC_LANGUAGE] [-D DST_LANGUAGE]
             [-n RENAME] [-p PATIENCE] [-v]
             [--list-formats] [--list-languages]
             [source_path]

positional arguments:
  source_path           Path to the video or audio file

options:

  -h, --help            show this help message and exit
  
  -C CONCURRENCY, --concurrency CONCURRENCY
                        Number of concurrent API requests to make
                        
  -o OUTPUT, --output OUTPUT
                        Output  path  for subtitles  (by default, 
                        subtitles are saved in the same directory 
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
                        the patience of retrying to translate.
                        Expect  a positive  number.  If -1 is 
                        assigned,  the program will  try  for 
                        infinite  times  until  there  is  no 
                        failures happened in the output.
                        
  -v, --verbose         logs the translation process to console.
  
  --list-formats        List all available subtitle formats
  
  --list-languages      List all available languages
```

### WARNING!

PLEASE USE IT WISELY!

DON'T ABUSE GOOGLE TRANSLATE SERVERS WITH HUGE REQUESTS AND MAKES ALL OF US ENDED UP IN 503 SERVICE UNAVAILABLE ERROR!

### License

MIT
