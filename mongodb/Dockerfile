FROM mongo:4.4.18

# To avoid this issue: https://www.mongodb.com/docs/v4.4/reference/installation-ubuntu-community-troubleshooting/#errors-when-running-sudo-apt-update
RUN rm /etc/apt/sources.list.d/mongodb-org.list

RUN apt-get update && apt-get install -y python3 python3-pip
RUN pip3 install boto3===1.16.49

COPY mongodb/cmd_utils.py common/backup.py common/prune-backups.py common/restore.py /opt/
