@echo off
setlocal

set "folderToDelete1=.\build"
set "folderToDelete2=.\dist"
set "fileToDelete1=.\*.spec"

if exist "%folderToDelete1%" (
    rmdir /s /q "%folderToDelete1%"
    if errorlevel 1 (
        echo Error occurred while deleting the folder.
    )
)

if exist "%folderToDelete2%" (
    rmdir /s /q "%folderToDelete2%"
    if errorlevel 1 (
        echo Error occurred while deleting the folder.
    )
)

if exist "%fileToDelete1%" (
    del /s /q "%fileToDelete1%"
    if errorlevel 1 (
        echo Error occurred while deleting the file.
    )
)

pyinstaller ^
--onefile autosrt.py
