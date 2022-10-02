FROM python:3.8
LABEL maintainer="jcsdavis@gmail.com"
COPY . /stuff
WORKDIR /stuff
RUN pip install -r requirements.txt
CMD ["python", "api.py"]
