from .sync import sync
from .rm_to_dir import RMDirectory
import json
import os
import sys

if __name__ == "__main__":
    conf_path = os.path.join(os.path.dirname(__file__), 'config.json')
    if len(sys.argv) > 1:
        conf_path = sys.argv[1]

    with open(conf_path) as f:
        config = json.loads(f.read())

    sync(config['host'], config['remote_dir'], config['local_raw_dir'])

    direc = RMDirectory(os.path.join(config['local_raw_dir'], 'latest', 'xochitl'))
    direc.to_readable(config['local_nice_dir'])
