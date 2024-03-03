#!/bin/sh

python3 clean.py
python3 compile.py build_ext --inplace

cp start.sh binary/
cp keepaway.base/main_player.py  binary/keepaway.base/
cp keepaway.base/formation_dt/ binary/keepaway.base/ -r
rm binary/keepaway.base/main_player.cpython-36m-x86_64-linux-gnu.so


python3 clean.py c-files