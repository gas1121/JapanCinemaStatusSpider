#!/bin/bash

set -e

# Build docker image
sudo docker build --rm=true --file docker/utils/Dockerfile --tag=gas1121/japancinemastatusspider:utils-test .
sudo docker build --rm=true --file docker/crawler/Dockerfile --tag=gas1121/japancinemastatusspider:crawler-test .
sudo docker build --rm=true --file docker/scheduler/Dockerfile --tag=gas1121/japancinemastatusspider:scheduler-test .
sudo docker build --rm=true --file docker/data_processor/Dockerfile --tag=gas1121/japancinemastatusspider:data_processor-test .

# create tempory dir to store combined coverage data
mkdir -p coverage/utils
mkdir -p coverage/crawler
mkdir -p coverage/scheduler
mkdir -p coverage/data_processor
sudo chown -R travis:travis coverage

# start target service for testing
sudo docker-compose -f travis/docker-compose.test.yml up -d

# waiting 10 secs
sleep 10

# install package for test
sudo docker-compose -f travis/docker-compose.test.yml exec utils pip install coverage
sudo docker-compose -f travis/docker-compose.test.yml exec crawler pip install coverage
sudo docker-compose -f travis/docker-compose.test.yml exec scheduler pip install coverage
sudo docker-compose -f travis/docker-compose.test.yml exec data_processor pip install coverage

# run tests
sudo docker-compose -f travis/docker-compose.test.yml exec utils ./run_tests.sh
sudo docker-compose -f travis/docker-compose.test.yml exec crawler ./run_tests.sh
sudo docker-compose -f travis/docker-compose.test.yml exec scheduler ./run_tests.sh
sudo docker-compose -f travis/docker-compose.test.yml exec data_processor ./run_tests.sh
# get coverage data from container
sudo docker cp $(sudo docker-compose -f travis/docker-compose.test.yml ps -q utils):/app/.coverage coverage/utils
sudo docker cp $(sudo docker-compose -f travis/docker-compose.test.yml ps -q crawler):/app/.coverage coverage/crawler
sudo docker cp $(sudo docker-compose -f travis/docker-compose.test.yml ps -q scheduler):/app/.coverage coverage/scheduler
sudo docker cp $(sudo docker-compose -f travis/docker-compose.test.yml ps -q data_processor):/app/.coverage coverage/data_processor
# change path in coverage data
sudo sed -i 's#/app#'"$PWD"'/utils#g' coverage/utils/.coverage
sudo sed -i 's#/app#'"$PWD"'/crawler#g' coverage/crawler/.coverage
sudo sed -i 's#/app#'"$PWD"'/scheduler#g' coverage/scheduler/.coverage
sudo sed -i 's#/app#'"$PWD"'/data_processor#g' coverage/data_processor/.coverage
# combine coverage data
pip install coverage coveralls
cd coverage && coverage combine utils/.coverage crawler/.coverage scheduler/.coverage data_processor/.coverage
sudo mv .coverage ..
cd ..
sudo chown travis:travis .coverage
# send coverage report
coveralls

# spin down compose
sudo docker-compose -f travis/docker-compose.test.yml down

# remove 'test' images
sudo docker rmi gas1121/japancinemastatusspider:utils-test
sudo docker rmi gas1121/japancinemastatusspider:crawler-test
sudo docker rmi gas1121/japancinemastatusspider:scheduler-test
sudo docker rmi gas1121/japancinemastatusspider:data_processor-test
