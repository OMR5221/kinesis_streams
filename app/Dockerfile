FROM ubuntu:16.04

MAINTAINER Oswald Ramirez "Oswald.Ramirez"

RUN apt-get update -y && \
    apt-get install -y python3-pip python3-dev && \
    cd /usr/local/bin \
    && ln -s /usr/bin/python3 python \
    && pip3 install --upgrade pip
	
	
# ADD . /myapp_docker
COPY . /myapp_docker
WORKDIR /myapp_docker
RUN pip install -r requirements.txt
ENTRYPOINT [ "python3" ]
CMD ["application.py"]
