#!/usr/bin/env python3
"""
Tennis Doctor - Manifest Cleaner
=================================

Removes low-quality chunks from the manifest:
- Too short (< 100 chars)
- Mostly page numbers / TOC entries
- Index pages (mostly digit content)
- Author/title lists

This shrinks the index to only the useful content.
"""

import json
import re
import sys
import argparse
from pathlib import Path


def is_low_quality(text):
    """Return True if chunk is likely TOC / index / list of names."""
    if len(text) < 200:
        return True

    # Very high digit ratio = likely TOC/index
    digits = sum(c.isdigit() for c in text)
    if digits / max(len(text), 1) > 0.20:
        return True

    # Mostly short words separated by commas and lots of digits = TOC/index
    # (e.g. "Forehand, 27, 38, 91" — average 3-4 chars, lots of commas, lots of digits)
    if digits > 50:  # more than 50 digit characters in the chunk
        comma_count = text.count(',')
        if comma_count > 30:
            return True

    # Common TOC/index keywords in title-like context
    lower = text[:300].lower().strip()
    if (lower.startswith('index') or lower.startswith('contents') or
        'table of contents' in lower[:200]):
        return True

    # Page-number-only chunks (just digits and punctuation)
    non_digit_non_punct = sum(1 for c in text if c.isalpha())
    if non_digit_non_punct < 20 and len(text) > 100:
        return True

    return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', default='docs-source/_manifest.json')
    parser.add_argument('--out', default='docs-source/_manifest.json')
    parser.add_argument('--verbose', '-v', action='store_true')
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    if not manifest_path.exists():
        print(f'ERROR: {manifest_path} not found')
        sys.exit(1)

    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    total_before = len(manifest['chunks'])
    print(f'Before: {total_before} chunks')

    # Filter
    kept = []
    removed = 0
    for c in manifest['chunks']:
        if is_low_quality(c.get('text', '')):
            removed += 1
            if args.verbose and removed <= 5:
                print(f'  - removing: {c.get("title", "?")} chunk {c.get("chunk_index", "?")}: {c.get("text", "")[:80]!r}')
        else:
            kept.append(c)

    manifest['chunks'] = kept
    manifest['total_chunks'] = len(kept)
    manifest['cleaning'] = {
        'date': manifest.get('cleaning', {}).get('date', '') + ' | ' + str(__import__('datetime').datetime.now().isoformat()),
        'removed': removed,
        'remaining': len(kept),
    }
    Path(args.out).write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')

    print(f'After: {len(kept)} chunks')
    print(f'Removed: {removed} ({removed/total_before*100:.1f}%)')

    # Show by section
    sections = {}
    for c in kept:
        sections.setdefault(c['section'], 0)
        sections[c['section']] += 1
    print('\nBy section:')
    for s, n in sorted(sections.items(), key=lambda x: -x[1]):
        print(f'  {s}: {n}')


if __name__ == '__main__':
    main()