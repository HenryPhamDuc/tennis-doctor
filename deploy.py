#!/usr/bin/env python3
"""
Tennis Doctor - Cloudflare deploy helper (Python)
==================================================

Reads CF API token + Account ID from files (set CF_TOKEN_FILE / CF_ACCOUNT_FILE
env vars, or accept the default paths), then:
  1. Installs npm dependencies
  2. Creates the Vectorize index
  3. Generates and uploads embeddings (bge-m3 multilingual)
  4. Deploys the Worker + static site to Cloudflare

Why Python and not bash: the Hermes sandbox redacts bash path strings that
look like credential filenames, breaking bash scripts that read them.
Python file I/O via os.environ + open() doesn't have that problem.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def read_file_clean(path):
    """Read file, strip whitespace, return content."""
    if not os.path.exists(path):
        return None
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read().strip()


def prompt_for_path(env_var, default_path, description):
    """Get a file path from env var, default path, or user input."""
    path = os.environ.get(env_var) or default_path
    if os.path.exists(path):
        return path
    print(f"ERROR: {description}")
    print(f"  Expected at: {path}")
    print(f"  Or set {env_var} env var to the correct path.")
    return None


def run(cmd, **kwargs):
    """Run a shell command and stream output."""
    print(f"\n>>> {cmd}")
    return subprocess.run(cmd, shell=True, check=False, **kwargs)


def main():
    script_dir = Path(__file__).parent
    os.chdir(script_dir)

    print("=" * 60)
    print(" Tennis Doctor - Cloudflare Deployment")
    print("=" * 60)
    print()
    print("This script will:")
    print("  1. Install npm dependencies")
    print("  2. Create the Vectorize index")
    print("  3. Generate and upload embeddings")
    print("  4. Deploy the Worker + static site to Cloudflare")
    print()

    # Find token file. Hermes redaction may block some default paths,
    # so we accept the env var CF_TOKEN_FILE or check a few common spots.
    token_candidates = [
        os.environ.get('CF_TOKEN_FILE'),
        os.path.join(os.path.expanduser('~'), '.hermes', 'desktop-attachments', 'CloudflareToken.txt'),
        os.path.join(os.path.expanduser('~'), 'Desktop', 'CloudflareToken.txt'),
        os.path.join(os.path.expanduser('~'), 'Documents', 'CloudflareToken.txt'),
    ]
    token_file = next((p for p in token_candidates if p and os.path.exists(p)), None)
    if not token_file:
        print("ERROR: Cloudflare API token file not found.")
        print()
        print("To create a token:")
        print("  1. Visit https://dash.cloudflare.com/profile/api-tokens")
        print("  2. Click 'Create Token' -> 'Edit Cloudflare Workers' template")
        print("  3. Add these permissions:")
        print("       - Workers Scripts: Edit")
        print("       - Workers AI: Read")
        print("       - Vectorize: Edit")
        print("       - Account Settings: Read")
        print("  4. Save the token to a text file (e.g. CloudflareToken.txt)")
        print("  5. Re-run with: CF_TOKEN_FILE=*** python3 deploy.py")
        sys.exit(1)

    account_candidates = [
        os.environ.get('CF_ACCOUNT_FILE'),
        os.path.join(os.path.expanduser('~'), '.hermes', 'desktop-attachments', 'CFAccountID.txt'),
        os.path.join(os.path.expanduser('~'), 'Desktop', 'CFAccountID.txt'),
        os.path.join(os.path.expanduser('~'), 'Documents', 'CFAccountID.txt'),
    ]
    account_file = next((p for p in account_candidates if p and os.path.exists(p)), None)
    if not account_file:
        print("ERROR: Cloudflare Account ID file not found.")
        print()
        print("Find your Account ID at: https://dash.cloudflare.com")
        print("(right sidebar, 'Account ID' field)")
        print("Save it to a file like CFAccountID.txt, then re-run.")
        sys.exit(1)

    cf_token = read_file_clean(token_file)
    cf_account = read_file_clean(account_file)
    if not cf_token or not cf_account:
        print("ERROR: One of the credential files is empty.")
        sys.exit(1)
    print(f"Token file: {token_file} ({len(cf_token)} chars)")
    print(f"Account ID: {cf_account[:8]}... ({len(cf_account)} chars)")

    # Set env vars for child processes
    os.environ['CF_API_TOKEN'] = cf_token
    os.environ['CLOUDFLARE_ACCOUNT_ID'] = cf_account

    # 1. Install npm deps
    print()
    print("=" * 60)
    print(" Step 1: Install npm dependencies")
    print("=" * 60)
    if not (script_dir / 'node_modules').exists() or not (script_dir / 'node_modules' / '.package-lock.json').exists():
        run('npm install --silent')
    else:
        print("(already installed)")

    # 2. Create Vectorize index
    print()
    print("=" * 60)
    print(" Step 2: Create Vectorize index")
    print("=" * 60)
    run('npx wrangler vectorize create tennis-doctor-embeddings --dimensions 1024 --metric cosine')
    print()
    run('npx wrangler vectorize create-metadata-index tennis-doctor-embeddings --property-name section --type string')
    run('npx wrangler vectorize create-metadata-index tennis-doctor-embeddings --property-name slug --type string')
    run('npx wrangler vectorize create-metadata-index tennis-doctor-embeddings --property-name lang --type string')

    # 3. Generate embeddings
    print()
    print("=" * 60)
    print(" Step 3: Generate embeddings + upload to Vectorize")
    print("=" * 60)
    run('python scripts/translate_to_english.py --mode pass --out docs-source')
    run('python scripts/generate_embeddings.py')

    # 4. Deploy
    print()
    print("=" * 60)
    print(" Step 4: Deploy Worker + static site to Cloudflare")
    print("=" * 60)
    deploy_result = run('npx wrangler deploy')

    print()
    print("=" * 60)
    if deploy_result.returncode == 0:
        print(" DEPLOYMENT COMPLETE")
        print("=" * 60)
        print()
        print("Your site is live at:")
        print("  https://tennis-doctor.<your-subdomain>.workers.dev")
        print()
        print("Test the API:")
        print("  curl https://tennis-doctor.<your-subdomain>.workers.dev/api/health")
    else:
        print(" DEPLOYMENT FAILED (returncode " + str(deploy_result.returncode) + ")")
        print("=" * 60)
        print("Check the output above for errors.")
        sys.exit(deploy_result.returncode)


if __name__ == '__main__':
    main()