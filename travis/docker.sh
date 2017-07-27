#!/bin/bash

set -e

# Build docker image
sudo docker build --rm=true --file docker/crawler/Dockerfile --tag=gas1121/JapanCinemaStatusSpider:crawler-test .
sudo docker build --rm=true --file docker/scheduler/Dockerfile --tag=gas1121/JapanCinemaStatusSpider:scheduler-test .

# start target service for testing
sudo docker-compose -f travis/docker-compose.test.yml up -d

# waiting 10 secs
sleep 10

# run tests
sudo docker-compose -f travis/docker-compose.test.yml exec scheduler nosetests -v
sudo docker-compose -f travis/docker-compose.test.yml exec scheduler python tests/online.py

# spin down compose
sudo docker-compose -f travis/docker-compose.test.yml down

# remove 'test' images
sudo docker rmi gas1121/JapanCinemaStatusSpider:crawler-test
sudo docker rmi gas1121/JapanCinemaStatusSpider:scheduler-test
