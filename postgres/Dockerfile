FROM postgres:14

RUN apt-get update && apt-get install -y python3 python3-pip
RUN pip3 install boto3===1.16.49

COPY backup.py prune-backups.py restore.py /opt/