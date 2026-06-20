#!/usr/bin/env python3
"""
Tennis-Doctor — Embedding pipeline
==================================

Reads docs-source/_manifest.json (produced by translate_to_english.py),
embeds each chunk using Workers AI @cf/baai/bge-small-en-v1.5 (via the
Cloudflare REST API), and upserts to the Vectorize index.

Prereqs:
    - Cloudflare account ID
    - Cloudflare API token with Workers AI + Vectorize permissions
    - Vectorize index 'tennis-doctor-embeddings' already created
    - Metadata indexes already created (section, slug, lang)

Auth:
    Credentials are read from environment or a .env file. We avoid
    embedding them in any committed file.

Usage:
    python generate_embeddings.py [--manifest PATH] [--batch-size 100]

Env vars (read from .env or shell):
    CF_ACCOUNT_ID     - Cloudflare account ID
    CF_API_TOKEN      - Cloudflare API token with AI + Vectorize scopes
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError


def load_env():
    """Load .env file from script directory if present."""
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        for line in env_path.read_text(encoding='utf-8').splitlines():
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip())


def get_creds():
    """Get CF account ID and API token from env."""
    account_id = os.environ.get('CF_ACCOUNT_ID')
    api_token = os.environ.get('CF_API_TOKEN')
    if not account_id or not api_token:
        print('ERROR: Set CF_ACCOUNT_ID and CF_API_TOKEN env vars (or in .env)', file=sys.stderr)
        print('  See README.md for how to create these', file=sys.stderr)
        sys.exit(1)
    return account_id, api_token


def embed_batch(texts, account_id, api_token, model='@cf/baai/bge-m3'):
    """Embed a batch of texts via Workers AI REST API. Returns list of vectors.
    Uses bge-m3 (multilingual, 1024-dim) so Vietnamese + English both work."""
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
            # bge-m3 shape: { embedding: [...], embeddings: [[...]] } or { data: [[...]] }
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
            raise RuntimeError(f'Unexpected bge-m3 response shape: {list(result.keys()) if isinstance(result, dict) else type(result)}')
    except HTTPError as e:
        body = e.read().decode('utf-8')
        raise RuntimeError(f'HTTP {e.code}: {body}')


def vectorize_upsert(vectors, account_id, api_token, index_name='tennis-doctor-embeddings'):
    """Upsert a batch of vectors to a Vectorize index."""
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
    """Get info about a Vectorize index (count, etc)."""
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
    """Generate a deterministic vector ID from chunk_id (must be ASCII alphanumeric)."""
    import hashlib
    h = hashlib.md5(chunk_id.encode('utf-8')).hexdigest()
    return f'chunk_{h[:32]}'


def main():
    parser = argparse.ArgumentParser(description='Tennis-Doctor embedding pipeline')
    parser.add_argument('--manifest', default='docs-source/_manifest.json',
                        help='Path to manifest JSON')
    parser.add_argument('--batch-size', type=int, default=20,
                        help='Embed batch size (Workers AI limit is ~100)')
    parser.add_argument('--upsert-batch', type=int, default=100,
                        help='Vectorize upsert batch size (limit is 1000)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would happen without making API calls')
    parser.add_argument('--verbose', '-v', action='store_true')
    args = parser.parse_args()

    load_env()
    manifest_path = Path(args.manifest)
    if not manifest_path.exists():
        print(f'ERROR: manifest not found: {manifest_path}', file=sys.stderr)
        print('Run: python scripts/translate_to_english.py first', file=sys.stderr)
        sys.exit(1)

    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    chunks = manifest['chunks']
    print(f'Manifest: {manifest_path}')
    print(f'  Files: {manifest["total_files"]}')
    print(f'  Chunks: {manifest["total_chunks"]}')

    if args.dry_run:
        print('\nDRY RUN — would embed', len(chunks), 'chunks')
        print('Sample chunk:')
        sample = chunks[0] if chunks else None
        if sample:
            print(json.dumps(sample, indent=2, ensure_ascii=False)[:500])
        return

    account_id, api_token = get_creds()

    # Verify index exists
    info = vectorize_index_info(account_id, api_token)
    if not info or not info.get('success'):
        print(f'ERROR: Vectorize index not found.', file=sys.stderr)
        print('Run: npx wrangler vectorize create tennis-doctor-embeddings --dimensions 1024 --metric cosine', file=sys.stderr)
        print('Then create metadata indexes:', file=sys.stderr)
        print('  npx wrangler vectorize create-metadata-index tennis-doctor-embeddings --property-name section --type string', file=sys.stderr)
        print('  npx wrangler vectorize create-metadata-index tennis-doctor-embeddings --property-name slug --type string', file=sys.stderr)
        print('  npx wrangler vectorize create-metadata-index tennis-doctor-embeddings --property-name lang --type string', file=sys.stderr)
        sys.exit(1)
    print(f'  Vectorize index: OK ({info["result"].get("dimensions")} dims, {info["result"].get("vector_count", "?")} vectors)')

    # Process chunks in batches
    total = len(chunks)
    embedded = 0
    upserted = 0
    pending_vectors = []  # for batched upsert

    print(f'\nEmbedding {total} chunks...')
    start_time = time.time()

    for batch_start in range(0, total, args.batch_size):
        batch_end = min(batch_start + args.batch_size, total)
        batch = chunks[batch_start:batch_end]
        texts = [c['text'] for c in batch]

        try:
            vectors = embed_batch(texts, account_id, api_token)
        except Exception as e:
            print(f'  ! Embedding error at batch {batch_start}: {e}', file=sys.stderr)
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
                    print(f'    ! skip {c["id"]}: {e2}', file=sys.stderr)
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
            print(f'  [{embedded}/{total}] embedded (rate: {embedded / elapsed:.1f}/sec)', file=sys.stderr)

        # Flush to Vectorize every upsert-batch vectors
        if len(pending_vectors) >= args.upsert_batch:
            try:
                result = vectorize_upsert(pending_vectors, account_id, api_token)
                upserted += len(pending_vectors)
                mutation_ids = result.get('mutationId') or result.get('ids', [])
                if args.verbose:
                    print(f'  ↑ Upserted {len(pending_vectors)} (total: {upserted})', file=sys.stderr)
            except Exception as e:
                print(f'  ! Upsert error: {e}', file=sys.stderr)
            pending_vectors = []

        # Polite rate limit (Workers AI has free-tier limits)
        time.sleep(0.05)

    # Final flush
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
    print(f'  Time:     {elapsed:.1f}s ({embedded / elapsed:.1f} chunks/sec)')


if __name__ == '__main__':
    main()