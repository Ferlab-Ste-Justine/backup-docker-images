def get_backup_cmd(backup_path):
    return f"etcdctl snapshot save {backup_path}"
