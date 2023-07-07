import datetime
import re
import os
import boto3
from botocore.client import Config

S3_ENDPOINT = os.environ.get('S3_ENDPOINT')
S3_BUCKET = os.environ.get('S3_BUCKET')
S3_ACCESS_KEY = os.environ.get('S3_ACCESS_KEY')
S3_SECRET_KEY = os.environ.get('S3_SECRET_KEY')
S3_REGION = os.environ.get('S3_REGION')
#Defaults to 30 days in seconds. 
S3_BACKUP_MAX_AGE = int(os.environ.get('S3_BACKUP_MAX_AGE', '2592000'))

def get_backup_list(
    s3,
    s3_bucket
):
    return s3.Bucket(s3_bucket).objects.all()

#backup-2021-01-06T22:06:31.106555.dump
BACKUP_NAME_REGEX = re.compile('^backup-(?P<timestamp>.*)[.]dump$')
def filter_expired_objects(
    objects,
    max_age,
    now_datetime
):
    def expired(obj):
        timestamp = datetime.datetime.fromisoformat(
            BACKUP_NAME_REGEX.search(obj.key).group('timestamp')
        )
        return (now_datetime - timestamp) >= datetime.timedelta(seconds=max_age)
    return filter(expired, objects)

def delete_objects(
    s3,
    s3_bucket,
    objects
):
    for obj in objects:
        s3.Object(s3_bucket, obj.key).delete()

if __name__ == "__main__":
    s3 = boto3.resource(
        's3',
        endpoint_url=S3_ENDPOINT,
        aws_access_key_id=S3_ACCESS_KEY,
        aws_secret_access_key=S3_SECRET_KEY,
        config=Config(signature_version='s3v4'),
        region_name=S3_REGION
    )
    objects = get_backup_list(
        s3,
        S3_BUCKET
    )
    expired_objects = filter_expired_objects(
        objects,
        S3_BACKUP_MAX_AGE,
        datetime.datetime.now()
    )
    delete_objects(
        s3,
        S3_BUCKET,
        expired_objects
    )