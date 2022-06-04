# autosrt
auto generate srt subtitles for any video or audio file and translate it for free using googletrans-4.0.0-rc1

this script is a combined and modified version from original autosub made by Anastasis Germanidis https://github.com/agermanidis/autosub and srt_translate made by jaredyam https://gist.github.com/jaredyam/4fe7527ccf6981595a879c9705e56c51

usage: autosrt [-h] [-C CONCURRENCY] [-o OUTPUT] [-F FORMAT] [-S SRC_LANGUAGE] [-D DST_LANGUAGE] [-n RENAME] [-p PATIENCE] [-v]
               [--list-formats] [--list-languages]
               [source_path]

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
  

this script can be compiled into a single executable file with pyinstaller with command : pyinstaller --onefile autosrt.py

I was succesfuly compiled it in Windows 10 with Pyhton-3.10.4 and python-3.8.12 in Debian 9

it still needs ffmpeg (ffmpeg.exe in Windows) so you have to install it first and make sure it can be reached from any folder by adding its location folder into PATH ENVIRONTMENT


Simple usage example :
  
  in linux :

  $ python3.8 autosrt.py -S zh-CN -D en filename.mp4
  
  
  in Windows :
  
  C:\autosrt>python autosrt.py -S zh-CN -D en filename.mp4
