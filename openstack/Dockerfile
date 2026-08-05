FROM python:3.14.6-slim-trixie

ENV PYTHONUNBUFFERED=1

RUN pip install --no-cache-dir openstacksdk===4.17.0

COPY openstack/snapshot.py openstack/prune-snapshots.py /opt/
