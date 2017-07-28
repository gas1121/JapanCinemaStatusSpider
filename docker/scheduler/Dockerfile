FROM library/python:3.6

ARG USE_MIRROR=0

# mirror setting

# use ustc mirrors if needed
COPY docker/set_mirror.sh /tmp/
RUN chmod +x /tmp/set_mirror.sh
RUN /tmp/set_mirror.sh $USE_MIRROR

# install latest scutils

# os setup
RUN apt-get update
RUN git clone -b py3 https://github.com/gas1121/scrapy-cluster.git /temp/scrapy-cluster
WORKDIR /temp/scrapy-cluster/kafka-monitor
RUN pip install -r requirements.txt
# install kafka_monitor.py as module
COPY docker/scheduler/setup.py /temp/scrapy-cluster/kafka-monitor
RUN pip install .

# install requirements

RUN mkdir -p /app
COPY scheduler /app
RUN pip install -r /app/requirements.txt
WORKDIR /app

CMD python run.py
