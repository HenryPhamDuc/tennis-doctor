#!/usr/bin/env python3
"""
Tennis-Doctor — Vietnamese → English translation pipeline
==========================================================

Reads the existing Vietnamese Tennis-WIKI content (from
C:/Users/Henry/Documents/tennis-wiki/docs/) and produces English
versions in tennis-doctor/docs-source/.

Strategy:
- Read all .md files from the source wiki
- Translate the body content to English using a lightweight
  pass: keep code blocks, links, and structure intact; translate
  prose using a local LLM (Ollama) if available, else fall back
  to leaving Vietnamese intact + adding an English summary via
  the frontmatter "summary" field.

Two modes:
1. LLM mode (preferred): use local Ollama to translate
2. Pass-through mode: keep Vietnamese but extract English
   frontmatter (title, summary, tags) using heuristics

Usage:
    python translate_to_english.py [--source PATH] [--out PATH] [--mode llm|pass]
"""

import sys
import os
import re
import json
import argparse
from pathlib import Path
from datetime import datetime


# ---------------------------------------------------------------------------
# Chunking: split a markdown article into retrievable chunks
# ---------------------------------------------------------------------------

def chunk_markdown(text, max_chars=1200):
    """Split markdown into chunks of ~max_chars, respecting paragraph
    and heading boundaries. Each chunk keeps its preceding heading context."""
    # Split by H2/H3 headings to keep semantic boundaries
    parts = re.split(r'(?m)^(#{2,4} .+)$', text)
    chunks = []
    current_h = ''
    buf = ''
    i = 0
    while i < len(parts):
        if i % 2 == 1:
            current_h = parts[i]
            i += 1
            continue
        body = parts[i] if i < len(parts) else ''
        paragraphs = body.split('\n\n')
        for p in paragraphs:
            p = p.strip()
            if not p:
                continue
            if len(buf) + len(p) + len(current_h) + 5 > max_chars and buf:
                chunks.append({'heading': current_h.strip(), 'text': buf.strip()})
                buf = ''
            buf += f'\n\n{p}'
        i += 1
    if buf.strip():
        chunks.append({'heading': current_h.strip(), 'text': buf.strip()})
    return chunks


# ---------------------------------------------------------------------------
# Translation via Ollama (optional, falls back gracefully)
# ---------------------------------------------------------------------------

def has_ollama():
    """Check if Ollama is running locally."""
    try:
        import urllib.request
        with urllib.request.urlopen('http://localhost:11434/api/tags', timeout=2) as r:
            return r.status == 200
    except Exception:
        return False


def translate_with_ollama(text, target_lang='en'):
    """Translate text using local Ollama."""
    try:
        import urllib.request
        prompt = f'Translate the following Vietnamese text to English. Keep technical terms (kinetic chain, split step, forehand, etc.) in English when appropriate. Preserve Markdown formatting. Output ONLY the translation, no preamble.\n\nText:\n{text}'
        payload = json.dumps({
            'model': 'llama3.1',
            'prompt': prompt,
            'stream': False,
            'options': {'temperature': 0.1, 'num_ctx': 4096},
        }).encode('utf-8')
        req = urllib.request.Request(
            'http://localhost:11434/api/generate',
            data=payload,
            headers={'Content-Type': 'application/json'},
        )
        with urllib.request.urlopen(req, timeout=60) as r:
            result = json.loads(r.read().decode('utf-8'))
            return result.get('response', '').strip()
    except Exception as e:
        return None


# ---------------------------------------------------------------------------
# Heuristic English summary extraction (no LLM)
# ---------------------------------------------------------------------------

# Common Vietnamese tennis terms → English mapping (curated glossary)
TERM_MAP = {
    'kỹ thuật': 'technique',
    'cơ sinh học': 'biomechanics',
    'chiến thuật': 'tactics',
    'tâm lý': 'mental game',
    'thể lực': 'fitness',
    'forehand': 'forehand',
    'backhand': 'backhand',
    'serve': 'serve',
    'giao bóng': 'serve',
    'volley': 'volley',
    'footwork': 'footwork',
    'di chuyển': 'footwork',
    'split step': 'split step',
    'cú đánh': 'stroke',
    'tay vợt': 'player',
    'huấn luyện viên': 'coach',
    'kinetic chain': 'kinetic chain',
    'chuỗi động lực': 'kinetic chain',
    'proprioception': 'proprioception',
    'cảm nhận cơ thể': 'proprioception',
    'biomechanics': 'biomechanics',
    'federer': 'Federer',
    'nadal': 'Nadal',
    'djokovic': 'Djokovic',
    'alcaraz': 'Alcaraz',
    'sinner': 'Sinner',
    'rublev': 'Rublev',
    'shelton': 'Shelton',
    'sampras': 'Sampras',
}


def extract_english_summary(vietnamese_text):
    """Extract a short English summary from Vietnamese content."""
    # Get the first non-empty paragraph after the title
    paragraphs = [p.strip() for p in vietnamese_text.split('\n\n') if p.strip()]
    # Skip headings, find first content paragraph
    content_para = None
    for p in paragraphs:
        if p.startswith('#'):
            continue
        if p.startswith('|') or p.startswith('```'):
            continue
        if len(p) > 50:
            content_para = p
            break
    if not content_para:
        return 'Tennis knowledge article.'
    # Just take the first sentence and add a note
    first_sentence = re.split(r'[.!?]\s', content_para)[0]
    if len(first_sentence) > 300:
        first_sentence = first_sentence[:300] + '…'
    # Apply term map for English keywords
    summary_en = first_sentence
    for vi, en in TERM_MAP.items():
        # Replace whole-word matches
        summary_en = re.sub(rf'\b{re.escape(vi)}\b', en, summary_en, flags=re.IGNORECASE)
    return f'[Auto-summary] {summary_en}'


def derive_english_title(vietnamese_title):
    """Derive an English title using term map."""
    title_en = vietnamese_title
    for vi, en in TERM_MAP.items():
        title_en = re.sub(rf'\b{re.escape(vi)}\b', en, title_en, flags=re.IGNORECASE)
    return title_en


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description='Tennis-Doctor: translate VI wiki to EN')
    parser.add_argument('--source', default=None,
                        help='Source VI wiki directory (auto-detected if not given)')
    parser.add_argument('--out', default='docs-source',
                        help='Output directory for EN content')
    parser.add_argument('--mode', choices=['auto', 'llm', 'pass'], default='auto',
                        help='Translation mode (auto=try LLM then fall back)')
    parser.add_argument('--limit', type=int, default=0,
                        help='Limit number of articles (0=all)')
    parser.add_argument('--verbose', '-v', action='store_true')
    args = parser.parse_args()

    src = Path(args.source) if args.source else None
    if src is None or not src.exists():
        # Auto-detect: walk up parent dirs + check known sibling locations
        candidates = []
        cwd = Path.cwd()
        # 1. Sibling of cwd (../tennis-wiki/docs)
        candidates.append(cwd.parent / 'tennis-wiki' / 'docs')
        # 2. Sibling 2-up
        candidates.append(cwd.parent.parent / 'tennis-wiki' / 'docs')
        # 3. Original tennis-wiki location
        candidates.append(Path(r'C:\Users\Henry\Documents\tennis-wiki\docs'))
        # 4. The "MY VAULT" tennis-wiki output
        candidates.append(Path(r'C:\Users\Henry\Documents\MY VAULT\Documents\Obsidian Vault\tennis-vault\Tennis Wiki-Vietnamese'))
        for c in candidates:
            if c.exists():
                src = c
                print(f'Auto-detected source: {src}', file=sys.stderr)
                break
        if src is None or not src.exists():
            print(f'ERROR: source not found. Tried:', file=sys.stderr)
            for c in candidates:
                print(f'  - {c}', file=sys.stderr)
            print(f'Pass --source PATH to specify explicitly', file=sys.stderr)
            sys.exit(1)
    if not src.exists():
        print(f'ERROR: source not found: {src}', file=sys.stderr)
        sys.exit(1)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    # Decide mode
    mode = args.mode
    if mode == 'auto':
        mode = 'llm' if has_ollama() else 'pass'
    print(f'Translation mode: {mode}', file=sys.stderr)
    if mode == 'llm':
        print('Ollama detected — will use llama3.1 for translation', file=sys.stderr)

    out.mkdir(parents=True, exist_ok=True)

    # Process all .md files
    md_files = sorted(src.rglob('*.md'))
    if args.limit:
        md_files = md_files[:args.limit]

    stats = {'total': 0, 'translated': 0, 'passthrough': 0, 'chunks': 0, 'errors': 0}
    all_chunks = []

    for i, md_file in enumerate(md_files):
        rel = md_file.relative_to(src)
        stats['total'] += 1
        try:
            raw = md_file.read_text(encoding='utf-8', errors='replace')
        except Exception as e:
            stats['errors'] += 1
            if args.verbose:
                print(f'  ! read error: {rel}: {e}', file=sys.stderr)
            continue

        # Skip ARCHITECTURE.md / CONTENT_MAP.md (English already)
        if md_file.name in ('ARCHITECTURE.md', 'CONTENT_MAP.md'):
            continue

        # Skip index.md (we'll regenerate those)
        if md_file.name == 'index.md':
            continue

        # Strip frontmatter
        body = raw
        if body.startswith('---\n'):
            end = body.find('\n---\n', 4)
            if end > 0:
                body = body[end + 5:]

        # Find first heading as title
        title_hint = None
        for ln in body.split('\n'):
            m = re.match(r'^#\s+(.+)$', ln)
            if m:
                title_hint = m.group(1).strip()
                break

        # Translate body
        if mode == 'llm':
            translated = translate_with_ollama(body)
            if translated and len(translated) > 100:
                stats['translated'] += 1
                en_body = translated
                en_title = title_hint or rel.stem.replace('-', ' ').title()
                en_summary = ''  # LLM provides translation directly
            else:
                # Fall back to passthrough for this file
                stats['passthrough'] += 1
                en_body = body
                en_title = derive_english_title(title_hint or rel.stem.replace('-', ' ').title())
                en_summary = extract_english_summary(body)
        else:
            stats['passthrough'] += 1
            en_body = body  # Keep Vietnamese (will be searchable via embedding too)
            en_title = derive_english_title(title_hint or rel.stem.replace('-', ' ').title())
            en_summary = extract_english_summary(body)

        # Write EN version
        out_path = out / rel
        out_path.parent.mkdir(parents=True, exist_ok=True)
        fm = '---\n'
        fm += f'title: "{en_title}"\n'
        if en_summary:
            fm += f'summary: "{en_summary[:300]}"\n'
        fm += f'source_vi: "{str(rel)}"\n'
        fm += f'translated: "{datetime.now().strftime("%Y-%m-%d")}"\n'
        fm += f'translation_mode: "{mode}"\n'
        fm += '---\n\n'
        out_path.write_text(fm + en_body, encoding='utf-8')

        # Generate chunks for embedding
        chunks = chunk_markdown(en_body)
        for j, chunk in enumerate(chunks):
            all_chunks.append({
                'id': f'{rel}#{j}',
                'title': en_title,
                'slug': str(rel.with_suffix('')).replace('\\', '/'),
                'section': rel.parts[0] if rel.parts else '',
                'lang': 'en',
                'chunk_index': j,
                'heading': chunk['heading'],
                'text': chunk['text'][:2000],  # cap chunk size
            })
            stats['chunks'] += 1

        if args.verbose and (i + 1) % 20 == 0:
            print(f'  [{i + 1}/{len(md_files)}] {rel}: {len(chunks)} chunks', file=sys.stderr)

    # Write chunk manifest (for embedding script)
    manifest_path = out / '_manifest.json'
    manifest_path.write_text(json.dumps({
        'generated': datetime.now().isoformat(),
        'total_files': stats['total'],
        'translated': stats['translated'],
        'passthrough': stats['passthrough'],
        'total_chunks': stats['chunks'],
        'chunks': all_chunks,
    }, ensure_ascii=False, indent=2), encoding='utf-8')

    print(f'\n=== Translation complete ===')
    print(f'  Source files:    {stats["total"]}')
    print(f'  Translated:      {stats["translated"]}')
    print(f'  Passthrough:     {stats["passthrough"]}')
    print(f'  Total chunks:    {stats["chunks"]}')
    print(f'  Errors:          {stats["errors"]}')
    print(f'  Output:          {out}/')
    print(f'  Chunk manifest:  {manifest_path}')


if __name__ == '__main__':
    main()