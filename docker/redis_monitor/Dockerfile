FROM library/python:3.6

ARG USE_MIRROR=0

# mirror setting

# use ustc mirrors if needed
COPY docker/set_mirror.sh /tmp/
RUN chmod +x /tmp/set_mirror.sh
RUN /tmp/set_mirror.sh $USE_MIRROR

# os setup

# install dockerize
RUN apt-get update && apt-get install -y wget
ENV DOCKERIZE_VERSION v0.5.0
RUN wget https://github.com/jwilder/dockerize/releases/download/$DOCKERIZE_VERSION/dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
    && tar -C /usr/local/bin -xzvf dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
    && rm dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz

RUN apt-get update
RUN git clone -b custom-dev https://github.com/gas1121/scrapy-cluster.git /temp/scrapy-cluster
WORKDIR /temp/scrapy-cluster/redis-monitor
RUN pip install -r requirements.txt

RUN mkdir -p /usr/src/app
WORKDIR /temp/scrapy-cluster
# move codebase over
RUN cp -r redis-monitor/* /usr/src/app
# override settings via localsettings.py
COPY docker/redis_monitor/localsettings.py /usr/src/app/localsettings.py
# copy testing script into container
RUN cp docker/run_docker_tests.sh /usr/src/app/run_docker_tests.sh
WORKDIR /usr/src/app

CMD dockerize -wait tcp://kafka:9092 -wait tcp://redis:6379 -timeout 40s python redis_monitor.py
