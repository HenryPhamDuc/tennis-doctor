#!/usr/bin/env python3
"""
Tennis Doctor - PDF Book Extractor
===================================

Extracts text from the tennis books in C:\\Users\\Henry\\Documents\\MY VAULT\
Documents\\Tennis Knowledge\\Tennis books\\, chunks them, and adds them to
the manifest for embedding.

Strategy:
- Use pymupdf for fast text extraction
- Skip duplicate books (e.g. Advanced_tennis.pdf and Advanced_tennis(1).pdf)
- Skip narrative/historical books (focus on instructional content)
- Chunk into ~800-1200 char segments at paragraph boundaries
- Save chunks as Markdown files with frontmatter, similar to translate_to_english.py

Output:
- docs-source/books/<book-slug>/<book-slug>.md (full text)
- docs-source/books/<book-slug>/<book-slug>-chunk-NNN.md (per-chunk)
- Appends to docs-source/_manifest.json

Run:
    python scripts/extract_pdfs.py [--book-dir PATH] [--out PATH]
"""

import os
import sys
import json
import re
import argparse
import hashlib
from pathlib import Path
from datetime import datetime

# Books to SKIP (duplicates, narrative-only, or off-topic)
SKIP_BOOKS = {
    # Duplicates
    'Advanced_tennis(1).pdf',  # duplicate of Advanced_tennis.pdf
    'Tennis(1).pdf',
    'Tennis(2).pdf',
    'Winning_tennis(1).pdf',
    # Narrative/biography (not instructional)
    'Arthur_Ashe,_portrait_in_motion.pdf',
    'Advantage_Canada__a_tennis_centenary.pdf',
    'Roger_Federer__the_greatest.pdf',
    'Strokes_of_genius__Federer,_Nadal,_and_the_greatest_match_ever_played.pdf',
    'Tennis_confidential__today\'s_greatest_players,_matches,_and_controversies.pdf',
    'The_Art_of_Tennis_-_Nicholas_Fox_Weber.pdf',
    'Tennis_by_Machiavelli.pdf',  # fiction/satire
    'Bud_Collins\'_tennis_encyclopedia.pdf',  # reference encyclopedia, mostly stats
    # Non-PDF
    'recording.webm',
    'convert.py',
    # Cooking (mistakenly filed here)
    'Tempting_Tennis_Treats_to_Serve_at_your_US_-_Sharon_Powell.pdf',
    # Very old or very long (>300MB) — skip for speed
}


def slugify(s):
    """Make a safe slug from a filename."""
    s = s.rsplit('.', 1)[0]  # remove extension
    s = re.sub(r'[^\w\s-]', '', s.lower())
    s = re.sub(r'[\s_-]+', '-', s).strip('-')
    return s or 'untitled'


def extract_text_pymupdf(pdf_path):
    """Extract text from a PDF using pymupdf. Returns list of (page_num, text)."""
    try:
        import pymupdf
        doc = pymupdf.open(str(pdf_path))
        pages = []
        for i, page in enumerate(doc):
            text = page.get_text("text")
            if text and text.strip():
                pages.append((i + 1, text))
        doc.close()
        return pages
    except Exception as e:
        print(f'  ! pymupdf failed: {e}', file=sys.stderr)
        return None


def chunk_text(pages, max_chars=1000, min_chars=200):
    """Chunk text by paragraphs, respecting page boundaries.

    Returns list of dicts: {text, page_start, page_end, chunk_index}
    """
    chunks = []
    current_text = ''
    current_page_start = None
    current_page_end = None
    chunk_index = 0

    for page_num, page_text in pages:
        # Split into paragraphs
        paragraphs = re.split(r'\n\s*\n', page_text)
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            # If adding this paragraph would exceed max_chars, flush
            if len(current_text) + len(para) + 2 > max_chars and current_text:
                if len(current_text) >= min_chars:
                    chunks.append({
                        'text': current_text.strip(),
                        'page_start': current_page_start,
                        'page_end': current_page_end,
                        'chunk_index': chunk_index,
                    })
                    chunk_index += 1
                current_text = ''
                current_page_start = None
                current_page_end = None
            if not current_page_start:
                current_page_start = page_num
            current_page_end = page_num
            current_text += '\n\n' + para
        # If current_text is getting large, also flush at page boundary
        if len(current_text) >= max_chars * 1.5:
            if len(current_text) >= min_chars:
                chunks.append({
                    'text': current_text.strip(),
                    'page_start': current_page_start,
                    'page_end': current_page_end,
                    'chunk_index': chunk_index,
                })
                chunk_index += 1
            current_text = ''
            current_page_start = None
            current_page_end = None

    # Flush remainder
    if current_text and len(current_text.strip()) >= min_chars:
        chunks.append({
            'text': current_text.strip(),
            'page_start': current_page_start,
            'page_end': current_page_end,
            'chunk_index': chunk_index,
        })

    return chunks


def main():
    parser = argparse.ArgumentParser(description='Tennis Doctor - PDF extractor')
    parser.add_argument('--book-dir', default=r'C:\Users\Henry\Documents\MY VAULT\Documents\Tennis Knowledge\Tennis books',
                        help='Directory containing PDF books')
    parser.add_argument('--out', default='docs-source',
                        help='Output directory (will contain books/ subdir)')
    parser.add_argument('--manifest', default='docs-source/_manifest.json',
                        help='Manifest file to append to')
    parser.add_argument('--max-books', type=int, default=0,
                        help='Limit number of books (0=all)')
    parser.add_argument('--max-chars', type=int, default=1000,
                        help='Maximum characters per chunk (default 1000)')
    parser.add_argument('--min-chars', type=int, default=200,
                        help='Minimum characters per chunk (default 200)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would happen without writing files')
    parser.add_argument('--verbose', '-v', action='store_true')
    args = parser.parse_args()

    book_dir = Path(args.book_dir)
    if not book_dir.exists():
        print(f'ERROR: book dir not found: {book_dir}', file=sys.stderr)
        sys.exit(1)

    out_dir = Path(args.out) / 'books'
    out_dir.mkdir(parents=True, exist_ok=True)

    # Find all PDFs, skip ones in SKIP_BOOKS
    all_pdfs = sorted(book_dir.glob('*.pdf'))
    pdfs = [p for p in all_pdfs if p.name not in SKIP_BOOKS]
    skipped = len(all_pdfs) - len(pdfs)
    if args.max_books:
        pdfs = pdfs[:args.max_books]

    print(f'Found {len(all_pdfs)} PDFs total, processing {len(pdfs)} (skipped {skipped})')
    if args.dry_run:
        print('DRY RUN - first 10:')
        for p in pdfs[:10]:
            print(f'  - {p.name} ({p.stat().st_size // 1024 // 1024} MB)')
        return

    # Load existing manifest if present
    manifest_path = Path(args.manifest)
    manifest = None
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        print(f'Loaded existing manifest with {manifest["total_chunks"]} chunks')
        existing_ids = {c['id'] for c in manifest.get('chunks', [])}
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
    book_stats = []

    start_time = datetime.now()
    for idx, pdf_path in enumerate(pdfs):
        title = slugify(pdf_path.stem)
        size_mb = pdf_path.stat().st_size // 1024 // 1024
        print(f'\n[{idx + 1}/{len(pdfs)}] {pdf_path.name} ({size_mb} MB)')

        # Extract
        pages = extract_text_pymupdf(pdf_path)
        if not pages:
            print(f'  ! extraction failed, skipping')
            continue

        total_chars = sum(len(t) for _, t in pages)
        print(f'  → {len(pages)} pages, {total_chars // 1000}k chars')

        if total_chars < 1000:
            print(f'  ! too short, skipping (likely image-only PDF)')
            continue

        # Chunk
        chunks = chunk_text(pages, max_chars=args.max_chars, min_chars=args.min_chars)
        print(f'  → {len(chunks)} chunks')

        # Write full text as a single .md file
        book_dir_out = out_dir / title
        book_dir_out.mkdir(parents=True, exist_ok=True)
        full_text_path = book_dir_out / f'{title}.md'
        frontmatter = (
            f'---\n'
            f'title: "{pdf_path.stem}"\n'
            f'source: "{pdf_path.name}"\n'
            f'source_type: "pdf_book"\n'
            f'pages: {len(pages)}\n'
            f'extracted: "{datetime.now().strftime("%Y-%m-%d")}"\n'
            f'---\n\n'
        )
        full_md = frontmatter + '\n\n'.join(f'## Page {n}\n\n{t}' for n, t in pages)
        full_text_path.write_text(full_md, encoding='utf-8')

        # Write per-chunk files
        for c in chunks:
            chunk_id = f'books/{title}#{c["chunk_index"]}'
            if chunk_id in existing_ids:
                continue
            chunk_path = book_dir_out / f'{title}-chunk-{c["chunk_index"]:03d}.md'
            chunk_fm = (
                f'---\n'
                f'title: "{pdf_path.stem}"\n'
                f'page_start: {c["page_start"]}\n'
                f'page_end: {c["page_end"]}\n'
                f'chunk_index: {c["chunk_index"]}\n'
                f'---\n\n'
            )
            chunk_path.write_text(chunk_fm + c['text'], encoding='utf-8')
            new_chunks.append({
                'id': chunk_id,
                'title': pdf_path.stem,
                'slug': f'books/{title}',
                'section': 'books',
                'lang': 'en',
                'chunk_index': c['chunk_index'],
                'heading': f'Pages {c["page_start"]}-{c["page_end"]}',
                'text': c['text'][:2000],
                'page_start': c['page_start'],
                'page_end': c['page_end'],
            })

        book_stats.append({'name': pdf_path.name, 'pages': len(pages), 'chunks': len(chunks), 'chars': total_chars})
        elapsed = (datetime.now() - start_time).total_seconds()
        print(f'  ✓ done (total elapsed: {elapsed:.0f}s)')

    # Update manifest
    if new_chunks:
        manifest['chunks'].extend(new_chunks)
        manifest['total_chunks'] = len(manifest['chunks'])
        manifest['total_files'] = len(set(c['slug'] for c in manifest['chunks']))
        manifest['book_extraction'] = {
            'date': datetime.now().isoformat(),
            'books_processed': len(book_stats),
            'new_chunks': len(new_chunks),
            'books': book_stats,
        }
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f'\n=== Done ===')
        print(f'  Books processed: {len(book_stats)}')
        print(f'  New chunks: {len(new_chunks)}')
        print(f'  Total chunks now: {manifest["total_chunks"]}')
        print(f'  Manifest updated: {manifest_path}')


if __name__ == '__main__':
    main()