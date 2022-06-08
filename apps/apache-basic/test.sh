#!/bin/bash

im=$(docker images -q nua-apache-basic:2.4.52-2)
cont=$(docker run -d -p 8080:80 $im)
sleep 1
curl http://127.0.0.1:8080
docker kill $cont
