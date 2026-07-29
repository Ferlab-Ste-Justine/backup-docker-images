import os
import time

import mysql.connector

SR_HOST = os.environ.get('SR_HOST')
SR_PORT = int(os.environ.get('SR_PORT', '9030'))
SR_USER = os.environ.get('SR_USER', 'root')
SR_PASSWORD = os.environ.get('SR_PASSWORD')
SR_S3_BUCKET = os.environ.get('SR_S3_BUCKET')
SR_S3_REGION = os.environ.get('SR_S3_REGION', 'ca-central-1')
SR_BACKUP_EXPIRE_HOURS = int(os.environ.get('SR_BACKUP_EXPIRE_HOURS', '336'))

SYSTEM_DBS = {'information_schema', '_statistics_', 'starrocks', 'sys'}
POLL_INTERVAL = 60
BACKUP_TIMEOUT = 86400
RESTORE_TIMEOUT = 86400

def get_connection():
    return mysql.connector.connect(
        host=SR_HOST,
        port=SR_PORT,
        user=SR_USER,
        password=SR_PASSWORD,
    )

def get_user_databases(conn):
    cursor = conn.cursor()
    cursor.execute("SHOW DATABASES")
    dbs = [row[0] for row in cursor.fetchall() if row[0] not in SYSTEM_DBS]
    cursor.close()
    return dbs

def create_repository(conn):
    cursor = conn.cursor()
    try:
        cursor.execute(
            f"CREATE REPOSITORY sr_backup WITH BROKER "
            f"ON LOCATION 's3://{SR_S3_BUCKET}/backups' "
            f"PROPERTIES('aws.s3.use_aws_sdk_default_behavior'='true','aws.s3.region'='{SR_S3_REGION}')"
        )
    except mysql.connector.Error as e:
        if 'already exist' in str(e).lower():
            print("Repository sr_backup already exists.")
        else:
            raise
    cursor.close()

def submit_backup(conn, db, stamp):
    cursor = conn.cursor()
    try:
        cursor.execute(
            f"BACKUP SNAPSHOT `{db}`.snap_{stamp} TO sr_backup "
            f"PROPERTIES('timeout'='{BACKUP_TIMEOUT}','type'='FULL',"
            f"'expired_time'='{SR_BACKUP_EXPIRE_HOURS} hours')"
        )
    except mysql.connector.Error as e:
        if 'already exist' in str(e).lower():
            print(f"{db}/snap_{stamp} already submitted, checking state.")
        else:
            raise
    cursor.close()

def poll_backup(conn, db, stamp):
    waited = 0
    while True:
        cursor = conn.cursor()
        cursor.execute(f"SHOW BACKUP FROM `{db}`")
        rows = cursor.fetchall()
        cursor.close()

        state = next(
            (row[3] for row in rows if row[1] == f'snap_{stamp}'),
            None,
        )
        print(f"{db}: {state or 'PENDING'}")

        if state == 'FINISHED':
            return
        if state == 'CANCELLED':
            raise RuntimeError(f"Backup for {db}/snap_{stamp} was CANCELLED")

        time.sleep(POLL_INTERVAL)
        waited += POLL_INTERVAL
        if waited > BACKUP_TIMEOUT:
            raise RuntimeError(f"Backup for {db}/snap_{stamp} timed out after {BACKUP_TIMEOUT}s")

def submit_restore(conn, db, snapshot):
    cursor = conn.cursor()
    try:
        cursor.execute(
            f"RESTORE SNAPSHOT `{db}`.`{snapshot}` FROM sr_backup "
            f"PROPERTIES('timeout'='{RESTORE_TIMEOUT}','backup_timestamp'='-1')"
        )
    except mysql.connector.Error as e:
        if 'already exist' in str(e).lower():
            print(f"{db}/{snapshot} restore already submitted, checking state.")
        else:
            raise
    cursor.close()

def poll_restore(conn, db, snapshot):
    waited = 0
    while True:
        cursor = conn.cursor()
        cursor.execute(f"SHOW RESTORE FROM `{db}`")
        rows = cursor.fetchall()
        cursor.close()

        state = next(
            (row[4] for row in rows if row[2] == snapshot),
            None,
        )
        print(f"{db}/{snapshot}: {state or 'PENDING'}")

        if state == 'FINISHED':
            return
        if state == 'CANCELLED':
            raise RuntimeError(f"Restore for {db}/{snapshot} was CANCELLED")

        time.sleep(POLL_INTERVAL)
        waited += POLL_INTERVAL
        if waited > RESTORE_TIMEOUT:
            raise RuntimeError(f"Restore for {db}/{snapshot} timed out after {RESTORE_TIMEOUT}s")
