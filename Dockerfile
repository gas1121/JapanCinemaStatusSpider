FROM library/python:alpine
MAINTAINER gas1121 <jtdzhx@gmail.com>

# use ustc mirrors
RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.ustc.edu.cn/g' /etc/apk/repositories \
 && mkdir -p ~/.pip \
 && echo "[global]" > ~/.pip/pip.conf \
 && echo "timeout=60" >> ~/.pip/pip.conf \
 && echo "index-url = https://mirrors.ustc.edu.cn/pypi/web/simple" >> ~/.pip/pip.conf

# install requirements
RUN apk update
RUN apk add python-dev curl libxml2-dev libxslt-dev \
    libffi-dev gcc musl-dev libgcc openssl-dev
RUN curl https://bootstrap.pypa.io/get-pip.py | python
COPY requirements.txt /tmp/
RUN pip install -r /tmp/requirements.txt