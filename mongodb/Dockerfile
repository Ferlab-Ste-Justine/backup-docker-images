FROM mongo:4.4.18

RUN apt-get update && apt-get install -y python3 python3-pip
RUN pip3 install boto3===1.16.49

COPY mongodb/cmd_utils.py common/backup.py common/prune-backups.py common/restore.py /opt/
