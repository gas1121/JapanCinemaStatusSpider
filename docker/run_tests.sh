#!/bin/bash
nosetests -v --with-coverage --cover-erase
if [ $? -eq 1 ]; then
    echo "unit tests failed"
    exit 1
fi

nosetests -v --with-coverage tests/online.py
if [ $? -eq 1 ]; then
    echo "integration tests failed"
    exit 1
fi
