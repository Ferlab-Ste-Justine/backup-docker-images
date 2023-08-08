import os

def get_backup_cmd(backup_path):
    mongodb_uri = os.environ.get('MONGO_URL')
    mongodb_database = os.environ.get('MONGO_DATABASE')
    return f'mongodump --uri="{mongodb_uri}" --db={mongodb_database} --archive > {backup_path}'
    
def get_restore_cmd(dump_path):
    mongodb_uri = os.environ.get('MONGO_URL')
    mongodb_database = os.environ.get('MONGO_DATABASE')
    return f'mongorestore --uri="{mongodb_uri}" --nsInclude={mongodb_database}.* --archive < {dump_path}'
