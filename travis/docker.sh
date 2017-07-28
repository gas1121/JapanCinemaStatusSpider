#!/bin/bash

set -e

# Build docker image
sudo docker build --rm=true --file docker/crawler/Dockerfile --tag=gas1121/japancinemastatusspider:crawler-test .
sudo docker build --rm=true --file docker/scheduler/Dockerfile --tag=gas1121/japancinemastatusspider:scheduler-test .

# create tempory dir to store combined coverage data
mkdir -p coverage
sudo chown travis:travis coverage

# start target service for testing
sudo docker-compose -f travis/docker-compose.test.yml up -d

# waiting 10 secs
sleep 10

# install package for test
sudo docker-compose -f travis/docker-compose.test.yml exec scheduler pip install coverage coveralls

# run tests
sudo docker-compose -f travis/docker-compose.test.yml exec scheduler ./run_tests.sh
# use gist for test purpose
curl -L https://gist.githubusercontent.com/gas1121/778f2665f62ddd7b61d462fa53ee46fb/raw/travis_test_script.sh > travis_test_script.sh
sudo chmod +x travis_test_script.sh
./travis_test_script.sh
# combine coverage data
sudo docker-compose -f travis/docker-compose.test.yml exec scheduler bash -c "cd /coverage && coverage combine /app/.coverage"
# send coverage report
pip install coveralls
cd coverage
coveralls

# spin down compose
sudo docker-compose -f travis/docker-compose.test.yml down

# remove 'test' images
sudo docker rmi gas1121/japancinemastatusspider:crawler-test
sudo docker rmi gas1121/japancinemastatusspider:scheduler-test
