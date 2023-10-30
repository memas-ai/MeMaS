FROM python:3.10

# Create app directory
WORKDIR /memas

# Install Universal Sentence Encoder
RUN wget https://tfhub.dev/google/universal-sentence-encoder/4?tf-hub-format=compressed -O use4.tar
RUN mkdir -p encoder/universal-sentence-encoder_4
RUN tar -xf use4.tar -C encoder/universal-sentence-encoder_4
RUN rm use4.tar

# Install app dependencies
COPY requirements.txt ./requirements.txt
RUN pip install -r requirements.txt
RUN python3 -c "import nltk; nltk.download('punkt')"


# Bundle app source
COPY logging.ini ./logging.ini
COPY memas ./memas
COPY --chmod=0755 memas-docker/wait-for-it.sh ./wait-for-it.sh
COPY --chmod=0755 memas-docker/init.sh ./init.sh


# Copy in the default config
ARG conf_file=memas-config.yml
ENV MEMAS_CONF_FILE=${conf_file}
COPY memas-docker/${conf_file} ./memas/${conf_file}
# TODO: provide way to use custom configs in docker compose


# Set the python path to include memas, since memas isn't technically a python package
ENV PYTHONPATH "$PYTHONPATH:memas"


EXPOSE 8010
CMD gunicorn -b :8010 -w 1 -k eventlet "memas.app:create_app()"
