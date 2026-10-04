import argparse
import json
import os
import shutil
import sys

def get_workspace_root():
    d = os.getcwd()
    while d != os.path.dirname(d):
        if os.path.exists(os.path.join(d, '.agents')):
            return d
        d = os.path.dirname(d)
    return os.getcwd()

def get_current_run(root):
    curr_file = os.path.join(root, 'runs', 'CURRENT')
    if os.path.exists(curr_file):
        with open(curr_file, 'r', encoding='utf-8') as f:
            return f.read().strip()
    return None

def stop(reason):
    root = get_workspace_root()
    state_dir = os.path.join(root, '.agents', 'state')
    os.makedirs(state_dir, exist_ok=True)
    stop_file = os.path.join(state_dir, 'STOP')
    
    with open(stop_file, 'w', encoding='utf-8') as f:
        f.write(reason + '\n')
        
    run = get_current_run(root)
    if run:
        state_file = os.path.join(root, 'runs', run, 'state.json')
        if os.path.exists(state_file):
            shutil.copy(state_file, os.path.join(root, 'runs', run, 'kill-snapshot.json'))
            
        events_file = os.path.join(root, 'runs', run, 'events.jsonl')
        with open(events_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps({'type': 'KILL', 'reason': reason}) + '\n')
            
    print(f"Run stopped: {reason}")

def resume():
    root = get_workspace_root()
    stop_file = os.path.join(root, '.agents', 'state', 'STOP')
    if os.path.exists(stop_file):
        os.remove(stop_file)
        print("Run resumed.")
    else:
        print("Run is not stopped.")

def status():
    root = get_workspace_root()
    stop_file = os.path.join(root, '.agents', 'state', 'STOP')
    if os.path.exists(stop_file):
        with open(stop_file, 'r', encoding='utf-8') as f:
            reason = f.read().strip()
        print(f"STOPPED: {reason}")
    else:
        print("ACTIVE")

def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='command', required=True)
    
    parser_stop = subparsers.add_parser('stop')
    parser_stop.add_argument('--reason', required=True)
    
    parser_resume = subparsers.add_parser('resume')
    parser_status = subparsers.add_parser('status')
    
    args = parser.parse_args()
    
    if args.command == 'stop':
        stop(args.reason)
    elif args.command == 'resume':
        resume()
    elif args.command == 'status':
        status()

if __name__ == '__main__':
    main()
