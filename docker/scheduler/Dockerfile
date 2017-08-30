FROM library/python:3.6

ARG USE_MIRROR=0

# mirror setting

# use ustc mirrors if needed
COPY docker/set_mirror.sh /tmp/
RUN chmod +x /tmp/set_mirror.sh
RUN /tmp/set_mirror.sh $USE_MIRROR

# install latest scutils

# os setup

# install dockerize
RUN apt-get update && apt-get install -y wget
ENV DOCKERIZE_VERSION v0.5.0
RUN wget https://github.com/jwilder/dockerize/releases/download/$DOCKERIZE_VERSION/dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
    && tar -C /usr/local/bin -xzvf dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
    && rm dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz

RUN apt-get update
RUN git clone -b custom-dev https://github.com/gas1121/scrapy-cluster.git /temp/scrapy-cluster
WORKDIR /temp/scrapy-cluster/kafka-monitor
RUN pip install -r requirements.txt
# install kafka_monitor.py as module
COPY docker/scheduler/setup.py /temp/scrapy-cluster/kafka-monitor
RUN pip install .

# install requirements

RUN mkdir -p /app
# install utils
COPY utils /utils
COPY scheduler /app
COPY docker/run_tests.sh /app
RUN chmod +x /app/run_tests.sh
WORKDIR /app
RUN pip install -r requirements.txt
RUN rm -rf /utils

CMD dockerize -wait tcp://kafka:9092 -wait tcp://redis:6379 -timeout 20s python run.py
