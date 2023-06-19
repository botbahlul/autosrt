#!/bin/sh

folder1="./build"
folder2="./dist"
file1="./*.spec"

if [ -d "$folder1" ]; then
	rm -rf "$folder1"
fi

if [ -d "$folder2" ]; then
	rm -rf "$folder2"
fi

if [ -f "$file1" ]; then
	rm -f "$file1"
fi

pyinstaller --python=/usr/local/bin/python3.8 \
--hidden-import argparse \
--onefile autosrt.py
