@echo off
set /p Usr="User name? "
set /p pythonpath="Python version folder (example python37-32) "
set /p filename="File to convert ? no extension. "
 
set target=%CD%\%filename%.ui
set output=%CD%\%filename%.py

echo Converting %target% to %output%

C:\Users\%Usr%\AppData\Local\Programs\Python\%pythonpath%\Scripts\pyside2-uic.exe %target% -o %output%

PAUSE