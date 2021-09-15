# syntax=docker/dockerfile:1
FROM python:3.7-slim-buster

WORKDIR /app


COPY . .

RUN pip install pipenv
RUN pipenv install
RUN mkdir /photo_folder

VOLUME /app/auth

CMD [  "pipenv", "run", "python", "upload.py" , "--up", "--path", "/photo_folder"]

#docker run -it --rm --name gphotoup -v /tmp/auth:/app/auth -v /tmp/pht:/photo_folder gphotoup
#docker run -it --rm --name gphotoup -v /tmp/auth:/app/auth -v /tmp/pht:/photo_folder gphotoup /bin/bash
#pipenv run python upload.py --up --path /photo_folder
#pipenv run python upload.py --ls





