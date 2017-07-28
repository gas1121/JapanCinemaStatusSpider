#!/bin/bash

set -e

# Build docker image
sudo docker build --rm=true --file docker/crawler/Dockerfile --tag=gas1121/japancinemastatusspider:crawler-test .
sudo docker build --rm=true --file docker/scheduler/Dockerfile --tag=gas1121/japancinemastatusspider:scheduler-test .

# start target service for testing
sudo docker-compose -f travis/docker-compose.test.yml up -d

# waiting 10 secs
sleep 10

sudo docker-compose -f travis/docker-compose.test.yml ps
sudo docker-compose -f travis/docker-compose.test.yml exec zookeeper ls
sudo docker-compose -f travis/docker-compose.test.yml exec redis ls

# install package for test
sudo docker-compose -f travis/docker-compose.test.yml exec scheduler pip install coverage coveralls


# run tests
sudo docker-compose -f travis/docker-compose.test.yml exec scheduler nosetests -v --with-coverage --cover-erase
sudo docker-compose -f travis/docker-compose.test.yml exec scheduler python tests/online.py
# send coverage report
sudo docker-compose -f travis/docker-compose.test.yml exec coveralls
# TODO combine different module coverage reports

# spin down compose
sudo docker-compose -f travis/docker-compose.test.yml down

# remove 'test' images
sudo docker rmi gas1121/japancinemastatusspider:crawler-test
sudo docker rmi gas1121/japancinemastatusspider:scheduler-test
