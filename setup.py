#!/usr/bin/env python
from __future__ import unicode_literals

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

long_description = (
    'autosrt is a utility for automatic speech recognition and subtitle generation. '
    'It takes a video or an audio file as input, performs voice activity detection '
    'to find speech regions,  makes parallel requests to Google Web Speech API  to '
    'generate transcriptions for those regions,  (optionally) translates them to a '
    'different language, and finally saves the resulting subtitles to disk. '
    'It supports a variety of input and output languages  and can currently produce '
    'subtitles in SRT, VTT, JSON, and RAW format.'
)

setup(
    name="autosrt",
    version="1.0.7",
    description="autosrt is a utility for automatic speech recognition and subtitle generation. It takes a video or an audio file as input, performs voice activity detection to find speech regions,  makes parallel requests to Google Web Speech API  to generate transcriptions for those regions,  (optionally) translates them to a different language, and finally saves the resulting subtitles to disk. It supports a variety of input and output languages  and can currently produce subtitles in SRT, VTT, JSON, and RAW format.",
    long_description = long_description,
    author="Bot Bahlul",
    author_email="bot.bahlul@gmail.com",
    url="https://github.com/botbahlul/autosrt",
    packages=[str("autosrt")],
    entry_points={
        "console_scripts": [
            "autosrt = autosrt:main",
        ],
    },
    install_requires=[
        "requests>=2.3.0",
        "pysrt>=1.0.1",
        "progressbar2>=3.34.3",
        "six>=1.11.0",
        "asyncio",
        "httpx>=0.13.3",
    ],
    license=open("LICENSE").read()
)
