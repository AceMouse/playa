#!/bin/bash
set -xe
sudo docker-compose up --build 
sudo docker run --rm -it -p 5003:5003 --gpus all --entrypoint /bin/bash playa-playa
