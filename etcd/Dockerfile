FROM python:3.9-alpine

ARG ETCD_VERSION=v3.4.15

RUN wget -O /opt/etcd-${ETCD_VERSION}-linux-amd64.tar.gz https://storage.googleapis.com/etcd/${ETCD_VERSION}/etcd-${ETCD_VERSION}-linux-amd64.tar.gz && \
    mkdir -p /opt/etcd && \
    tar xzvf /opt/etcd-${ETCD_VERSION}-linux-amd64.tar.gz -C /opt/etcd && \
    cp /opt/etcd/etcd-${ETCD_VERSION}-linux-amd64/etcd /usr/local/bin/etcd && \
    cp /opt/etcd/etcd-${ETCD_VERSION}-linux-amd64/etcdctl /usr/local/bin/etcdctl && \
    rm -f /opt/etcd-${ETCD_VERSION}-linux-amd64.tar.gz && \
    rm -rf /opt/etcd

RUN pip3 install boto3===1.16.49

COPY backup.py prune-backups.py /opt/