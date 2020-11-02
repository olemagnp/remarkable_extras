import sys
import subprocess
import datetime
import os

def sync(host, remote_dir, local_dir):
    now = str(datetime.datetime.now())

    backup_path = f"{local_dir}/{now}"
    latest_link = f"{local_dir}/latest"

    os.makedirs(backup_path)

    subprocess.run([
        "/usr/bin/rsync",
        "-avp",
        "--delete",
        f"{host}:{remote_dir}",
        "--link-dest", latest_link,
        "--exclude", ".cache",
        backup_path
    ])

    if os.path.exists(latest_link):
        os.remove(latest_link)
    os.symlink(backup_path, latest_link, True)


if __name__ == "__main__":
    sync(1, 2, 3)
