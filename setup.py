#!/usr/bin/env python3.8
from __future__ import unicode_literals
import sys
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module='setuptools')
warnings.filterwarnings("ignore", category=UserWarning, module='setuptools')
warnings.filterwarnings("ignore", message=".*is deprecated*")

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup
from autosrt import VERSION

long_description = (
    'autosrt is a utility for automatic speech recognition and subtitle generation.'
    'It takes a video or an audio file as input, performs voice activity detection '
    'to find speech regions,  makes parallel requests to Google Web Speech API  to '
    'generate transcriptions for those regions,  (optionally) translates them to a '
    'different language, and finally saves the resulting subtitles file to disk.   '
    'It supports a variety of input and output languages and can currently produce '
    'subtitles in SRT, VTT, JSON, and RAW format.'
)

install_requires=[
    "requests>=2.3.0",
    "httpx>=0.24.0",
    "urllib3 >=1.26.0,<3.0",
    "pysrt>=1.0.1",
    "six>=1.11.0",
    "progressbar2>=3.34.3",
]

setup(
    name="autosrt",
    version=VERSION,
    description="a utility for automatic speech recognition and subtitle generation",
    long_description = long_description,
    author="Bot Bahlul",
    author_email="bot.bahlul@gmail.com",
    url="https://github.com/botbahlul/autosrt",
    packages=["autosrt"],
    entry_points={
        "console_scripts": [
            "autosrt = autosrt:main",
        ],
    },
    install_requires=install_requires,
    license=open("LICENSE").read()
)
