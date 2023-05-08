#!/usr/bin/env python
from __future__ import unicode_literals
import sys

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
        "pysrt>=1.0.1",
        "progressbar2>=3.34.3",
        "six>=1.11.0",
]

if sys.platform == "win32":
    install_requires.append("python-magic>=0.4.27")
    install_requires.append("python_magic_bin>=0.4.14")
if sys.platform == "linux":
    install_requires.append("python-magic>=0.4.27")
if not sys.platform == "win32" and not sys.platform == "linux":
    install_requires.append("python-magic>=0.4.27")

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
