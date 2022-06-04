# autosrt <a href="https://pypi.python.org/pypi/autosrt"><img src="https://img.shields.io/pypi/v/autosrt.svg"></img></a>
  
### Auto-generated subtitles for any video and translate it for free using googletrans

autosrt is a utility for automatic speech recognition and subtitle generation. It takes a video or an audio file as input, performs voice activity detection to find speech regions, makes parallel requests to Google Web Speech API to generate transcriptions for those regions, (optionally) translates them to a different language, and finally saves the resulting subtitles to disk. It supports a variety of input and output languages (to see which, run the utility with the argument `--list-languages`) and can currently produce subtitles in either the [SRT format](https://en.wikipedia.org/wiki/SubRip) or simple [JSON](https://en.wikipedia.org/wiki/JSON).

### Installation

1. Install [ffmpeg](https://www.ffmpeg.org/).

### Usage

```
$ autosrt -h
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
                        the patience of retrying to translate. Expect a positive number. If -1 is assigned, the program will try for
                        infinite times until there is no failures happened in the output.
  -v, --verbose         logs the translation process to console.
  --list-formats        List all available subtitle formats
  --list-languages      List all available source/destination languages
```

### License

MIT
