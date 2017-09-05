FROM library/python:3.6

ARG USE_MIRROR=0

# mirror setting

# use ustc mirrors if needed
COPY docker/set_mirror.sh /tmp/
RUN chmod +x /tmp/set_mirror.sh
RUN /tmp/set_mirror.sh $USE_MIRROR

# os setup

RUN apt-get update
RUN git clone -b custom-dev https://github.com/gas1121/scrapy-cluster.git /temp/scrapy-cluster
WORKDIR /temp/scrapy-cluster/rest
RUN pip install -r requirements.txt

RUN mkdir -p /usr/src/app
WORKDIR /temp/scrapy-cluster
# move codebase over
RUN cp -r rest/* /usr/src/app
# override settings via localsettings.py
COPY docker/rest/localsettings.py /usr/src/app/localsettings.py
# copy testing script into container
RUN cp docker/run_docker_tests.sh /usr/src/app/run_docker_tests.sh
# copy service guarder script
COPY docker/service_guarder.py /usr/src/app/service_guarder.py
# copy run script
COPY docker/run.sh /usr/src/app/run.sh
RUN chmod +x /usr/src/app/run.sh
WORKDIR /usr/src/app

CMD ./run.sh python rest_service.py
