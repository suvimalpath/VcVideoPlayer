FROM nikolaik/python-nodejs:python3.9-nodejs17
RUN apt update && apt upgrade -y
RUN apt install ffmpeg -y
RUN mkdir /innexia/
COPY . /innexia
WORKDIR /innexia
RUN pip3 install --upgrade pip
RUN pip3 install -U -r requirements.txt
CMD python3 main.py
