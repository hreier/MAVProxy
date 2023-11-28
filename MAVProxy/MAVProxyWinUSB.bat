cd ..\
del c:\users\uberb\appdata\roaming\python\python311\site-packages\MAVProxy-1.8.67-py3.11.egg
python setup.py build install --user
rem python .\MAVProxy\mavproxy.py --console
pause
python .\MAVProxy\mavproxy.py --master=COM11 --baudrate 115200 --show-errors --target-system=1 --target-component=84 --aircraft=soleon --state-basedir=./logs --soleon

pause