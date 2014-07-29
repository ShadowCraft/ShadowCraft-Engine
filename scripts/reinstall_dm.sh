#!/bin/bash

cd wowapi
python setup.py build
python setup.py install
cd ../../
python setup_dm.py build
python setup_dm.py install