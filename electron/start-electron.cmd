@echo off
setlocal
set ELECTRON_RUN_AS_NODE=
cd /d "%~dp0\.."
call ".\node_modules\.bin\electron.cmd" .
