#!/bin/bash
nosetests -v --with-coverage --cover-erase
if [ $? -eq 1 ]; then
    echo "unit tests failed"
    exit 1
fi

shopt -s nullglob
for i in tests/online*.py; do
    nosetests -v --with-coverage $i
    if [ $? -eq 1 ]; then
        echo "integration tests failed"
        exit 1
    fi
done
