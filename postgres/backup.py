import datetime
import subprocess
import os

import boto3
from botocore.client import Config


DB_HOST = os.environ.get('DB_HOST')
DB_PORT = os.environ.get('DB_PORT', '5432')
DB = os.environ.get('DB')
DB_USER = os.environ.get('DB_USER')
DB_PASSWORD = os.environ.get('DB_PASSWORD')

S3_ENDPOINT = os.environ.get('S3_ENDPOINT')
S3_BUCKET = os.environ.get('S3_BUCKET')
S3_ACCESS_KEY = os.environ.get('S3_ACCESS_KEY')
S3_SECRET_KEY = os.environ.get('S3_SECRET_KEY')
S3_REGION = os.environ.get('S3_REGION')

def get_backup_file(
    db_host, 
    db_port, 
    db, 
    db_user, 
    db_password, 
    iso_datetime, 
    dir='/opt'
):
    pgpass_path = os.path.expanduser("~/.pgpass")
    with open(pgpass_path, mode='w+') as file:
        file.write(
            "{db_host}:{db_port}:{db}:{db_user}:{db_password}".format(
                db_host=db_host,
                db_port=db_port,
                db=db,
                db_user=db_user,
                db_password=db_password
            )
        )
    backup_path = os.path.join(dir, 'backup-{fn}.dump'.format(fn=iso_datetime))
    os.chmod(pgpass_path, 0o600)
    cmd = "pg_dump --dbname={db} --host={db_host} --username={db_user} > {backup_path}".format(
        db=db,
        db_host=db_host,
        db_user=db_user,
        backup_path=backup_path
    )
    subprocess.run(cmd, shell=True, check=True)
    return backup_path

def send_to_s3(
    backup_path, 
    s3_bucket,
    s3
):
    s3.Bucket(s3_bucket).upload_file(backup_path, os.path.basename(backup_path))

if __name__ == "__main__":
    backup_path = get_backup_file(
        DB_HOST,
        DB_PORT,
        DB,
        DB_USER,
        DB_PASSWORD,
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