#!/bin/bash

while true; do
  sudo docker run --rm --name bis_c --pull=always -p 5002-5010:5002-5010 -v ai_vol:/safeweb_ai/output <dockerhb_repo>/<dockerhb_image>:<dockerhb_tag>
  sleep 5
done
