FROM python:2.7.17-buster

WORKDIR /usr/src/app
COPY . .
RUN pip install -r requirements.txt

CMD [ "sh", "sqlite_run.sh" ]
