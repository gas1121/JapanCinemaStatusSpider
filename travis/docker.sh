#!/bin/bash

set -e

# Build docker image
sudo docker build --rm=true --file docker/crawler/Dockerfile --tag=gas1121/japancinemastatusspider:crawler-test .
sudo docker build --rm=true --file docker/scheduler/Dockerfile --tag=gas1121/japancinemastatusspider:scheduler-test .

# create tempory dir to store combined coverage data
mkdir -p coverage

# start target service for testing
sudo docker-compose -f travis/docker-compose.test.yml up -d

# waiting 10 secs
sleep 10

# install package for test
sudo docker-compose -f travis/docker-compose.test.yml exec scheduler pip install coverage coveralls

# run tests
sudo docker-compose -f travis/docker-compose.test.yml exec scheduler ./run_tests.sh
# combine coverage data
sudo docker-compose -f travis/docker-compose.test.yml exec scheduler "cd /coverage && coverage combine /app/.coverage"
# send coverage report
pip install coveralls
cd coverage
coveralls

# spin down compose
sudo docker-compose -f travis/docker-compose.test.yml down

# remove 'test' images
sudo docker rmi gas1121/japancinemastatusspider:crawler-test
sudo docker rmi gas1121/japancinemastatusspider:scheduler-test
