FROM debian:stretch

RUN apt-get -q update && apt-get -yq install python python-simplejson python-apt
