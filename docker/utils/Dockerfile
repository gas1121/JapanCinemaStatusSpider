FROM library/python:3.6

ARG USE_MIRROR=0

# mirror setting

# use ustc mirrors if needed
COPY docker/set_mirror.sh /tmp/
RUN chmod +x /tmp/set_mirror.sh
RUN /tmp/set_mirror.sh $USE_MIRROR

# install dependency

# os setup
RUN apt-get update
RUN mkdir -p /app
COPY utils /app
COPY docker/run_tests.sh /app
RUN chmod +x /app/run_tests.sh
WORKDIR /app
RUN pip install .
RUN pip install nose

# run command
CMD ["ping", "localhost"]
