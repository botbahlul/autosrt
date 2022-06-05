# autosrt <a href="https://pypi.org/project/autosrt/0.0.1/"><img src="https://img.shields.io/pypi/v/autosrt.svg"></img></a>

### auto generate subtitle for any video or audio file and translate it for free using googletrans-4.0.0-rc1

this script is a modified and combined version of original autosub made by Anastasis Germanidis at https://github.com/agermanidis/autosub
and translate-srt-subtitles.py made by jaredyam at https://gist.github.com/jaredyam/4fe7527ccf6981595a879c9705e56c51

you can compile it into a single executable file with pyinstaller with command :

```
pyinstaller --onefile __init__.py
```
then you can just put it into a folder that has been added to your PATH ENVIRONTMENT

or you can just install it with python by cloning this git with git clone or download this git as zip and then extract it into a folder and then just type :

```
python setup.py build
python setup.py install
```
I was succesfuly compiled it in Windows 10 with Pyhton-3.10.4 and python-3.8.12 in Debian 9

it still needs ffmpeg (ffmpeg.exe in Windows) so you have to install it first and make sure it can be reached
from any folder by adding its location folder into PATH ENVIRONTMENT

you can get ffmpeg from https://www.ffmpeg.org/

Simple usage example :
  
in linux :
```
$ autosrt --list-languages
$ autosrt -S zh-CN -D en filename.mp4
```  
  
in Windows :
```
C:\autosrt>autosrt --list-languages
C:\autosrt>autosrt -S zh-CN -D en filename.mp4
```  

you can get compiled version from https://drive.google.com/file/d/1YVi7E2iY28SZc5k0R52OVDubCOCYTk8e/view?usp=sharing

in Windows just extract those ffmpeg.exe and autosrt.exe to a folder that has been added to PATH ENVIRONTMET
for example in C:\Windows\system32

in Linux just extract that autosrt file to /usr/bin/ or /usr/local/bin/ or /usr/sbin/ or /usr/local/sbin/


### WARNING!

PLEASE USE IT WISELY!

DON'T ABUSE GOOGLE TRANSLATE SERVERS WITH HUGE REQUESTS AND MAKES ALL OF US GET 503 Service Unavailable ERROR!


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
                        Output path for subtitles (by default, subtitles are saved in the same directory and name as the source path)
                        
  -F FORMAT, --format FORMAT
                        Destination subtitle format
                        
  -S SRC_LANGUAGE, --src-language SRC_LANGUAGE
                        Language spoken in source file
                        
  -D DST_LANGUAGE, --dst-language DST_LANGUAGE
                        Desired language for the subtitles
                        
  -n RENAME, --rename RENAME
                        rename the output file.
                        
  -p PATIENCE, --patience PATIENCE
                        the patience of retrying to translate. Expect a positive number. If -1 is assigned, the program will try for infinite times until there is no failures happened in the output.
                        
  -v, --verbose         logs the translation process to console.
  
  --list-formats        List all available subtitle formats
  
  --list-languages      List all available source/destination languages
```

### License

MIT
