@echo off
echo Installing required Python libraries...

python -m ensurepip --upgrade

python -m pip install --upgrade pip
python -m pip install pillow
python -m pip install opencv-python
python -m pip install numpy
python -m pip install psd-tools
python -m pip install lxml

echo.
echo All required libraries installed!
pause