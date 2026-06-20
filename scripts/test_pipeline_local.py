#!/usr/bin/env python3
"""
Tennis Doctor - Local Pipeline Test
====================================

Simulates the full RAG pipeline using local Ollama (bge-m3 embeddings + Llama 3.1),
bypassing Cloudflare. Useful for:
  - Development without a CF account
  - CI tests
  - Verifying the pipeline before production deploy

Steps:
  1. Load chunks from docs-source/_manifest.json
  2. Embed all chunks with local Ollama bge-m3
  3. Build a local numpy vector index
  4. On a test question: embed query -> top-K chunks -> format prompt -> query Llama 3.1
  5. Print the answer

This is NOT a replacement for the production deploy. It just lets us verify
that the retrieval + LLM chain works.
"""

import sys
import os
import json
import time
import urllib.request
from pathlib import Path

import numpy as np


# ---------- Ollama helpers ----------

def ollama_embed(text, model='bge-m3'):
    payload = json.dumps({'model': model, 'prompt': text}).encode('utf-8')
    req = urllib.request.Request(
        'http://localhost:11434/api/embeddings',
        data=payload,
        headers={'Content-Type': 'application/json'},
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())['embedding']


def ollama_generate(prompt, model='llama3.1', max_tokens=400):
    payload = json.dumps({
        'model': model,
        'prompt': prompt,
        'stream': False,
        'options': {'temperature': 0.5, 'num_ctx': 4096, 'num_predict': max_tokens},
    }).encode('utf-8')
    req = urllib.request.Request(
        'http://localhost:11434/api/generate',
        data=payload,
        headers={'Content-Type': 'application/json'},
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())['response']


# ---------- Pipeline ----------

def main():
    print('=' * 60)
    print(' Tennis Doctor - Local Pipeline Test')
    print('=' * 60)

    # 1. Load manifest
    manifest_path = Path('docs-source') / '_manifest.json'
    if not manifest_path.exists():
        print(f'ERROR: {manifest_path} not found. Run:')
        print('  python scripts/translate_to_english.py')
        sys.exit(1)
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    chunks = manifest['chunks']
    print(f'Loaded {len(chunks)} chunks from manifest')

    # 2. Embed all chunks (this is slow locally, use first 50 for the demo)
    sample_size = int(os.environ.get('TEST_CHUNKS', 50))
    test_chunks = chunks[:sample_size]
    print(f'Embedding first {len(test_chunks)} chunks via Ollama bge-m3...')
    start = time.time()
    vectors = []
    for i, c in enumerate(test_chunks):
        v = ollama_embed(c['text'][:1000])  # truncate for speed
        vectors.append(v)
        if (i + 1) % 10 == 0:
            elapsed = time.time() - start
            rate = (i + 1) / elapsed
            eta = (len(test_chunks) - i - 1) / rate if rate > 0 else 0
            print(f'  [{i + 1}/{len(test_chunks)}] {rate:.1f}/s, ETA: {eta:.0f}s')
    vectors = np.array(vectors, dtype=np.float32)
    elapsed = time.time() - start
    print(f'Embedded {len(vectors)} chunks in {elapsed:.1f}s ({len(vectors) / elapsed:.1f}/s)')

    # 3. Test query
    test_questions = [
        'What is the kinetic chain in tennis?',
        'How does Carlos Alcaraz generate power on his forehand?',
        'Explain the 70% rule',
    ]
    print()
    print('=' * 60)
    print(' Test Questions')
    print('=' * 60)

    for q in test_questions:
        print()
        print(f'Q: {q}')
        # Embed query
        qvec = np.array(ollama_embed(q), dtype=np.float32)

        # Cosine similarity
        # Normalize
        qnorm = qvec / (np.linalg.norm(qvec) + 1e-8)
        vnorm = vectors / (np.linalg.norm(vectors, axis=1, keepdims=True) + 1e-8)
        scores = vnorm @ qnorm

        # Top-5
        top_idx = np.argsort(scores)[::-1][:5]
        print('Top chunks:')
        for rank, idx in enumerate(top_idx):
            c = test_chunks[idx]
            print(f'  [{rank + 1}] score={scores[idx]:.3f}  {c["title"]} ({c["section"]})')
            print(f'      {c["text"][:150].strip()}...')

        # Build context
        context_parts = []
        for rank, idx in enumerate(top_idx[:3]):
            c = test_chunks[idx]
            context_parts.append(f'[{rank + 1}] {c["title"]} [{c["section"]}]\n{c["text"][:500]}')
        context = '\n\n---\n\n'.join(context_parts)

        # Build prompt
        system = (
            "You are Tennis Doctor, an expert tennis coach. "
            "Answer the question using ONLY the provided context. "
            "Cite sources as [1], [2], etc. "
            "Be concise (max 200 words). "
            "If context doesn't answer, say so."
        )
        prompt = f'{system}\n\nContext:\n{context}\n\nQuestion: {q}\n\nAnswer:'

        # Generate
        print('Generating answer (Llama 3.1)...')
        start = time.time()
        answer = ollama_generate(prompt, max_tokens=300)
        gen_time = time.time() - start
        print(f'A: {answer.strip()[:600]}')
        print(f'   (generated in {gen_time:.1f}s)')
        print('-' * 60)


if __name__ == '__main__':
    main()