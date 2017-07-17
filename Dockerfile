FROM library/python:alpine

ARG USE_MIRROR=0

# use ustc mirrors if needed
COPY docker/set_mirror.sh /tmp/
RUN /tmp/set_pip_mirror.sh

# install requirements
RUN apk update
RUN apk add python-dev curl libxml2-dev libxslt-dev \
    libffi-dev gcc musl-dev libgcc openssl-dev postgresql-dev
RUN curl https://bootstrap.pypa.io/get-pip.py | python
COPY requirements.txt /tmp/
RUN pip install -r /tmp/requirements.txt