#!/usr/bin/env python3
"""
Tennis Doctor - Hybrid Embedding Pipeline
==========================================

Embeds chunks locally via Ollama bge-m3 (no Cloudflare neuron limit)
then upserts pre-computed vectors to Cloudflare Vectorize via REST API
(storage operation, no neuron inference cost).

Why this exists:
- Cloudflare Workers AI Free plan: 10,000 neurons/day — only ~10 bge-m3 embeddings
- Ollama local: unlimited, no daily limit
- Vectorize storage: 5M free dims (separate billing from AI inference)

Usage:
    python scripts/embed_ollama_upsert_cf.py [--manifest PATH] [--limit N]
                                          [--start-from N] [--batch-size N]
                                          [--ollama-url URL] [--model NAME]
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
        print('ERROR: Set CF_ACCOUNT_ID and CF_API_TOKEN env vars', file=sys.stderr)
        sys.exit(1)
    return account_id, api_token


def embed_ollama(texts, ollama_url='http://localhost:11434', model='bge-m3'):
    """Embed a batch of texts via Ollama. Returns list of 1024-dim vectors."""
    vectors = []
    for text in texts:
        payload = json.dumps({'model': model, 'prompt': text}).encode('utf-8')
        req = Request(f'{ollama_url}/api/embeddings', data=payload,
                      headers={'Content-Type': 'application/json'})
        try:
            with urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                vectors.append(data['embedding'])
        except HTTPError as e:
            body = e.read().decode('utf-8')[:200]
            raise RuntimeError(f'Ollama HTTP {e.code}: {body}')
        except Exception as e:
            raise RuntimeError(f'Ollama error: {e}')
    return vectors


def vectorize_upsert(vectors, account_id, api_token,
                     index_name='tennis-doctor-embeddings'):
    """Upsert pre-computed vectors to Cloudflare Vectorize."""
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
        body = e.read().decode('utf-8')[:500]
        raise RuntimeError(f'HTTP {e.code}: {body}')


def vectorize_index_info(account_id, api_token,
                        index_name='tennis-doctor-embeddings'):
    url = f'https://api.cloudflare.com/client/v4/accounts/{account_id}/vectorize/v2/indexes/{index_name}/info'
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
    parser.add_argument('--ollama-url', default='http://localhost:11434')
    parser.add_argument('--ollama-model', default='bge-m3')
    parser.add_argument('--batch-size', type=int, default=10,
                        help='Ollama batch size (1=safest, 10=balanced)')
    parser.add_argument('--upsert-batch', type=int, default=100)
    parser.add_argument('--limit', type=int, default=0)
    parser.add_argument('--start-from', type=int, default=0)
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
    print(f'Manifest: {len(chunks)} chunks to embed (start={args.start_from})')

    if args.dry_run:
        print('DRY RUN - first 3:')
        for c in chunks[:3]:
            print(f"  - {c['title'][:50]} ({c['section']}#{c['chunk_index']})")
        return

    account_id, api_token = get_creds()

    # Show current Vectorize status
    info = vectorize_index_info(account_id, api_token)
    if info and info.get('success'):
        result = info.get('result', {})
        print(f"Vectorize index: vectors={result.get('vectorCount', '?')}, "
              f"processedUpToDatetime={result.get('processedUpToDatetime', '?')}")

    total = len(chunks)
    embedded = 0
    upserted = 0
    pending_vectors = []

    print(f'\nEmbedding {total} chunks via Ollama {args.ollama_model}...')
    print(f'  Ollama URL: {args.ollama_url}')
    print(f'  Batch size: {args.batch_size} chunks per request')
    start_time = time.time()

    for batch_start in range(0, total, args.batch_size):
        batch_end = min(batch_start + args.batch_size, total)
        batch = chunks[batch_start:batch_end]
        texts = [c['text'][:1500] for c in batch]  # cap input

        try:
            vectors = embed_ollama(texts, args.ollama_url, args.ollama_model)
        except Exception as e:
            print(f'  ! batch {batch_start} error: {e}', file=sys.stderr)
            continue

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
            print(f'  [{embedded}/{total}] {rate:.2f}/s, ETA: {eta:.0f}s',
                  file=sys.stderr)

        # Flush to Vectorize
        if len(pending_vectors) >= args.upsert_batch:
            try:
                vectorize_upsert(pending_vectors, account_id, api_token)
                upserted += len(pending_vectors)
                if args.verbose:
                    print(f'  ↑ Upserted {len(pending_vectors)} (total: {upserted})',
                          file=sys.stderr)
            except Exception as e:
                print(f'  ! Upsert error: {e}', file=sys.stderr)
            pending_vectors = []

    # Flush remainder
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
    print(f'  Time: {elapsed:.1f}s ({embedded / max(elapsed, 0.1):.2f} chunks/sec)')


if __name__ == '__main__':
    main()
