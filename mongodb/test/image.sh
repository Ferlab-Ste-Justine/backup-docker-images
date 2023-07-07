#!/bin/sh -e

docker build -t localhost:5000/mongodb-backup:test -f ../Dockerfile ../..

docker push localhost:5000/mongodb-backup:test
