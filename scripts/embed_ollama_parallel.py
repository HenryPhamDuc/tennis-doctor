#!/usr/bin/env python3
"""
Tennis Doctor - Parallel Hybrid Embedding Pipeline
===================================================

Embeds chunks locally via Ollama bge-m3 in PARALLEL (multi-threaded),
then upserts pre-computed vectors to Cloudflare Vectorize.

Why parallel:
- Single Ollama request ~3s per chunk (sequential)
- Ollama uses CPU but can handle concurrent requests
- 4-8 concurrent requests gives 3-5x speedup on multi-core systems
"""

import os
import sys
import json
import time
import argparse
import hashlib
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
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


def embed_one(text, ollama_url, model):
    """Embed a single text via Ollama."""
    payload = json.dumps({'model': model, 'prompt': text}).encode('utf-8')
    req = Request(f'{ollama_url}/api/embeddings', data=payload,
                  headers={'Content-Type': 'application/json'})
    try:
        with urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            return data['embedding']
    except HTTPError as e:
        body = e.read().decode('utf-8')[:200]
        raise RuntimeError(f'Ollama HTTP {e.code}: {body}')
    except Exception as e:
        raise RuntimeError(f'Ollama error: {e}')


def vectorize_upsert(vectors, account_id, api_token,
                     index_name='tennis-doctor-embeddings'):
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
    parser.add_argument('--workers', type=int, default=4,
                        help='Parallel Ollama workers (4-8 typical)')
    parser.add_argument('--upsert-batch', type=int, default=100)
    parser.add_argument('--limit', type=int, default=0)
    parser.add_argument('--start-from', type=int, default=0)
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--verbose', '-v', action='store_true')
    parser.add_argument('--log-file', default='embedding_run.log',
                        help='Log progress to this file')
    parser.add_argument('--only-sections', default='books,tennisplayer',
                        help='Comma-separated section names to embed (default: books,tennisplayer). '
                             'Use "*" for all sections.')
    args = parser.parse_args()

    # Open log file for progress output
    log_fh = open(args.log_file, 'a', encoding='utf-8')
    def log(msg):
        ts = time.strftime('%H:%M:%S')
        line = f'[{ts}] {msg}'
        print(line, flush=True)
        log_fh.write(line + '\n')
        log_fh.flush()

    load_env()

    manifest_path = Path(args.manifest)
    if not manifest_path.exists():
        print(f'ERROR: {manifest_path} not found', file=sys.stderr)
        sys.exit(1)

    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    chunks = manifest['chunks']
    if args.only_sections != '*':
        keep = set(s.strip() for s in args.only_sections.split(','))
        before = len(chunks)
        chunks = [c for c in chunks if c.get('section') in keep]
        log(f'Section filter: kept {len(chunks)}/{before} chunks '
            f'(sections: {sorted(keep)})')
    if args.start_from:
        chunks = chunks[args.start_from:]
    if args.limit:
        chunks = chunks[:args.limit]
    log(f'Manifest: {len(chunks)} chunks to embed (start={args.start_from})')

    if args.dry_run:
        log('DRY RUN - first 3:')
        for c in chunks[:3]:
            log(f"  - {c['title'][:50]} ({c['section']}#{c['chunk_index']})")
        return

    account_id, api_token = get_creds()

    info = vectorize_index_info(account_id, api_token)
    if info and info.get('success'):
        result = info.get('result', {})
        log(f"Vectorize: vectors={result.get('vectorCount', '?')}")

    total = len(chunks)
    embedded = 0
    upserted = 0
    pending_vectors = []
    errors = 0

    log(f'Embedding {total} chunks via Ollama {args.ollama_model} '
        f'({args.workers} workers)...')
    start_time = time.time()

    # Build list of (index, chunk, text)
    work = [(i, c, c['text'][:1500]) for i, c in enumerate(chunks)]

    def process_one(item):
        i, chunk, text = item
        try:
            v = embed_one(text, args.ollama_url, args.ollama_model)
            return (i, chunk, v, None)
        except Exception as e:
            return (i, chunk, None, str(e))

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(process_one, w): w for w in work}
        done_count = 0
        for future in as_completed(futures):
            i, chunk, v, err = future.result()
            done_count += 1
            if err:
                errors += 1
                if args.verbose:
                    print(f'  ! skip {chunk["id"][:60]}: {err}', file=sys.stderr)
                continue
            pending_vectors.append({
                'id': deterministic_id(chunk['id']),
                'values': v,
                'metadata': {
                    'title': chunk['title'][:200],
                    'slug': chunk['slug'][:200],
                    'section': chunk.get('section', '')[:100],
                    'lang': chunk.get('lang', 'en'),
                    'text': chunk['text'][:2000],
                    'heading': chunk.get('heading', '')[:200],
                    'source_id': chunk['id'][:200],
                },
            })
            embedded += 1

            if args.verbose and done_count % 50 == 0:
                elapsed = time.time() - start_time
                rate = embedded / max(elapsed, 0.1)
                eta = (total - embedded) / max(rate, 0.1)
                log(f'[{embedded}/{total}] {rate:.2f}/s, ETA: {eta:.0f}s '
                    f'(errors: {errors})')

            # Flush
            if len(pending_vectors) >= args.upsert_batch:
                try:
                    vectorize_upsert(pending_vectors, account_id, api_token)
                    upserted += len(pending_vectors)
                    log(f'↑ Upserted {len(pending_vectors)} '
                        f'(total: {upserted})')
                except Exception as e:
                    log(f'! Upsert error: {e}')
                pending_vectors = []

    # Flush remainder
    if pending_vectors:
        try:
            vectorize_upsert(pending_vectors, account_id, api_token)
            upserted += len(pending_vectors)
        except Exception as e:
            log(f'! Final upsert error: {e}')

    elapsed = time.time() - start_time
    log(f'=== Embedding complete ===')
    log(f'  Embedded: {embedded} / {total}')
    log(f'  Errors: {errors}')
    log(f'  Upserted: {upserted}')
    log(f'  Time: {elapsed:.1f}s '
        f'({embedded / max(elapsed, 0.1):.2f} chunks/sec)')
    log_fh.close()


if __name__ == '__main__':
    main()
