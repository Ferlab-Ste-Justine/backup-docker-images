import os

def get_backup_cmd(backup_path):
    return f"pg_dump -Fc > {backup_path}"
    
def get_restore_cmd(dump_path):
    database = os.environ.get('PGDATABASE')
    return f"pg_restore --no-owner -d {database} {dump_path}"
