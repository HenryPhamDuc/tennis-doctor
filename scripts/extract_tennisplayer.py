#!/usr/bin/env python3
"""
Tennis Doctor - tennisplayer.net Extractor
============================================

Extracts text from the tennisplayer.net archive at H:\\Play Tennis\\tennisplayer.net:
- HTML files (3,185): bulletin/, public/, root
- DOCX files (649): Fundamentals/, Stroke Analysis/, More/, New Issue/

Source attribution:
- Site: tennisplayer.net (Nick Wheatley's tennis instruction site)
- Section derived from folder structure
- Author extracted from meta tags or docx body when available

Skips:
- Office lock files (~$*)
- .tmp files
- .DS_Store, Thumbs.db
- Non-content files

Usage:
    python scripts/extract_tennisplayer.py [--src PATH] [--out PATH] [--manifest PATH]
                                          [--limit N] [--max-chars N] [--min-chars N]
"""

import os
import sys
import json
import re
import argparse
import hashlib
from pathlib import Path
from datetime import datetime


def slugify(s):
    s = s.rsplit('.', 1)[0]
    s = re.sub(r'[^\w\s-]', '', s.lower())
    s = re.sub(r'[\s_-]+', '-', s).strip('-')
    return s or 'untitled'


def clean_title(t):
    """Clean up forum-style titles with extra whitespace and site name suffix."""
    if not t:
        return None
    t = re.sub(r'\s+', ' ', t).strip()
    # Strip site name suffix like "- TennisPlayer.net Forums"
    t = re.sub(r'\s*-\s*(TennisPlayer\.net|Tennis Player).*$',
               '', t, flags=re.I).strip()
    # Strip leading "Topic:" or "Re:" markers
    t = re.sub(r'^(Topic|Re|Fwd|FW):\s*', '', t, flags=re.I).strip()
    return t or None


def clean_text(t):
    """Clean extracted text: collapse whitespace, strip forum noise."""
    if not t:
        return ''
    # Remove tabs and multiple spaces (forum formatting)
    t = re.sub(r'[ \t]+', ' ', t)
    # Collapse multiple blank lines
    t = re.sub(r'\n\s*\n\s*\n+', '\n\n', t)
    return t.strip()


# Lines that are pure forum/nav chrome (case-insensitive exact match)
FORUM_CHROME_LINES = {
    'announcement', 'collapse', 'x', 'no announcement yet.',
    'posts', 'latest activity', 'search', 'page', 'of',
    'filter', 'time', 'all time', 'today', 'last week', 'last month',
    'show', 'all', 'discussions only', 'photos only', 'videos only',
    'links only', 'polls only', 'events only', 'filtered by:',
    'clear all', 'new posts', 'previous', 'next', 'template',
    'share', 'tweet', 'home', 'forums', 'messages', 'forum',
    'senior member', 'join date:', 'member', 'logged out',
    'home page', 'logout', 'login', 'main site', 'automatically',
    'logged into', 'forums again.', 'comment', 'post', 'cancel',
    'tags:', 'none', 'tags',
}

# User handle pattern: lowercase alphanum + underscores, typically 5-25 chars
# (English words can be short, real usernames are usually longer or have digits)
USER_HANDLE_RE = re.compile(r'^[a-z][a-z0-9_]{4,24}$', re.I)

# Date patterns to skip
DATE_RE = re.compile(r'^(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+\d{4}$', re.I)


def strip_forum_chrome(text):
    """Remove per-line forum chrome, keep only meaningful lines."""
    lines = text.split('\n')
    cleaned = []
    for line in lines:
        s = line.strip()
        if not s:
            cleaned.append('')
            continue
        # Skip pure chrome lines
        if s.lower() in FORUM_CHROME_LINES:
            continue
        # Skip pure user handles (forum usernames are lowercase alphanum)
        if USER_HANDLE_RE.match(s):
            continue
        # Skip "Jan 2020" type dates
        if DATE_RE.match(s):
            continue
        # Skip "Posts: ..." type lines (number may be on a separate line)
        if re.match(r'^Posts:', s, re.I):
            continue
        # Skip just digits
        if re.match(r'^\d{1,5}$', s):
            continue
        # Skip "Join Date: ..." lines
        if re.match(r'^Join Date:', s, re.I):
            continue
        # Skip "#1" "#2" post numbers
        if re.match(r'^#\d+$', s):
            continue
        # Skip standalone "1" (post counter)
        if re.match(r'^\d{1,3}$', s):
            continue
        # Skip "N like(s)" lines
        if re.match(r'^\d+\s+likes?$', s, re.I):
            continue
        # Skip timestamp lines
        if re.match(r'^\d{1,2}-\d{1,2}-\d{4}', s):
            continue
        # Skip lone emoji / star ratings
        if re.match(r'^[★☆]+$', s):
            continue
        cleaned.append(s)
    # Collapse multiple blank lines
    text = '\n'.join(cleaned)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def extract_html_text(path):
    """Extract main text content from HTML file. Strips nav/scripts/styles."""
    try:
        from bs4 import BeautifulSoup
        with open(path, encoding='utf-8', errors='replace') as f:
            html = f.read()
        soup = BeautifulSoup(html, 'html.parser')
        # Remove nav/scripts/styles and common forum noise
        for tag in soup(['script', 'style', 'nav', 'header', 'footer',
                         'aside', 'noscript', 'iframe']):
            tag.decompose()
        # Remove common forum chrome
        for sel in ['.navbar', '.menu', '.sidebar', '.breadcrumb',
                    '.pagination', '.share', '.social', '.comments',
                    '.advertisement', '.ads', '.signature', '.quote',
                    '[id*=banner]', '[class*=banner]']:
            try:
                for el in soup.select(sel):
                    el.decompose()
            except Exception:
                pass

        # Try to find article/main/post content first
        article = (soup.find('article')
                   or soup.find('main')
                   or soup.find('div', class_=re.compile(r'post|article|content|entry', re.I))
                   or soup.find('div', id=re.compile(r'post|article|content|entry', re.I)))
        target = article or soup.body or soup

        # Get meta description and author
        title = None
        meta_desc = None
        meta_author = None
        # 1. Prefer og:title
        og_title = soup.find('meta', property='og:title')
        if og_title and og_title.get('content'):
            title = og_title['content']
        # 2. Try <title> tag
        if not title:
            title_tag = soup.find('title')
            if title_tag:
                title = title_tag.get_text()
        # 3. Try h1 — pick the one with class "main-title" or the 2nd h1
        # (first is often the site "Announcement" header)
        if not title or len(title.strip()) < 3:
            h1s = soup.find_all('h1')
            for h1 in h1s:
                cls = ' '.join(h1.get('class', []))
                t = h1.get_text(strip=True)
                if t and 'main-title' in cls:
                    title = t
                    break
            # Fallback: take the longest h1
            if not title and h1s:
                title = max((h.get_text(strip=True) for h in h1s
                             if h.get_text(strip=True)),
                            key=len, default='')
        for m in soup.find_all('meta'):
            n = (m.get('name', '') or m.get('property', '')).lower()
            c = m.get('content', '').strip()
            if n in ('description', 'og:description') and c:
                meta_desc = c
            elif n in ('author', 'article:author') and c:
                meta_author = c

        # Extract text
        text = target.get_text(separator='\n', strip=True)
        text = clean_text(text)
        text = strip_forum_chrome(text)

        return {
            'title': clean_title(title) or slugify(path.stem),
            'description': meta_desc,
            'author': meta_author,
            'text': text,
        }
    except Exception as e:
        return {'error': str(e)}


def extract_docx_text(path):
    """Extract text from DOCX file."""
    try:
        from docx import Document
        doc = Document(str(path))
        title = None
        author = None
        text_lines = []
        for i, p in enumerate(doc.paragraphs):
            t = p.text.strip()
            if not t:
                continue
            if i == 0 and not title:
                title = t
            elif i == 1 and not author and len(t) < 80 and '\n' not in t:
                author = t
            text_lines.append(t)
        text = clean_text('\n\n'.join(text_lines))
        return {
            'title': clean_title(title) or slugify(path.stem),
            'author': author,
            'text': text,
        }
    except Exception as e:
        return {'error': str(e)}


def chunk_text(text, max_chars=1000, min_chars=200):
    """Chunk text by paragraphs. Returns list of chunk strings."""
    chunks = []
    current = ''
    for para in re.split(r'\n\s*\n', text):
        para = para.strip()
        if not para:
            continue
        if len(current) + len(para) + 2 > max_chars and current:
            if len(current) >= min_chars:
                chunks.append(current.strip())
            current = ''
        current += '\n\n' + para
    if current and len(current.strip()) >= min_chars:
        chunks.append(current.strip())
    return chunks


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--src', default=r'H:\Play Tennis\tennisplayer.net',
                        help='tennisplayer.net root directory')
    parser.add_argument('--out', default='docs-source',
                        help='Output directory (will contain tennisplayer/ subdir)')
    parser.add_argument('--manifest', default='docs-source/_manifest.json',
                        help='Manifest file to APPEND to (existing manifest preserved)')
    parser.add_argument('--max-chars', type=int, default=1000)
    parser.add_argument('--min-chars', type=int, default=200)
    parser.add_argument('--limit', type=int, default=0,
                        help='Limit number of files (0=all)')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--verbose', '-v', action='store_true')
    args = parser.parse_args()

    src = Path(args.src)
    if not src.exists():
        print(f'ERROR: source not found: {src}', file=sys.stderr)
        sys.exit(1)

    out_dir = Path(args.out) / 'tennisplayer'
    out_dir.mkdir(parents=True, exist_ok=True)

    # Discover files
    files = []
    for f in src.rglob('*'):
        if not f.is_file():
            continue
        name = f.name
        # Skip Office lock files, temp files
        if name.startswith('~$') or name.endswith('.tmp'):
            continue
        if name in ('.DS_Store', 'Thumbs.db', 'sync.ffs_db'):
            continue
        ext = f.suffix.lower()
        if ext in ('.html', '.htm', '.docx'):
            files.append(f)

    files.sort()
    if args.limit:
        files = files[:args.limit]

    print(f'Found {len(files)} tennisplayer.net text files')
    if args.dry_run:
        print('DRY RUN - first 5:')
        for f in files[:5]:
            print(f'  - {f.relative_to(src)}')
        return

    # Load existing manifest if present
    manifest_path = Path(args.manifest)
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        existing_ids = {c['id'] for c in manifest.get('chunks', [])}
        print(f'Existing manifest: {manifest["total_chunks"]} chunks, {len(existing_ids)} unique IDs')
    else:
        existing_ids = set()
        manifest = {
            'generated': datetime.now().isoformat(),
            'total_files': 0,
            'translated': 0,
            'passthrough': 0,
            'total_chunks': 0,
            'chunks': [],
        }

    new_chunks = []
    file_stats = []
    skipped = 0
    errors = 0
    start = datetime.now()

    for idx, f in enumerate(files):
        rel = f.relative_to(src)
        # Section: first folder under src (e.g., "Fundamentals", "bulletin", "Stroke Analysis")
        parts = rel.parts
        section = parts[0] if len(parts) > 1 else 'root'
        # Sub-section: second folder if exists
        sub_section = parts[1] if len(parts) > 2 else None
        # Title slug
        title_slug = slugify(f.stem)

        # Extract based on extension
        if f.suffix.lower() in ('.html', '.htm'):
            result = extract_html_text(f)
        else:
            result = extract_docx_text(f)

        if 'error' in result:
            errors += 1
            if args.verbose:
                print(f'  ! {rel}: {result["error"]}', file=sys.stderr)
            continue

        text = result.get('text', '').strip()
        if len(text) < args.min_chars:
            skipped += 1
            if args.verbose:
                print(f'  - skip {rel} ({len(text)} chars, too short)', file=sys.stderr)
            continue

        # Chunk
        chunks = chunk_text(text, max_chars=args.max_chars, min_chars=args.min_chars)
        if not chunks:
            skipped += 1
            continue

        # Build metadata
        title_display = result.get('title') or title_slug
        author = result.get('author')
        description = result.get('description')

        for i, chunk_text_val in enumerate(chunks):
            chunk_id = f'tennisplayer/{section}/{title_slug}-chunk-{i}'
            if chunk_id in existing_ids:
                continue
            new_chunks.append({
                'id': chunk_id,
                'title': title_display,
                'slug': title_slug,
                'section': 'tennisplayer',  # use a single section for retrieval
                'lang': 'en',
                'source_type': 'tennisplayer_net',
                'source_path': str(rel).replace('\\', '/'),
                'source_section': section,
                'source_sub_section': sub_section,
                'author': author or 'tennisplayer.net (Nick Wheatley archive)',
                'description': description,
                'chunk_index': i,
                'heading': f'{title_display} (Part {i+1})',
                'text': chunk_text_val,
            })

        file_stats.append({
            'path': str(rel).replace('\\', '/'),
            'section': section,
            'sub_section': sub_section,
            'title': title_display,
            'author': author,
            'chunks': len(chunks),
            'chars': len(text),
        })

        if args.verbose and (idx + 1) % 50 == 0:
            elapsed = (datetime.now() - start).total_seconds()
            rate = (idx + 1) / max(elapsed, 0.1)
            print(f'  [{idx+1}/{len(files)}] {rate:.1f} files/s, '
                  f'{len(new_chunks)} new chunks', file=sys.stderr)

    # Write out per-chunk markdown files (for inspection)
    for chunk in new_chunks:
        chunk_dir = out_dir / chunk['source_section']
        chunk_dir.mkdir(parents=True, exist_ok=True)
        chunk_path = chunk_dir / f"{chunk['slug']}-chunk-{chunk['chunk_index']}.md"
        frontmatter = (
            f'---\n'
            f'title: "{chunk["title"]}"\n'
            f'source: tennisplayer.net\n'
            f'source_path: {chunk["source_path"]}\n'
            f'section: {chunk["source_section"]}\n'
            f'sub_section: {chunk.get("source_sub_section", "")}\n'
            f'author: "{chunk["author"]}"\n'
            f'chunk_index: {chunk["chunk_index"]}\n'
            f'---\n\n'
        )
        chunk_path.write_text(frontmatter + chunk['text'], encoding='utf-8')

    # Update manifest
    manifest['chunks'].extend(new_chunks)
    manifest['total_chunks'] = len(manifest['chunks'])
    manifest['generated'] = datetime.now().isoformat()
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2),
                            encoding='utf-8')

    # Save file stats for review
    stats_path = Path(args.out) / 'tennisplayer-stats.json'
    stats_path.write_text(json.dumps({
        'extracted': len(file_stats),
        'skipped': skipped,
        'errors': errors,
        'new_chunks': len(new_chunks),
        'by_section': {s: sum(c['chunks'] for c in file_stats
                              if c['section'] == s)
                       for s in set(c['section'] for c in file_stats)},
        'files': file_stats,
    }, ensure_ascii=False, indent=2), encoding='utf-8')

    elapsed = (datetime.now() - start).total_seconds()
    print(f'\n=== Extraction complete ===')
    print(f'  Files processed: {len(file_stats)} / {len(files)}')
    print(f'  Skipped (too short): {skipped}')
    print(f'  Errors: {errors}')
    print(f'  New chunks: {len(new_chunks)}')
    print(f'  Manifest total: {manifest["total_chunks"]}')
    print(f'  Time: {elapsed:.1f}s')
    print(f'  Stats: {stats_path}')


if __name__ == '__main__':
    main()
