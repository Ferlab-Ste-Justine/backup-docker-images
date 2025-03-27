import datetime
import subprocess
import os
import re
import time

import boto3
from botocore.client import Config

import cmd_utils

S3_ENDPOINT = os.environ.get('S3_ENDPOINT')
S3_BUCKET = os.environ.get('S3_BUCKET')
S3_ACCESS_KEY = os.environ.get('S3_ACCESS_KEY')
S3_SECRET_KEY = os.environ.get('S3_SECRET_KEY')
S3_REGION = os.environ.get('S3_REGION')

S3_DUMP_OBJECT = os.environ.get('S3_DUMP_OBJECT', '')

BACKUP_NAME_REGEX = re.compile('^backup-(?P<timestamp>.*)[.]dump$')
def _get_obj_date(obj):
    timestamp = datetime.datetime.fromisoformat(
        BACKUP_NAME_REGEX.search(obj.key).group('timestamp')
    )
    return timestamp

def download_dump(
    dump_path,
    s3_object, 
    s3_bucket,
    s3
):
    print("Downloading dump ...")
    if s3_object == "":
        objs = s3.Bucket(s3_bucket).objects.all()
        objs = sorted(objs, key=_get_obj_date, reverse=True)
        if len(objs) == 0:
            print("No backup dump to restore from")
            exit(1)
        s3_object = objs[0].key

    s3.Bucket(s3_bucket).download_file(s3_object, dump_path)
        
def restore_from_dump(
    dump_path
):
    print("Restoring from dump ...")
    cmd = cmd_utils.get_restore_cmd(dump_path)
    subprocess.run(cmd, shell=True, check=True)
    
if __name__ == "__main__":
    start = time.time()

    s3 = boto3.resource(
        's3',
        endpoint_url=S3_ENDPOINT,
        aws_access_key_id=S3_ACCESS_KEY,
        aws_secret_access_key=S3_SECRET_KEY,
        config=Config(signature_version='s3v4'),
        region_name=S3_REGION
    )
    download_dump(
        "opt/backup.dump",
        S3_DUMP_OBJECT, 
        S3_BUCKET,
        s3
    )
    restore_from_dump(
        "opt/backup.dump"
    )

    duration = (time.time() - start) / 60
    print(f"\nThe script took {duration:.2f} minute(s) to run.")
