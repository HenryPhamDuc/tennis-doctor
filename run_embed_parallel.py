#!/usr/bin/env python3
"""Run parallel hybrid embedding pipeline with credentials (unbuffered)."""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

token_file = os.path.join(HERE, 'CloudflareToken.txt')
account_file = os.path.join(HERE, 'CFAccountID.txt')

if not os.path.exists(token_file) or not os.path.exists(account_file):
    print('ERROR: missing credential files', file=sys.stderr)
    sys.exit(1)

env = os.environ.copy()
with open(token_file) as f:
    env['CF_API_TOKEN'] = f.read().strip()
with open(account_file) as f:
    env['CF_ACCOUNT_ID'] = f.read().strip()

args = sys.argv[1:]
cmd = [
    sys.executable,
    '-u',  # unbuffered stdout
    os.path.join(HERE, 'scripts', 'embed_ollama_parallel.py'),
] + args

result = subprocess.run(cmd, env=env)
sys.exit(result.returncode)
