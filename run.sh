#!/bin/bash
set -xe
sudo docker-compose up
sudo docker run --name playa --mount type=bind,source="$(pwd)"/output,target=/playa/output --rm -it -p 5003:5003 --gpus all --device /dev/snd --entrypoint /bin/bash playa-playa 
