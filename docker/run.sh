#!/bin/bash
python service_guarder.py
if [ $? -ne 0 ]; then
    echo "base service check failed"
    exit 1
fi
eval $@
