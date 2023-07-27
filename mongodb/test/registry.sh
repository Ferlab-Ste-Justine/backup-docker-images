#!/bin/sh -e

docker run -d -p 5000:5000 --restart=always --name my_local_registry registry:2.8.2
