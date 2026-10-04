import argparse
import json
import os
import time
from datetime import datetime

# Simple file locking since fcntl is unix only and we are on windows
class FileLock:
    def __init__(self, filepath):
        self.lockfile = filepath + ".lock"
    
    def __enter__(self):
        while True:
            try:
                self.fd = os.open(self.lockfile, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                return self
            except FileExistsError:
                time.sleep(0.1)

    def __exit__(self, exc_type, exc_val, exc_tb):
        os.close(self.fd)
        os.unlink(self.lockfile)

def get_workspace_root():
    d = os.getcwd()
    while d != os.path.dirname(d):
        if os.path.exists(os.path.join(d, '.agents')):
            return d
        d = os.path.dirname(d)
    return os.getcwd()

def next_id(prefix):
    root = get_workspace_root()
    runs_dir = os.path.join(root, 'runs')
    os.makedirs(runs_dir, exist_ok=True)
    counters_file = os.path.join(runs_dir, 'counters.json')
    
    with FileLock(counters_file):
        try:
            with open(counters_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = {}
            
        if prefix == 'RUN':
            now = datetime.now()
            month_key = f"RUN-{now.year}-{now.month:02d}"
            count = data.get(month_key, 0) + 1
            data[month_key] = count
            res = f"{month_key}-{count:04d}"
        elif prefix == 'MC':
            count = data.get(prefix, 0) + 1
            data[prefix] = count
            res = f"{prefix}-{count:04d}"
        else:
            count = data.get(prefix, 0) + 1
            data[prefix] = count
            res = f"{prefix}-{count:03d}"
            
        with open(counters_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
            
    print(res)
    return res

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['next'])
    parser.add_argument('prefix', choices=['EVID', 'DEC', 'REQ', 'US', 'TEST', 'SRC', 'MC', 'RUN'])
    args = parser.parse_args()
    
    if args.command == 'next':
        next_id(args.prefix)

if __name__ == '__main__':
    main()
