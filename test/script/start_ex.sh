#!/bin/bash

rm -rf ../../../out/

pytest -vs --html ../out/build_option_report.html ../example/test_build_option.py

pkill -f '/pyd.py --root /root/.pycache --start'

