@echo off
rem Links cc5_plugin\CC5Bridge into CC5 OpenPlugin (needs admin once). Close CC5 first.
set SRC=%~dp0cc5_plugin\CC5Bridge
set DST=C:\Program Files\Reallusion\Character Creator 5\Bin64\OpenPlugin\CC5Bridge
if exist "%DST%" (echo already installed & pause & exit /b 0)
powershell -Command "Start-Process cmd -Verb RunAs -ArgumentList '/c mklink /J \"%DST%\" \"%SRC%\" & pause'"
