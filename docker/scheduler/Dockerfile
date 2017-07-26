FROM library/python:3.6

ARG USE_MIRROR=0

# mirror setting

# use ustc mirrors if needed
COPY docker/set_mirror.sh /tmp/
RUN /tmp/set_mirror.sh $USE_MIRROR

# os setup
RUN apt-get update

# install requirements

COPY scheduler/requirements.txt /tmp/
RUN pip install -r /tmp/requirements.txt
RUN mkdir -p /app
WORKDIR /app

CMD python run.py
