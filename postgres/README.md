# About

This image manages postgres databases backups in an s3 object store.

It uses the **pg_dump** backup strategy.

Other considered alternatives were a disk snapshot or a base tar filesystem backup combined with WAL backups.

# Usage

The image has two scripts used for separate pursuposes (they are intended to run in tandem as separate deamons):

- /opt/backup.py: Create a backup copy of a postgres database in s3.
  Environment variables:
    - DB_HOST: Host of the postgres database server
    - DB_PORT: Post the postgres database server is exposed on (defaults to 5432)
    - DB: Name of the database that should be backed up
    - DB_USER: User to that the backup script should connect to postgres as
    - DB_PASSWORD: Password that should be used to authenticate the postgres user
    - S3_ENDPOINT: Endpoint of the S3 object store that will store the backups
    - S3_BUCKET: S3 bucket that the backup files should be stored in
    - S3_ACCESS_KEY: Access key used to access the s3 object store
    - S3_SECRET_KEY: Secret key to authentify against the s3 object store
    - S3_REGION: Region to use

- /opt/prune-backups.py: Delete database backups in the object store that are too old
  Environment variables:
    - S3_ENDPOINT: Endpoint of the S3 object store that stores the backups
    - S3_BUCKET: S3 bucket that the backup files are stored in
    - S3_ACCESS_KEY: Access key used to access the s3 object store
    - S3_SECRET_KEY: Secret key to authentify against the s3 object store
    - S3_REGION: Region to use
    - S3_BACKUP_MAX_AGE: Maximum age (in seconds) that remaining backups can have. Any backups that are older than that will be deleted.

# Known Limitation

Technically, you may find yourself without backups if:
  - You run both scripts
  - The script that backups the database stops functioning and the situation is not addressed

So, two fairly reasonable things are assumed here:
  - You monitor the script that backs up your database and you address the situation in a timely manner if it stops working (a sane operating procedure either way, you don't want to rely on backups that are too old)
  - You set **S3_BACKUP_MAX_AGE** in the pruning script to a sufficiently large value to give you some leeway