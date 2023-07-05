#!/bin/bash

while true; do
  sudo docker run --pull=always -p 5002-5010:5002-5010 -v sw_vol:/safeweb_ai/output safeweb/ai
  sleep 5
done
