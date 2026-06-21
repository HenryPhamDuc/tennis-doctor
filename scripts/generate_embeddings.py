#!/usr/bin/env python3
"""
Tennis Doctor - Embedding Pipeline (Vectorize)
================================================

Reads docs-source/_manifest.json, embeds each chunk using Cloudflare Workers
AI bge-m3 (multilingual, 1024-dim), and upserts to the Vectorize index.

Prereqs:
    - Cloudflare account ID + API token
    - Vectorize index 'tennis-doctor-embeddings' already created (1024-dim)

Env vars (read from .env or shell):
    CF_ACCOUNT_ID     - Cloudflare account ID
    CF_API_TOKEN      - Cloudflare API token with AI + Vectorize scopes

Usage:
    python scripts/generate_embeddings.py [--manifest PATH] [--limit N]
"""

import os
import sys
import json
import time
import argparse
import hashlib
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError


def load_env():
    """Load .env from script directory if present."""
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        for line in env_path.read_text(encoding='utf-8').splitlines():
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip())


def get_creds():
    account_id = os.environ.get('CF_ACCOUNT_ID')
    api_token = os.environ.get('CF_API_TOKEN')
    if not account_id or not api_token:
        print('ERROR: Set CF_ACCOUNT_ID and CF_API_TOKEN env vars (or in .env)', file=sys.stderr)
        sys.exit(1)
    return account_id, api_token


def embed_batch(texts, account_id, api_token, model='@cf/baai/bge-m3'):
    url = f'https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{model}'
    payload = json.dumps({'text': texts}).encode('utf-8')
    req = Request(url, data=payload, headers={
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json',
    })
    try:
        with urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            if not data.get('success'):
                raise RuntimeError(f'AI API error: {data}')
            result = data['result']
            if isinstance(result, dict):
                vectors = result.get('data') or result.get('embeddings') or result.get('embedding')
                if vectors and isinstance(vectors[0], list):
                    return vectors
                if vectors and isinstance(vectors, list):
                    return [vectors]
            if isinstance(result, list):
                if isinstance(result[0], list):
                    return result
                return [result]
            raise RuntimeError(f'Unexpected bge-m3 response: {type(result)}')
    except HTTPError as e:
        body = e.read().decode('utf-8')
        raise RuntimeError(f'HTTP {e.code}: {body}')


def vectorize_upsert(vectors, account_id, api_token, index_name='tennis-doctor-embeddings'):
    url = f'https://api.cloudflare.com/client/v4/accounts/{account_id}/vectorize/v2/indexes/{index_name}/upsert'
    payload = json.dumps({'vectors': vectors}).encode('utf-8')
    req = Request(url, data=payload, headers={
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json',
    })
    try:
        with urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            if not data.get('success'):
                raise RuntimeError(f'Vectorize error: {data}')
            return data.get('result', {})
    except HTTPError as e:
        body = e.read().decode('utf-8')
        raise RuntimeError(f'HTTP {e.code}: {body}')


def vectorize_index_info(account_id, api_token, index_name='tennis-doctor-embeddings'):
    url = f'https://api.cloudflare.com/client/v4/accounts/{account_id}/vectorize/v2/indexes/{index_name}'
    req = Request(url, headers={'Authorization': f'Bearer {api_token}'})
    try:
        with urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except HTTPError as e:
        if e.code == 404:
            return None
        raise


def deterministic_id(chunk_id):
    h = hashlib.md5(chunk_id.encode('utf-8')).hexdigest()
    return f'chunk_{h[:32]}'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', default='docs-source/_manifest.json')
    parser.add_argument('--batch-size', type=int, default=20)
    parser.add_argument('--upsert-batch', type=int, default=100)
    parser.add_argument('--limit', type=int, default=0, help='Limit total chunks (0=all)')
    parser.add_argument('--start-from', type=int, default=0, help='Skip first N chunks (for resume)')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--verbose', '-v', action='store_true')
    args = parser.parse_args()

    load_env()
    manifest_path = Path(args.manifest)
    if not manifest_path.exists():
        print(f'ERROR: {manifest_path} not found', file=sys.stderr)
        sys.exit(1)

    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    chunks = manifest['chunks']
    if args.start_from:
        chunks = chunks[args.start_from:]
    if args.limit:
        chunks = chunks[:args.limit]
    print(f'Manifest: {len(chunks)} chunks to embed')

    if args.dry_run:
        print('DRY RUN - first 3:')
        for c in chunks[:3]:
            print(f"  - {c['title'][:50]} ({c['section']}#{c['chunk_index']})")
        return

    account_id, api_token = get_creds()

    info = vectorize_index_info(account_id, api_token)
    if not info or not info.get('success'):
        print('ERROR: Vectorize index not found.', file=sys.stderr)
        print('Run: npx wrangler vectorize create tennis-doctor-embeddings --dimensions 1024 --metric cosine', file=sys.stderr)
        sys.exit(1)
    existing_count = info['result'].get('vector_count', 0)
    print(f'Index already has {existing_count} vectors')

    total = len(chunks)
    embedded = 0
    upserted = 0
    pending_vectors = []

    print(f'\nEmbedding {total} chunks...')
    start_time = time.time()

    for batch_start in range(0, total, args.batch_size):
        batch_end = min(batch_start + args.batch_size, total)
        batch = chunks[batch_start:batch_end]
        texts = [c['text'][:1500] for c in batch]  # cap input

        try:
            vectors = embed_batch(texts, account_id, api_token)
        except Exception as e:
            print(f'  ! batch {batch_start} error: {e}', file=sys.stderr)
            # Retry one at a time
            for c, t in zip(batch, texts):
                try:
                    v = embed_batch([t], account_id, api_token)
                    pending_vectors.append({
                        'id': deterministic_id(c['id']),
                        'values': v[0],
                        'metadata': {
                            'title': c['title'][:200],
                            'slug': c['slug'][:200],
                            'section': c.get('section', '')[:100],
                            'lang': c.get('lang', 'en'),
                            'text': c['text'][:2000],
                            'heading': c.get('heading', '')[:200],
                            'source_id': c['id'][:200],
                        },
                    })
                    embedded += 1
                except Exception as e2:
                    print(f'    ! skip {c["id"][:60]}: {e2}', file=sys.stderr)
        else:
            for c, v in zip(batch, vectors):
                pending_vectors.append({
                    'id': deterministic_id(c['id']),
                    'values': v,
                    'metadata': {
                        'title': c['title'][:200],
                        'slug': c['slug'][:200],
                        'section': c.get('section', '')[:100],
                        'lang': c.get('lang', 'en'),
                        'text': c['text'][:2000],
                        'heading': c.get('heading', '')[:200],
                        'source_id': c['id'][:200],
                    },
                })
            embedded += len(batch)

        if args.verbose:
            elapsed = time.time() - start_time
            rate = embedded / max(elapsed, 0.1)
            eta = (total - embedded) / max(rate, 0.1)
            print(f'  [{embedded}/{total}] {rate:.1f}/s, ETA: {eta:.0f}s', file=sys.stderr)

        # Flush
        if len(pending_vectors) >= args.upsert_batch:
            try:
                result = vectorize_upsert(pending_vectors, account_id, api_token)
                upserted += len(pending_vectors)
                if args.verbose:
                    print(f'  ↑ Upserted {len(pending_vectors)} (total: {upserted})', file=sys.stderr)
            except Exception as e:
                print(f'  ! Upsert error: {e}', file=sys.stderr)
            pending_vectors = []

        time.sleep(0.05)

    if pending_vectors:
        try:
            vectorize_upsert(pending_vectors, account_id, api_token)
            upserted += len(pending_vectors)
        except Exception as e:
            print(f'  ! Final upsert error: {e}', file=sys.stderr)

    elapsed = time.time() - start_time
    print(f'\n=== Embedding complete ===')
    print(f'  Embedded: {embedded} / {total}')
    print(f'  Upserted: {upserted}')
    print(f'  Time: {elapsed:.1f}s ({embedded / max(elapsed, 0.1):.1f} chunks/sec)')


if __name__ == '__main__':
    main()