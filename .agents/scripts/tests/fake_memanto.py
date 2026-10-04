import sys
import json

args = sys.argv[1:]
if 'status' in args:
    print('status: on-prem')
else:
    print('OK')
