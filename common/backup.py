import datetime
import subprocess
import os
import time

import boto3
from botocore.client import Config

import cmd_utils

S3_ENDPOINT = os.environ.get('S3_ENDPOINT')
S3_BUCKET = os.environ.get('S3_BUCKET')
S3_ACCESS_KEY = os.environ.get('S3_ACCESS_KEY')
S3_SECRET_KEY = os.environ.get('S3_SECRET_KEY')
S3_REGION = os.environ.get('S3_REGION')

def get_backup_file(
    iso_datetime, 
    dir='/opt'
):
    print("Getting backup file ...")
    backup_path = os.path.join(dir, 'backup-{fn}.dump'.format(fn=iso_datetime))
    cmd = cmd_utils.get_backup_cmd(backup_path)
    subprocess.run(cmd, shell=True, check=True)
    return backup_path

def send_to_s3(
    backup_path, 
    s3_bucket,
    s3
):
    print("Sending to S3 ...")
    s3.Bucket(s3_bucket).upload_file(backup_path, os.path.basename(backup_path))

if __name__ == "__main__":
    start = time.time()

    backup_path = get_backup_file(
        datetime.datetime.now().isoformat(),
        '/opt'
    )
    s3 = boto3.resource(
        's3',
        endpoint_url=S3_ENDPOINT,
        aws_access_key_id=S3_ACCESS_KEY,
        aws_secret_access_key=S3_SECRET_KEY,
        config=Config(signature_version='s3v4'),
        region_name=S3_REGION
    )
    send_to_s3(
        backup_path, 
        S3_BUCKET,
        s3
    )

    duration = (time.time() - start) / 60
    print(f"\nThe script took {duration:.2f} minute(s) to run.")
