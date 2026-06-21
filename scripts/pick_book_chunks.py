#!/usr/bin/env python3
"""
Tennis Doctor - Simple Book Picker
==================================

Takes the manifest, keeps ALL Vault chunks, and adds a sample of book chunks
to reach the target vector count.
"""

import json
import sys
import argparse
import re
from pathlib import Path
from collections import defaultdict


# Tier 1 = must include, Tier 5 = skip
PRIORITY_BOOKS = {
    'Bollettieris_Tennis_Handbook_-_Nick_Bollettieri': 1,
    'Tennis_Medicine_-_Di_giacomo': 1,
    'The_biomechanics_of_tennis__body_movement_studies_with_case_histories': 1,
    'Tennis_For_Dummies_2nd_Edition_-_Patrick_McEnroe': 1,
    'Coaching_Tennis': 1,
    'Science_of_coaching_tennis': 1,
    'Teaching_Tennis_Volume_1_-_Martin_van_Daalen': 1,
    'Serious_Tennis': 1,
    'Tennis_skills_&_drills': 1,
    'Tennis_strokes_and_strategies': 1,
    'Play_winning_tennis_with_perfect_fundamentals._Book_1': 1,
    'Tennis_tactics__singles_and_doubles': 1,
    'Complete_conditioning_for_tennis': 1,
    'Focused_for_tennis': 1,
    'Maximum_tennis__10_keys_to_unleashing_your_on-court_potential': 1,
    'Tennis_Fundamentals': 1,
    'Tennis_handbook': 1,
    'Release_Your_Kinetic_Chain__Exercises_For_the_Shoulder_to_Hand__Activating_Your_Arm\'s_Kinetic_Chain!': 1,
    'Tennis_Science-Behind_Carla_Mooney': 1,
    'The_Handbook_Of_Tennis_-_Paul_Douglas': 1,
    'The_mental_ADvantage__developing_your_psychological_skills_in_tennis': 2,
    'Mastering_the_art_of_winning_tennis__the_psychology_behind_successful_strategy': 2,
    'Tennis_and_the_mind': 2,
    'Visual_tennis__mental_imagery_and_the_quest_for_the_winning_edge': 2,
    'Inside_tennis': 2,
    'Topspin_to_better_tennis': 2,
    'High_tech_tennis': 2,
    'Doubles_strategy__a_creative_and_psychological_approach_to_tennis': 2,
    'How_to_play_winning_doubles': 2,
    'Modern_tennis_doubles': 2,
    'Pattern_play_tennis': 2,
    'Tennis_doubles__tactics_and_formations': 2,
    'Winning_doubles': 2,
    'Coaching_tennis_successfully': 2,
    'Coaching_youth_tennis': 2,
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', default='docs-source/_manifest.json')
    parser.add_argument('--out', default='docs-source/_manifest.json')
    parser.add_argument('--target-vectors', type=int, default=28000)
    parser.add_argument('--chunks-per-book', type=int, default=20)
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    if not manifest_path.exists():
        print(f'ERROR: {manifest_path} not found')
        sys.exit(1)

    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    chunks = manifest['chunks']

    vault_chunks = [c for c in chunks if c['section'] != 'books']
    book_chunks = [c for c in chunks if c['section'] == 'books']

    print(f'Vault chunks: {len(vault_chunks)}')
    print(f'Book chunks available: {len(book_chunks)}')

    # Group by book
    by_book = defaultdict(list)
    for c in book_chunks:
        by_book[c['title']].append(c)

    # Sort by priority, take evenly-spaced chunks per book
    selected_books = []
    for title, book_chunks_list in by_book.items():
        # Sort chunks by index
        book_chunks_list.sort(key=lambda c: c.get('chunk_index', 0))
        # Skip first 2 (cover/title) and take evenly distributed samples
        if len(book_chunks_list) <= 2:
            continue
        available = book_chunks_list[2:]
        n = min(args.chunks_per_book, len(available))
        if n <= 0:
            continue
        # Take every Nth to get spread coverage
        step = max(1, len(available) // n)
        picks = [available[i * step] for i in range(n) if i * step < len(available)]
        for c in picks:
            c['_book_priority'] = PRIORITY_BOOKS.get(title, 5)
        selected_books.extend(picks)

    # Sort by priority (1=best first) then keep until we hit target
    selected_books.sort(key=lambda c: c.get('_book_priority', 5))
    remaining_slots = args.target_vectors - len(vault_chunks)
    final_book_chunks = selected_books[:remaining_slots]

    print(f'\nAvailable book chunks (after sampling): {len(selected_books)}')
    print(f'Remaining slots: {remaining_slots}')
    print(f'Final book chunks: {len(final_book_chunks)}')
    print(f'Books represented: {len(set(c["title"] for c in final_book_chunks))}')

    # Clean up metadata
    for c in final_book_chunks:
        c.pop('_book_priority', None)

    new_chunks = vault_chunks + final_book_chunks
    manifest['chunks'] = new_chunks
    manifest['total_chunks'] = len(new_chunks)
    manifest['total_files'] = len(set(c['slug'] for c in new_chunks))
    manifest['selection'] = {
        'target_vectors': args.target_vectors,
        'vault_chunks': len(vault_chunks),
        'book_chunks': len(final_book_chunks),
        'books_used': len(set(c['title'] for c in final_book_chunks)),
    }
    Path(args.out).write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')

    sections = defaultdict(int)
    for c in new_chunks:
        sections[c['section']] += 1
    print(f'\nFinal total: {len(new_chunks)} chunks')
    print('By section:')
    for s, n in sorted(sections.items(), key=lambda x: -x[1]):
        print(f'  {s}: {n}')


if __name__ == '__main__':
    main()