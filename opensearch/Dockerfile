FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

RUN pip install --no-cache-dir boto3==1.16.49 requests==2.31.0

COPY opensearch/backup.py common/prune-backups.py opensearch/restore.py /opt/
