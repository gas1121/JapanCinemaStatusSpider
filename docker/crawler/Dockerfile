FROM library/python:3.6

ARG USE_MIRROR=0

# mirror setting

# use ustc mirrors if needed
COPY docker/set_mirror.sh /tmp/
RUN chmod +x /tmp/set_mirror.sh
RUN /tmp/set_mirror.sh $USE_MIRROR

# install scrapy-cluster

# os setup
RUN apt-get update && apt-get -y install \
  python-lxml \
  build-essential \
  libssl-dev \
  libffi-dev \
  python-dev \
  libxml2-dev \
  libxslt1-dev \
  && rm -rf /var/lib/apt/lists/*
RUN git clone -b py3 https://github.com/gas1121/scrapy-cluster.git /temp/scrapy-cluster
WORKDIR /temp/scrapy-cluster/crawler
# add a setup.py file to install as package
COPY docker/crawler/setup.py .
RUN pip install -r requirements.txt
RUN pip install .

# install other requirements

RUN mkdir -p /app
# install utils
COPY utils /utils
COPY crawler /app
COPY docker/run_tests.sh /app
RUN chmod +x /app/run_tests.sh
WORKDIR /app
RUN pip install -r requirements.txt
RUN rm -rf /utils

# by default run walkerplus_movie spider, override this in compose file
CMD scrapy crawl walkerplus_movie