import sys
import subprocess
import datetime
import os

def sync(host, remote_dir, local_dir):
    now = str(datetime.datetime.now())

    backup_path = f"{local_dir}/{now}"
    latest_link = f"{local_dir}/latest"

    os.makedirs(backup_path)

    res = subprocess.run([
        "/usr/bin/rsync",
        "-avp",
        "--timeout",
        "10",
        "--delete",
        f"{host}:{remote_dir}",
        "--link-dest", latest_link,
        "--exclude", ".cache",
        backup_path
    ])

    if res.returncode != 0:
        raise OSError(f"Sync returned code: {res.returncode}")

    if os.path.exists(latest_link):
        os.remove(latest_link)
    os.symlink(backup_path, latest_link, True)


if __name__ == "__main__":
    sync(1, 2, 3)
