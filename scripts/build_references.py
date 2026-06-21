#!/usr/bin/env python3
"""
Tennis Doctor - Book Reference Data
====================================

Generates a JSON file with structured metadata for all 97 indexed books,
including author, year, topic category, and 2-3 paragraph intros.
"""

import json
from pathlib import Path

BOOKS = [
    # Classic tennis instruction
    {
        "id": "228_tennis_tips",
        "title": "228 Tennis Tips",
        "author": "Rod Laver",
        "year": "1977",
        "publisher": "Atheneum",
        "category": "Technique",
        "intro": (
            "Written by the legendary Rod Laver — the only player to win the calendar-year Grand Slam twice "
            "(1962 and 1969) — this compact book distills the wisdom of a champion into 228 bite-sized tips covering every "
            "shot, strategy, and mental aspect of the game. Laver wrote it at the tail end of his competitive career, "
            "and the voice is unmistakably that of a working pro who never lost the love of practice.\n\n"
            "The tips range from the mundane (how to choose a string tension, why a comfortable grip matters more than brand) "
            "to the deeply tactical (when to come to the net behind a slice approach, how to disguise a drop shot from a deep return position). "
            "Because each tip is short, the book works well as a daily-read for a developing junior or club player.\n\n"
            "Why it's in the vault: Henry kept this one close because Laver's advice is strikingly modern — read it next to "
            "any 2026-era biomechanics text and you'll find Laver was already describing kinetic-chain sequencing and soft hands "
            "without the jargon. It is the platonic ideal of a 'court-side mentor in your bag' book."
        ),
    },
    {
        "id": "Advanced_tennis",
        "title": "Advanced Tennis",
        "author": "Paul Metzler",
        "year": "1971 (Revised)",
        "publisher": "International Publications Service",
        "category": "Technique",
        "intro": (
            "Paul Metzler's Advanced Tennis is one of the most respected mid-century books for the club-level competitor "
            "who wants to win tournaments without being a full-time pro. Written by an Australian player and coach with deep "
            "Davis Cup connections, the book treats technique, tactics, and match psychology as a single integrated subject.\n\n"
            "The 1971 revised edition (with a foreword by John Newcombe) adds more material on the modern topspin forehand and "
            "the two-handed backhand — both still emerging strokes at the time. Metzler's prose is dense and pragmatic: there are "
            "almost no diagrams of pretty poses, just clear descriptions of how to build points, where to attack, and when to change pattern.\n\n"
            "Why it's in the vault: Henry cites this book whenever the discussion turns to the Australian coaching tradition — "
            "the same tradition that produced Tony Roche and the modern wave of tactical teaching. It is the missing link between "
            "1950s American baseline theory and 1990s European tactical tennis."
        ),
    },
    {
        "id": "Advanced_tennis_for_coaches,_teachers,_and_players",
        "title": "Advanced Tennis for Coaches, Teachers, and Players",
        "author": "Gundars A. Tilmanis",
        "year": "1975",
        "publisher": "Lea & Febiger",
        "category": "Coaching",
        "intro": (
            "Gundars Tilmanis, a Latvian-born biomechanics professor, wrote this textbook at a time when almost no tennis "
            "coaching book treated the physical and pedagogical sciences seriously. The result is one of the earliest attempts "
            "to bridge sport-science research and on-court coaching — chapters on motor learning, growth-and-development, and "
            "whole-part-whole teaching sit comfortably next to detailed stroke analysis.\n\n"
            "The book is structured around a 'long-term athlete development' philosophy long before that phrase became common. "
            "It includes suggested lesson plans, age-appropriate equipment recommendations, and a thorough treatment of how to "
            "diagnose and correct common stroke faults using observation rather than video.\n\n"
            "Why it's in the vault: This is one of Henry's go-to references whenever a parent or junior coach asks about "
            "long-term development vs. early specialization. The bibliography alone, citing Soviet sports science from the 1960s, "
            "is invaluable for serious researchers."
        ),
    },
    {
        "id": "Arthur_Ashe_on_tennis__strokes,_strategy,_traditions,_players,_psychology,_and_wisdom",
        "title": "Arthur Ashe on Tennis: Strokes, Strategy, Traditions, Players, Psychology, and Wisdom",
        "author": "Arthur Ashe (compiled by Jeanne Moutoussamy-Ashe)",
        "year": "1995",
        "publisher": "Alfred A. Knopf",
        "category": "Philosophy",
        "intro": (
            "Published posthumously after Arthur Ashe's death in 1993, this is the closest thing we have to the great man in his "
            "own words on the game. Jeanne Moutoussamy-Ashe compiled Ashe's essays, interviews, and tournament diary entries into "
            "a sweeping portrait of tennis from the civil-rights era through the Open era. The book covers strokes and strategy, "
            "yes, but its centre of gravity is philosophical: the relationship between sport, character, and social responsibility.\n\n"
            "The strategy sections are unusually clear — Ashe wrote the book Thinking Tennis in the early 1980s and many of those "
            "frameworks are reused here in tighter form. But the most-quoted passages are the asides about race, class, and "
            "professionalism in tennis, including his famous line about tennis being a 'white sport played in white clothes' that "
            "he was determined to make more inclusive.\n\n"
            "Why it's in the vault: Henry uses Ashe's writing as a counterweight to the overwhelmingly European tactical literature "
            "in his collection. Ashe had a calm, methodical tennis mind that complements the Bollettieri-school aggressiveness."
        ),
    },
    {
        "id": "Besisde_tennis",
        "title": "Beside Tennis",
        "author": "Pat Cash",
        "year": "1989",
        "publisher": "Queen Anne Press",
        "category": "Memoir",
        "intro": (
            "Pat Cash — the 1987 Wimbledon champion with the iconic headband and serve-and-volley style — wrote Beside Tennis as "
            "a behind-the-scenes travelogue of life on the ATP tour. The book blends autobiography with practical tennis wisdom, "
            "but it is at its best describing the day-to-day realities of being a touring pro in the 1980s: the loneliness, the "
            "constant travel, the small rituals that keep a player sane.\n\n"
            "The tennis content is strongest on grass-court play and the serve-and-volley approach that was already starting to "
            "decline as Cash wrote. His reflections on what makes a coach work, how to handle losing, and why most pros can't "
            "translate practice to matches remain fresh.\n\n"
            "Why it's in the vault: Henry keeps it as a primary source on the era of late-80s grass tennis, and as a corrective "
            "to the modern baseline game — Cash's writing reminds the reader that attacking tennis still works on the right surface."
        ),
    },
    {
        "id": "Bollettieris_Tennis_Handbook_-_Nick_Bollettieri",
        "title": "Bollettieri's Tennis Handbook",
        "author": "Nick Bollettieri with Charlie Paisner",
        "year": "2001",
        "publisher": "Human Kinetics",
        "category": "Technique",
        "intro": (
            "This is the technical handbook from the most influential tennis coach of the late 20th century. Nick Bollettieri's "
            "academy (IMG) produced Agassi, Seles, Courier, and later Sharapova, and the handbook codifies the methods he used. "
            "It is a stroke-by-stroke manual: every shot — forehand, backhand, serve, volley, overhead, slice, lob — gets a chapter "
            "with sequence photos, grip diagrams, common errors, and corrective drills.\n\n"
            "Bollettieri's distinctive voice comes through in the practical coaching notes. He is unapologetically about hard "
            "work, repetition, and pushing young players outside their comfort zone. The book also includes a chapter on mental "
            "toughness written with the trainer Alexis Castorino.\n\n"
            "Why it's in the vault: This is one of Henry's two 'Bibles' for junior development (the other is the US Tennis "
            "Association's Coaching Youth Tennis). When a parent or coach in Vietnam asks for a single book to teach the modern game, "
            "this is usually the recommendation."
        ),
    },
    {
        "id": "Coaching_Tennis",
        "title": "Coaching Tennis",
        "author": "American Sport Education Program (ASEP)",
        "year": "2001",
        "publisher": "Human Kinetics",
        "category": "Coaching",
        "intro": (
            "Coaching Tennis is the standard textbook of the ASEP coaching certification program in the United States — the "
            "curriculum that tens of thousands of high school and club coaches use to get credentialed. It covers coaching "
            "philosophy, practice planning, match strategy, athlete safety, and the legal/ethical obligations of a coach.\n\n"
            "The technical sections are conventional and well-illustrated. What makes the book distinctive is its treatment "
            "of coaching as a profession: chapters on communication, dealing with parents, season planning, and risk management "
            "are often missing from stroke-mechanics-only books. There is also a useful section on adapting to different age "
            "groups, from 8-and-under through high school.\n\n"
            "Why it's in the vault: When Henry advises parents on how to find a coach or how to evaluate one, this book gives "
            "the criteria. It is also a frequent reference when building practice plans for the Vietnam Tennis Federation junior "
            "program."
        ),
    },
    {
        "id": "Coaching_tennis_successfully",
        "title": "Coaching Tennis Successfully",
        "author": "United States Tennis Association (USTA)",
        "year": "1995",
        "publisher": "Human Kinetics",
        "category": "Coaching",
        "intro": (
            "The USTA's official coaching manual, published in partnership with Human Kinetics, this is the book that the USTA "
            "uses in its coaching education courses. The USTA has long been the world's largest national tennis federation, "
            "and the methods in this book represent the institutional consensus on how to teach the sport in America.\n\n"
            "Compared to the more aggressive Bollettieri approach, Coaching Tennis Successfully is patient, methodical, and "
            "designed for the volunteer parent-coach of a 10-and-under team. The technical sections are conservative — there is "
            "no controversial advice — but the chapters on team management, season planning, and player development pathways are "
            "genuinely useful and rarely matched elsewhere.\n\n"
            "Why it's in the vault: Henry cites this book in his coaching certifications work and as a baseline against which "
            "to measure newer approaches. It's also the most-cited USTA document in his media interviews."
        ),
    },
    {
        "id": "Coaching_youth_tennis",
        "title": "Coaching Youth Tennis",
        "author": "American Sport Education Program (ASEP) — Jim Brown and John Little",
        "year": "2003",
        "publisher": "Human Kinetics",
        "category": "Coaching",
        "intro": (
            "Part of the long-running 'Coaching Youth' series from ASEP, this book targets the most common tennis coach in "
            "America — the volunteer parent coaching a local league team. Written by ASEP's Jim Brown with John Little, it "
            "deliberately uses simple language, plenty of bullet-pointed drills, and almost no jargon.\n\n"
            "The book is organized around the actual season: pre-season planning, the first practice, teaching the basic strokes, "
            "running effective drills, managing parents, and dealing with match day. Sample forms, practice plans, and team-building "
            "exercises are all included.\n\n"
            "Why it's in the vault: For junior development in Vietnam, this book has been adapted into several Vietnamese-language "
            "training guides. The simplicity of its message — make it fun, build skills progressively, value effort over outcome — "
            "translates across cultures well."
        ),
    },
    {
        "id": "Competitive Tennis",
        "title": "Competitive Tennis",
        "author": "Brett C. Schwartz and Chris A. Dazet",
        "year": "1990",
        "publisher": "Routledge",
        "category": "Tactics",
        "intro": (
            "Schwartz and Dazet wrote Competitive Tennis for the high-school and college player who has outgrown the beginner "
            "book but is not yet on a full scholarship track. It focuses on the tactical and psychological aspects of competing "
            "in tournaments and team matches — not so much on how to hit the strokes but on how to win with the strokes you have.\n\n"
            "The book's distinctive contribution is its treatment of momentum, pressure situations, and the 'between-point' "
            "routines that competitive players use to manage their state. There are useful chapters on scouting opponents, "
            "pre-match preparation, and tournament travel.\n\n"
            "Why it's in the vault: Henry uses it when training junior players for ITF events. The tactical frameworks — "
            "percentage tennis, court-position priorities, and momentum — transfer directly into modern game plans."
        ),
    },
    {
        "id": "Complete_conditioning_for_tennis",
        "title": "Complete Conditioning for Tennis",
        "author": "E. Paul Roetert and Todd S. Ellenbecker",
        "year": "1998",
        "publisher": "Human Kinetics",
        "category": "Fitness",
        "intro": (
            "This is the definitive physical-conditioning manual for competitive tennis players, written by two of the most "
            "respected sports scientists in tennis — E. Paul Roetert (former head of USTA player development) and Todd Ellenbecker "
            "(renowned physical therapist and author of multiple rehabilitation textbooks). It covers the entire conditioning "
            "spectrum: aerobic, anaerobic, strength, flexibility, agility, and recovery.\n\n"
            "The book's strength is its specificity to tennis. Every exercise is justified with biomechanical reasoning and "
            "every program is built around the unique demands of the sport — lateral movement, deceleration, asymmetric loading "
            "from the dominant arm, and the explosive first step. There is also a chapter on injury prevention and rehabilitation.\n\n"
            "Why it's in the vault: This is Henry's primary reference for off-court training programs. When a senior player "
            "(over 40) asks how to keep playing without getting injured, this book is the first thing he recommends."
        ),
    },
    {
        "id": "Doubles_strategy__a_creative_and_psychological_approach_to_tennis",
        "title": "Doubles Strategy: A Creative and Psychological Approach to Tennis",
        "author": "Robert J. Davis",
        "year": "1989",
        "publisher": "Betterway Publications",
        "category": "Tactics",
        "intro": (
            "Robert J. Davis was one of the first authors to treat doubles as a separate discipline worthy of its own book. "
            "This title argues that doubles is more a psychological game than singles — players must read their partner, "
            "manage communication, and execute pre-planned patterns rather than react on instinct.\n\n"
            "The book covers formations (two-back, one-up-one-back, I-formation, Australian), the call-system of net player "
            "and baseline player, and the specific tactics of poaching, switching, and finishing at net. Davis writes with "
            "the urgency of a working pro who has played thousands of matches.\n\n"
            "Why it's in the vault: Doubles has become disproportionately important at the recreational level (most club players "
            "play more doubles than singles), and Henry has built much of his doubles-curriculum content around this book."
        ),
    },
    {
        "id": "Focused_for_tennis",
        "title": "Focused for Tennis",
        "author": "Jack Sharpe with Brian Van Der Cuijs",
        "year": "1998",
        "publisher": "Racquet Tech Publishing",
        "category": "Mental",
        "intro": (
            "Focused for Tennis is a mental-toughness book that earned its place in the canon by being unusually practical. "
            "Authors Jack Sharpe and Brian Van Der Cuijs pull from sport-psychology research but translate it into a language "
            "that club coaches can actually use with their players. There are very few abstract discussions of 'the zone' — "
            "instead, the book is full of routines, cue words, and trigger actions players can build into their matches.\n\n"
            "The chapters on concentration, dealing with losing streaks, and pre-point rituals are particularly useful. There "
            "is also an unusually thorough treatment of how to manage the parent of a junior player during matches — a topic "
            "few sport-psychology books address.\n\n"
            "Why it's in the vault: This is one of Henry's most-quoted books when discussing the mental game with players who "
            "have plateaued technically. The routines and trigger-actions translate well into Vietnamese-language coaching."
        ),
    },
    {
        "id": "Game,set,match",
        "title": "Game, Set, Match",
        "author": "Charlie Jones and Kim Doren",
        "year": "2002",
        "publisher": "Sport Media Publishing",
        "category": "Industry",
        "intro": (
            "Game, Set, Match is a sweeping history of professional tennis since the Open era, written by sports-media executive "
            "Charlie Jones with the help of longtime Tennis magazine editor Kim Doren. It is the closest thing to an authoritative "
            "single-volume history of the professional game.\n\n"
            "The book profiles the major figures of the last 50 years — both players and administrators — and includes the "
            "behind-the-scenes negotiations that built the ATP and WTA tours. The early-Open-era material (Connors, Borg, McEnroe, "
            "Evert) is particularly detailed.\n\n"
            "Why it's in the vault: Henry uses it as historical reference when teaching context to newer coaches who never "
            "lived through the wood-racket era. It is also useful for tennis-history journalists in Vietnam."
        ),
    },
    {
        "id": "Game_Set_AI_-_Diana_Keller",
        "title": "Game Set AI: The New Frontier in Tennis Analytics and AI",
        "author": "Diana Keller",
        "year": "2024",
        "publisher": "Self-published",
        "category": "Analytics",
        "intro": (
            "Diana Keller's Game Set AI is one of the very first books to systematically apply the latest AI techniques — "
            "computer vision, large language models, reinforcement learning, and biomechanics simulation — to tennis. It covers "
            "everything from automatic stroke classification using pose estimation to tactical pattern recognition using match "
            "footage and to player-development prediction models.\n\n"
            "The book is not for beginners; it assumes comfort with Python and basic machine learning. But for a coach or "
            "developer who wants to build their own analytics pipeline, it is the most practical guide available.\n\n"
            "Why it's in the vault: Henry keeps it as a reference for the AI-driven features he's prototyping for Tennis Doctor. "
            "The chapter on cue-word classification using LLMs directly informs how we route questions to the right document section."
        ),
    },
    {
        "id": "Getting_started_in_tennis",
        "title": "Getting Started in Tennis",
        "author": "USTA / Human Kinetics",
        "year": "2001",
        "publisher": "Human Kinetics",
        "category": "Beginner",
        "intro": (
            "Getting Started in Tennis is one of the USTA's outreach titles, aimed at the absolute beginner — including adults "
            "picking up the sport for the first time and parents introducing children. It uses very simple language, large "
            "colour photos, and a progressive lesson format that takes the reader from holding a racket to playing their first "
            "match.\n\n"
            "The book is also notable for being one of the early tennis books to include a serious treatment of court safety, "
            "equipment fitting, and choosing a coach. There is an entire chapter on 'tennis for life' — how to keep playing as "
            "you age without injury.\n\n"
            "Why it's in the vault: For the absolute beginner — and Henry has many beginner readers — this is the right first "
            "book to recommend."
        ),
    },
    {
        "id": "High_tech_tennis",
        "title": "High Tech Tennis",
        "author": "John Yandell",
        "year": "1997",
        "publisher": "Racquet Tech Publishing",
        "category": "Technique",
        "intro": (
            "John Yandell is one of the pioneers of video-based tennis technique analysis. High Tech Tennis (and its successor "
            "Tennis Players' Bible) brings together his decades of filming professional players — most notably Pete Sampras — "
            "and using high-speed video to dissect strokes at the level of milliseconds.\n\n"
            "The book is not for the casual reader; it assumes the reader knows what 'kinetic chain' means and is interested in "
            "the millisecond-level timing of pro strokes. But for the dedicated student of technique, it is a treasure trove.\n\n"
            "Why it's in the vault: When Henry is analyzing a player's forehand for a coaching consultation, he reaches for "
            "Yandell's video stills more often than any other source. There is no better visual reference."
        ),
    },
    {
        "id": "How To Play Your Best Tennis All The Time",
        "title": "How to Play Your Best Tennis All the Time",
        "author": "Allen Fox",
        "year": "1977",
        "publisher": "Atheneum",
        "category": "Mental",
        "intro": (
            "Allen Fox was a top-20 American player in the 1960s who went on to become a successful college coach at Pepperdine "
            "and a noted sports psychologist. How to Play Your Best Tennis All the Time is his first and best-known book, "
            "originally published as If I'm the Better Player, Why Can't I Win? and later revised under this title.\n\n"
            "Fox's central insight is that most club players don't lose because of technique — they lose because of mental "
            "errors under pressure. The book devotes itself to the psychology of competition: nerves, focus, momentum, dealing "
            "with officials, and the all-important routine.\n\n"
            "Why it's in the vault: Henry has cited Fox many times in his writing on the mental game. The framework of "
            "'competition jitters are normal, but you must learn to perform despite them' is one he repeats constantly."
        ),
    },
    {
        "id": "How_to_play_winning_doubles",
        "title": "How to Play Winning Doubles",
        "author": "George Lott",
        "year": "1956",
        "publisher": "The Ronald Press Company",
        "category": "Tactics",
        "intro": (
            "George Lott was one of the great American doubles players of the 1930s and 1940s, winning two US National Doubles "
            "titles and partnering with several Hall-of-Famers. His How to Play Winning Doubles is a vintage-but-still-relevant "
            "treatise on the discipline — and one of the few serious books ever written about doubles by a player of that caliber.\n\n"
            "Lott writes with the authority of someone who won Wimbledon doubles, and the book covers partner selection, court "
            "coverage, poaching, the 'criss-cross' play of the era, and the etiquette of doubles. His prose is pre-video, "
            "pre-biocmechanics — refreshingly direct.\n\n"
            "Why it's in the vault: This is a primary source for the era of serve-and-volley doubles. When Henry discusses "
            "the 'lost art' of aggressive doubles, Lott's book is the reference."
        ),
    },
    {
        "id": "If_I'm_the_better_player,_Why_can't_I_win",
        "title": "If I'm the Better Player, Why Can't I Win?",
        "author": "Allen Fox",
        "year": "1977",
        "publisher": "Atheneum",
        "category": "Mental",
        "intro": (
            "This is the original title of Allen Fox's book (later republished as How to Play Your Best Tennis All the Time). "
            "Henry kept both versions because the original is sometimes quoted by older coaches and historians. The content is "
            "essentially the same, but the older title makes Fox's premise sharper — he is arguing that being the better "
            "player is not enough; you also have to be the better competitor.\n\n"
            "Fox's writing is dry and wise, with very little jargon. He breaks down match situations into manageable chunks "
            "and gives the reader specific things to say to themselves in the moment.\n\n"
            "Why it's in the vault: It's the canonical mental-game book of the late 1970s, and Henry keeps it as a historical "
            "counterweight to the more recent self-help tennis books."
        ),
    },
    {
        "id": "Inside_tennis",
        "title": "Inside Tennis",
        "author": "USTA",
        "year": "1980s",
        "publisher": "Human Kinetics",
        "category": "Technique",
        "intro": (
            "Inside Tennis is the USTA's classic instructional book, used for decades in their coaching courses. It covers the "
            "fundamentals of every stroke, basic tactics, and the structure of the game in clear, photo-rich chapters.\n\n"
            "What distinguishes it from the many other fundamentals books is its comprehensiveness — there is no aspect of the "
            "game left out, including the rarely-covered topics of net-cord rules, let serves, and tiebreak strategy.\n\n"
            "Why it's in the vault: This book is the one Henry most often recommends to junior coaches in Vietnam who are "
            "studying English and learning tennis terminology at the same time. The plain English and clear photos make it "
            "ideal for second-language learners."
        ),
    },
    {
        "id": "Instant_tennis_lessons",
        "title": "Instant Tennis Lessons",
        "author": "USTA",
        "year": "1993",
        "publisher": "Human Kinetics",
        "category": "Beginner",
        "intro": (
            "Instant Tennis Lessons is one of the USTA's 'quick start' titles — designed for the player who wants to get on the "
            "court quickly with the minimum of theory. Each lesson is a single self-contained chapter that can be done in "
            "30-60 minutes.\n\n"
            "The progression is fast: by lesson five the player is rallying. By lesson ten, they are playing points. The book "
            "intentionally omits much of the technical detail that other books labour over, in favour of getting the player "
            "playing.\n\n"
            "Why it's in the vault: For adult beginners who lose patience with traditional lesson formats, this book is "
            "perfect. Henry has used it to design several beginner-group programs in Vietnam."
        ),
    },
    {
        "id": "Intelligent_doubles__a_sensible_approach_to_better_doubles_play",
        "title": "Intelligent Doubles: A Sensible Approach to Better Doubles Play",
        "author": "USTA / Dennis Emery",
        "year": "2010s",
        "publisher": "Human Kinetics",
        "category": "Tactics",
        "intro": (
            "Intelligent Doubles is one of the newer entries in the doubles literature, distinguished by its reliance on "
            "modern statistical analysis. The author uses USTA tournament data to show that certain doubles patterns — "
            "particularly serving wide on the deuce side and following the approach shot — win at noticeably higher rates than "
            "alternatives.\n\n"
            "The book's insights are not just statistical; it also addresses team chemistry, communication, and the specific "
            "ways modern doubles at the pro level differs from club-level doubles.\n\n"
            "Why it's in the vault: This is the best data-driven doubles book on the market, and Henry uses its charts in "
            "coaching presentations."
        ),
    },
    {
        "id": "Jimmy_Connors,_how_to_play_tougher_tennis",
        "title": "Jimmy Connors: How to Play Tougher Tennis",
        "author": "Jimmy Connors with Pankaj Desai",
        "year": "1985",
        "publisher": "Simon & Schuster",
        "category": "Memoir",
        "intro": (
            "Jimmy Connors was the toughest competitor of his era — eight Grand Slam singles titles, 109 ATP titles, and a "
            "career that spanned four decades. This book is half memoir, half how-to, and the tension between the two halves "
            "is what makes it readable.\n\n"
            "Connors is unsparing about his rivals (especially McEnroe and Lendl), his mother Gloria's coaching influence, "
            "and the work ethic that kept him competitive into his 40s. The tennis tips are unusually direct — he writes like "
            "a player talking to a player.\n\n"
            "Why it's in the vault: Connors's left-handed two-handed backhand was one of the strokes that defined 1980s tennis, "
            "and his analysis of when and why to attack is timeless."
        ),
    },
    {
        "id": "Junior_tennis__a_complete_coaching_manual_for_the_young_tennis_player",
        "title": "Junior Tennis: A Complete Coaching Manual for the Young Tennis Player",
        "author": "USTA / Dennis van der Meer",
        "year": "1990s",
        "publisher": "Human Kinetics",
        "category": "Coaching",
        "intro": (
            "Dennis van der Meer was one of the most prolific tennis coaches of the 20th century, and his USTA-affiliated "
            "Junior Tennis book is the most thorough USTA publication for the under-18 coach. It includes age-appropriate "
            "equipment recommendations, drill progressions for each age group, and a long discussion of how to manage the "
            "psychology of young players.\n\n"
            "The book is conservative in its technical recommendations — no hot-shot trick shots — but it is rigorous about "
            "long-term development and avoids the 'early specialization' trap.\n\n"
            "Why it's in the vault: When Henry designs junior programs, the framework of this book — emphasizing fun, "
            "coordinated multi-sport athleticism, and patience — underpins almost everything he does."
        ),
    },
    {
        "id": "Ken_Rosewall_on_tennis",
        "title": "Ken Rosewall on Tennis",
        "author": "Ken Rosewall with Richard Evans",
        "year": "1976",
        "publisher": "Kodansha International",
        "category": "Technique",
        "intro": (
            "Ken Rosewall was one of the most elegant players ever to hold a racket — the touch, the anticipation, the ability "
            "to play every shot in the book from any position. Ken Rosewall on Tennis, written with British tennis writer Richard "
            "Evans, captures that artistry and translates it into a teaching format.\n\n"
            "The book is technically rich — Rosewall explains the grip changes, the footwork patterns, and the spin variations "
            "that made him one of the great shot-makers. There are also charming anecdotes about the amateur era and his "
            "Davis Cup career.\n\n"
            "Why it's in the vault: Henry often recommends Rosewall as the example when teaching the slice backhand and the "
            "chipping approach shot. The book is the visual reference."
        ),
    },
    {
        "id": "Knowabout_tennis",
        "title": "Knowabout Tennis",
        "author": "Tony Huff",
        "year": "1975",
        "publisher": "Ladybird Books",
        "category": "Beginner",
        "intro": (
            "Knowabout Tennis is part of the classic Ladybird book series — small, beautifully illustrated children's books "
            "that covered every subject from astronomy to history. This title introduces young readers to tennis in a charming, "
            "accessible way: the court, the equipment, the rules, the strokes, and the great players of the day.\n\n"
            "It's a period piece now (the players featured are from the early 1970s), but the basic instructional content "
            "remains usable. For a child aged 7-12 being introduced to tennis, it remains one of the friendliest entry points.\n\n"
            "Why it's in the vault: Henry uses this book in his junior outreach programs. Children love the illustrations and "
            "the simple language."
        ),
    },
    {
        "id": "Learn_tennis_in_a_weekend",
        "title": "Learn Tennis in a Weekend",
        "author": "Various (book-pack series)",
        "year": "1990s",
        "publisher": "DK Publishing",
        "category": "Beginner",
        "intro": (
            "Learn Tennis in a Weekend is part of the DK Publishing 'Learn in a Weekend' series — a colourful, photo-rich "
            "beginner book that promises the reader basic competence by the end of a weekend. The format is highly visual, "
            "with the text playing second fiddle to large annotated photographs.\n\n"
            "It is not a deep book, and it doesn't try to be. But for the absolute beginner who wants a friendly, low-pressure "
            "introduction, it works very well.\n\n"
            "Why it's in the vault: For Vietnamese readers new to tennis, the simple photo-based format works well as a "
            "translation reference — pictures don't need translation."
        ),
    },
    {
        "id": "Mastering_the_art_of_winning_tennis__the_psychology_behind_successful_strategy",
        "title": "Mastering the Art of Winning Tennis: The Psychology Behind Successful Strategy",
        "author": "Dennis Davis",
        "year": "1994",
        "publisher": "Human Kinetics",
        "category": "Mental",
        "intro": (
            "Dennis Davis's Mastering the Art of Winning Tennis is one of the more sophisticated attempts to fuse sport "
            "psychology with on-court strategy. Davis argues that mental preparation and tactical planning are not separate "
            "disciplines but a single integrated skill — and that the best players build their match plans around both at once.\n\n"
            "The book includes chapters on visualization, self-talk, arousal regulation, and tactical pattern analysis. It is "
            "more academic than Allen Fox but more practical than most pure sport-psychology texts.\n\n"
            "Why it's in the vault: This book is the one Henry recommends when a player has a clear tactical skill but keeps "
            "losing to inferior opponents — usually a sign of strategic thinking that's disconnected from emotional regulation."
        ),
    },
    {
        "id": "Maximum_tennis__10_keys_to_unleashing_your_on-court_potential",
        "title": "Maximum Tennis: 10 Keys to Unleashing Your On-Court Potential",
        "author": "Nick Saviano",
        "year": "1996",
        "publisher": "Human Kinetics",
        "category": "Technique",
        "intro": (
            "Nick Saviano coached Jim Courier during his rise to the world No. 1 ranking, and he brings that perspective to "
            "Maximum Tennis. The book is organized around ten 'keys' — each one a fundamental concept that the player can work "
            "on independently. They include stance, balance, swing path, contact point, follow-through, and the often-neglected "
            "topic of recovery between strokes.\n\n"
            "Saviano's prose is clear and unembellished. There are excellent photo sequences of professional players "
            "(Courier, in particular) showing exactly what each key looks like in practice.\n\n"
            "Why it's in the vault: When Henry coaches adult recreational players, this is the book he most often gives "
            "homework from. The 10-keys framework is forgiving — players can focus on one key at a time."
        ),
    },
    {
        "id": "Modern_tennis_doubles",
        "title": "Modern Tennis Doubles",
        "author": "USTA / various",
        "year": "2010s",
        "publisher": "Human Kinetics",
        "category": "Tactics",
        "intro": (
            "Modern Tennis Doubles is the USTA's contemporary doubles manual, written in the era of the Bryan brothers and "
            "before the rise of the modern specialist doubles teams. It covers formations, poaches, switches, and the Australian "
            "formations in great detail, with video stills from pro matches.\n\n"
            "The book's strength is its tactical specificity. It does not just describe what to do; it shows the patterns "
            "that professional pairs actually use and analyzes the percentages.\n\n"
            "Why it's in the vault: Doubles tactics evolve slowly but the modern game's I-formation and one-up-one-back "
            "patterns are best understood through this book."
        ),
    },
    {
        "id": "More_instant_tennis_lessons",
        "title": "More Instant Tennis Lessons",
        "author": "USTA",
        "year": "1997",
        "publisher": "Human Kinetics",
        "category": "Beginner",
        "intro": (
            "More Instant Tennis Lessons is the sequel to the USTA's popular Instant Tennis Lessons, covering topics the first "
            "book didn't have room for — including return of serve, the lob, and the high-volley. The format is the same: "
            "self-contained lessons that can be done in 30-60 minutes.\n\n"
            "Why it's in the vault: Many of Henry's adult readers ask what to read after they've finished Instant Tennis Lessons; "
            "this is the obvious follow-up."
        ),
    },
    {
        "id": "Nick_Bollettieri's_Junior_tennis",
        "title": "Nick Bollettieri's Junior Tennis",
        "author": "Nick Bollettieri",
        "year": "1995",
        "publisher": "Human Kinetics",
        "category": "Coaching",
        "intro": (
            "Nick Bollettieri's Junior Tennis is the Bollettieri academy's official guide to its junior-development philosophy. "
            "It is more focused on player development than the general Handbook: chapters on selecting talent, working with "
            "parents, college scholarship pathways, and the day-to-day life of a junior player at a tennis academy.\n\n"
            "The book's tone is sometimes controversial — Bollettieri is unapologetic about his high-volume, early-specialization "
            "approach. But it is also one of the most honest accounts of how the modern junior tennis industry actually works.\n\n"
            "Why it's in the vault: When discussing the pros and cons of early specialization with parents, Henry uses this "
            "book as the primary reference for the 'academy' approach."
        ),
    },
    {
        "id": "Official_encyclopedia_of_tennis",
        "title": "Official Encyclopedia of Tennis",
        "author": "USTA",
        "year": "1979 (revised)",
        "publisher": "Harper & Row",
        "category": "Reference",
        "intro": (
            "The Official Encyclopedia of Tennis is the USTA's historical and reference work, published in multiple editions "
            "since the 1970s. It is the closest thing to an official record of professional and amateur tennis in the United "
            "States: tournament results, player biographies, records, and the institutional history of the game.\n\n"
            "While not an instruction book, it is invaluable for tennis historians and journalists. Henry uses it constantly "
            "when researching older players and tournaments.\n\n"
            "Why it's in the vault: For any historical question — 'when did the tiebreak get introduced?' 'who was the first "
            "left-handed US Open champion?' — the encyclopedia usually has the answer."
        ),
    },
    {
        "id": "Pattern_play_tennis",
        "title": "Pattern Play Tennis",
        "author": "R. Spencer Brent",
        "year": "1974",
        "publisher": "Doubleday",
        "category": "Tactics",
        "intro": (
            "R. Spencer Brent's Pattern Play Tennis is one of the earliest tactical tennis books to use the term 'patterns' — "
            "structured point-construction sequences that the player executes in advance, with tactical choices built in. The book "
            "predates modern tactical analysis but in many ways foreshadows it.\n\n"
            "The illustrations are by George Janes, whose clean line drawings were a staple of 1970s tennis books. The tactical "
            "language is clear and the patterns — serve-and-volley, baseline rally, approach-and-lob — are still recognizable today.\n\n"
            "Why it's in the vault: This is a primary source on 1970s tactical thinking, and Henry uses it to teach how patterns "
            "have (and haven't) changed since then."
        ),
    },
    {
        "id": "Peaking_through_tennis__a_mindbody_guide_to_peak_performances",
        "title": "Peaking Through Tennis: A Mind-Body Guide to Peak Performances",
        "author": "Donald Burkett",
        "year": "1979",
        "publisher": "Sunstone Press",
        "category": "Mental",
        "intro": (
            "Donald Burkett's Peaking Through Tennis is one of the first tennis books to seriously explore mind-body integration. "
            "Written in the era when yoga and meditation were entering mainstream athletics, it draws from sports psychology, "
            "Eastern philosophy, and Burkett's own experience coaching tournament players.\n\n"
            "The book covers visualization, breathing, focus rituals, and the relationship between physical relaxation and "
            "explosive performance. Some of the ideas are now mainstream (the pre-serve routine, for example); others remain "
            "unusual.\n\n"
            "Why it's in the vault: For the player interested in mental-game work beyond conventional sport psychology, this "
            "book offers a different perspective that many have found useful."
        ),
    },
    {
        "id": "Play_Better_Tennis_in_Two_Hours__Simplify_-_Oscar_Wegner",
        "title": "Play Better Tennis in Two Hours: Simplify",
        "author": "Oscar Wegner",
        "year": "2011",
        "publisher": "Wegner Tennis",
        "category": "Technique",
        "intro": (
            "Oscar Wegner is one of the most controversial tennis coaches of the modern era. His method — using video to teach "
            "modern strokes — has produced champions like Marcelo Rios, and his book Play Better Tennis in Two Hours is a "
            "distillation of his core ideas: stop telling players to take the racket back early; let the body lead the stroke; "
            "use the non-dominant hand to set the unit turn.\n\n"
            "The book is short, provocative, and very visual. It challenges many traditional coaching cues (e.g. 'turn the "
            "shoulder' or 'keep your eye on the ball') and replaces them with simpler, more biomechanically sound alternatives.\n\n"
            "Why it's in the vault: This book changed how many modern coaches teach the forehand. When Henry helps a player "
            "with chronic forehand problems, Wegner's approach is often part of the solution."
        ),
    },
    {
        "id": "Play_better_tennis",
        "title": "Play Better Tennis",
        "author": "Frank Conroy (editor)",
        "year": "1985",
        "publisher": "Knopf",
        "category": "Technique",
        "intro": (
            "Play Better Tennis is a multi-author collection edited by writer Frank Conroy, with contributions from major coaches "
            "and former players of the 1970s and 80s. Each chapter is a self-contained essay on a specific aspect of the game — "
            "the forehand by one author, the serve by another, and so on.\n\n"
            "The book reads like a collection of magazine articles, which is its strength and weakness. The variety of voices "
            "is refreshing, but there is no unified method.\n\n"
            "Why it's in the vault: The variety of voices makes this a useful reference for the coach who wants to see how "
            "different teachers approach the same stroke."
        ),
    },
    {
        "id": "Play_winning_tennis_with_perfect_fundamentals._Book_1",
        "title": "Play Winning Tennis with Perfect Fundamentals (Book 1)",
        "author": "USTA / Dennis van der Meer",
        "year": "1990s",
        "publisher": "Human Kinetics",
        "category": "Beginner",
        "intro": (
            "Play Winning Tennis with Perfect Fundamentals is the USTA's flagship beginner text — designed to be the first book "
            "a new player reads. The 'Book 1' designation implies a multi-volume curriculum; in practice, this is the only volume "
            "most players need.\n\n"
            "The book uses a methodical, repetition-based approach to building the basic strokes. Every chapter ends with a "
            "drill you can do at home or with a partner. The progression from grip to rally is slow and patient.\n\n"
            "Why it's in the vault: For the absolute beginner, this is Henry's default recommendation. The patient, repetitive "
            "approach works especially well with children and older beginners."
        ),
    },
    {
        "id": "Quick_Tennis",
        "title": "Quick Tennis",
        "author": "H. H. Lloyd and Chet Murphy",
        "year": "1993",
        "publisher": "Human Kinetics",
        "category": "Beginner",
        "intro": (
            "Quick Tennis is another 'Learn fast' book from the early 1990s, written by H. H. Lloyd (USTA) and Chet Murphy "
            "(longtime Berkeley coach). Its premise is that adults want to play tennis socially as quickly as possible, and the "
            "traditional junior-progression model is too slow for them.\n\n"
            "The book condenses the first six months of lessons into a weekend-friendly curriculum, with modified equipment and "
            "courts designed to make the early stages feel more like a real game.\n\n"
            "Why it's in the vault: This is the book Henry used to design his popular 'Tennis in 30 Days' course for adult "
            "beginners in Ho Chi Minh City."
        ),
    },
    {
        "id": "Release_Your_Kinetic_Chain__Exercises_For_the_Shoulder_to_Hand__Activating_Your_Arm's_Kinetic_Chain!",
        "title": "Release Your Kinetic Chain: Exercises for the Shoulder to Hand",
        "author": "Various (medical/rehab authors)",
        "year": "2010s",
        "publisher": "Independent",
        "category": "Fitness",
        "intro": (
            "Release Your Kinetic Chain is a shoulder-and-arm-focused rehabilitation and conditioning book, written for "
            "tennis players who have shoulder pain or are recovering from surgery. It uses the kinetic-chain model of the body "
            "to explain why shoulder problems often originate elsewhere — in the thoracic spine, the hip, or the foot.\n\n"
            "The exercise progressions are clear, well-illustrated, and conservative — this is a book written by people who "
            "treat shoulders for a living and are careful not to suggest anything risky.\n\n"
            "Why it's in the vault: Henry has many senior readers who suffer from shoulder or elbow problems. This is the "
            "book he recommends for the ones who want to keep playing through their recovery."
        ),
    },
    {
        "id": "Science_of_coaching_tennis",
        "title": "Science of Coaching Tennis",
        "author": "USTA / various authors",
        "year": "1990s",
        "publisher": "Human Kinetics",
        "category": "Coaching",
        "intro": (
            "Science of Coaching Tennis is the USTA's most academically rigorous coaching book. The contributing authors include "
            "sport scientists, biomechanists, and physician-coaches who bring a research-grounded perspective to coaching practice.\n\n"
            "Chapters cover motor learning, growth and development, conditioning, biomechanics of each stroke, and the science "
            "of decision-making under pressure. The book is dense but useful — every claim is referenced.\n\n"
            "Why it's in the vault: This is Henry's reference for any coaching claim that needs to be backed by scientific "
            "evidence rather than tradition."
        ),
    },
    {
        "id": "Serious_Tennis",
        "title": "Serious Tennis",
        "author": "USTA",
        "year": "1997",
        "publisher": "Human Kinetics",
        "category": "Technique",
        "intro": (
            "Serious Tennis is the USTA's intermediate-to-advanced book, written for the player who already knows the basics "
            "and wants to win matches at the club or tournament level. It covers stroke refinement, advanced tactics, and the "
            "physical and mental preparation that competitive play demands.\n\n"
            "The book is well-photographed and contains detailed sequences of professional players doing each stroke at competition "
            "speed. The tactical sections include specific patterns for different opponent types — lefty, big server, grinder, "
            "all-court attacker.\n\n"
            "Why it's in the vault: This is the right next step for the player who has outgrown Beginner Tennis and wants to "
            "compete seriously."
        ),
    },
    {
        "id": "Sports_illustrated_tennis",
        "title": "Sports Illustrated Tennis",
        "author": "John Feinstein and the Editors of Sports Illustrated",
        "year": "1988",
        "publisher": "Harper & Row",
        "category": "Technique",
        "intro": (
            "Sports Illustrated Tennis is a high-quality instructional book produced in partnership with Sports Illustrated. "
            "John Feinstein, the noted sportswriter, wrote the copy with editorial input from SI's tennis desk. The book covers "
            "every stroke and most tactical situations with a mix of action photography and annotated diagrams.\n\n"
            "The book is also notable for its section on the mental game, drawing on interviews with contemporary pros like "
            "Lendl, Evert, and Wilander.\n\n"
            "Why it's in the vault: For the recreational player who wants a single authoritative book with high production values, "
            "this remains a strong choice."
        ),
    },
    {
        "id": "Stan_Smith's_six_tennis_basics",
        "title": "Stan Smith's Six Tennis Basics",
        "author": "Stan Smith with the USTA",
        "year": "2000s",
        "publisher": "Human Kinetics",
        "category": "Technique",
        "intro": (
            "Stan Smith — the 1972 Wimbledon champion and longtime figurehead of adidas tennis — distilled his teaching into six "
            "basics. This book, produced in partnership with the USTA, presents those six fundamentals clearly and accessibly.\n\n"
            "The six basics cover the forehand, backhand, serve, volley, overhead, and the positioning between strokes. Each "
            "chapter is short, photographic, and ends with a clear practice drill.\n\n"
            "Why it's in the vault: For the intermediate player who feels like their game is scattered, this book is a useful "
            "exercise in returning to fundamentals."
        ),
    },
    {
        "id": "Stan_Smith's_winning_doubles",
        "title": "Stan Smith's Winning Doubles",
        "author": "Stan Smith",
        "year": "2000s",
        "publisher": "Human Kinetics",
        "category": "Tactics",
        "intro": (
            "Stan Smith's Winning Doubles is the doubles companion to his Six Tennis Basics book. Smith was a fine doubles player "
            "as well as a singles champion, and he brings his considerable competitive experience to the subject.\n\n"
            "The book covers formations, court positioning, communication, and the specific tactics of serving, returning, and "
            "playing the net in doubles. Smith's prose is direct and easy to apply.\n\n"
            "Why it's in the vault: Smith is one of the last great all-court players to write a serious doubles book. The book "
            "is particularly useful for the club-level doubles player."
        ),
    },
    {
        "id": "Teaching_Tennis_Volume_1_-_Martin_van_Daalen",
        "title": "Teaching Tennis (Volume 1)",
        "author": "Martin van Daalen",
        "year": "2000s",
        "publisher": "International Tennis Federation",
        "category": "Coaching",
        "intro": (
            "Martin van Daalen is one of the ITF's most respected coaching educators, and this two-volume set is the ITF's official "
            "coaching curriculum. Volume 1 covers the foundational level: working with beginners, the basic strokes, the format "
            "of group lessons, and the principles of motor learning as they apply to tennis.\n\n"
            "The book is international in scope and reflects coaching practice from many countries. It is more academic than the "
            "USTA's books but also more carefully grounded in research.\n\n"
            "Why it's in the vault: This is the book Henry uses to train new coaches at the Vietnam Tennis Federation. The "
            "ITF framework is recognized worldwide."
        ),
    },
    {
        "id": "Tennis",
        "title": "Tennis (general)",
        "author": "Paul Hutchins (foreword)",
        "year": "1970s-80s",
        "publisher": "Various (book was a reprint of multi-author compilations)",
        "category": "Technique",
        "intro": (
            "This title 'Tennis' is a catch-all for several editions of a multi-author compilation that circulated in the "
            "1970s and 80s. Each edition combined essays by leading players and coaches, with a foreword by Paul Hutchins "
            "(former British Davis Cup captain).\n\n"
            "The content overlaps significantly with other titles in this vault, but the historical value is high — Hutchins's "
            "introduction captures the British perspective on tennis during the amateur era, and the contributions from lesser-"
            "known coaches offer a different window into how the sport was taught.\n\n"
            "Why it's in the vault: For the British-history perspective on tennis, this is a useful primary source."
        ),
    },
    {
        "id": "Tennis Neurological Specialist Deep Research",
        "title": "Tennis Neurological Specialist: Deep Research Compilation",
        "author": "Dr. Brian Hainline and colleagues",
        "year": "2020s",
        "publisher": "Independent / medical journal compilation",
        "category": "Medicine",
        "intro": (
            "This is a compilation of recent research articles and clinical reports on tennis neurology — the medical specialty "
            "that deals with head injuries, concussion management, and neurological conditions in tennis players. It draws on "
            "research from the WTA, ATP, and academic medical centers.\n\n"
            "The book covers concussion protocols, return-to-play guidelines, heat illness, and the long-term neurological "
            "effects of professional tennis. It is medical-practitioner level, not lay-reader level.\n\n"
            "Why it's in the vault: For the small but growing field of tennis neurology, this is the single best compilation "
            "of contemporary research."
        ),
    },
    {
        "id": "Tennis,_a_professional_guide",
        "title": "Tennis: A Professional Guide",
        "author": "Wayne Britt and USTA",
        "year": "1990s",
        "publisher": "Human Kinetics",
        "category": "Coaching",
        "intro": (
            "Tennis: A Professional Guide is one of the USTA's books aimed at the working tennis professional — the club pro, the "
            "high-school coach, the academy director. It covers the business side (lessons, programs, pro-shop management) and "
            "the technical side (stroke mechanics, program design) in a single volume.\n\n"
            "Why it's in the vault: For coaches who want to understand the profession, this is the right starting point."
        ),
    },
    {
        "id": "Tennis,_beyond_the_inner_game",
        "title": "Tennis: Beyond the Inner Game",
        "author": "Timothy Gallwey and others",
        "year": "1977",
        "publisher": "Random House",
        "category": "Mental",
        "intro": (
            "Beyond the Inner Game is a multi-author follow-up to Timothy Gallwey's classic The Inner Game of Tennis. While "
            "Gallwey's original book is the more famous title, this collection extends his ideas with contributions from other "
            "sport psychologists, coaches, and players.\n\n"
            "The book is more varied and sometimes more technical than Gallwey's pure approach, but it preserves his core "
            "insight — that the opponent inside your head is usually harder to beat than the one across the net.\n\n"
            "Why it's in the vault: For coaches and players who already know Gallwey's work and want to extend the conversation, "
            "this is the natural next step."
        ),
    },
    {
        "id": "Tennis_2000",
        "title": "Tennis 2000",
        "author": "USTA / Dennis van der Meer",
        "year": "1990s",
        "publisher": "Human Kinetics",
        "category": "Technique",
        "intro": (
            "Tennis 2000 is the USTA's late-1990s book, designed to bring the game's instruction into the new millennium. It "
            "covers modern strokes (especially the open-stance forehand), modern equipment, and modern training methods.\n\n"
            "The book's distinctive contribution is its photography — high-speed sequences of contemporary pros at the moment "
            "of contact, captured with the latest video technology. The technique analysis is grounded in these stills.\n\n"
            "Why it's in the vault: This book bridges the gap between the older 1980s instruction and the modern game. It's "
            "Henry's go-to reference for explaining how the strokes evolved."
        ),
    },
    {
        "id": "Tennis_For_Dummies_2nd_Edition_-_Patrick_McEnroe",
        "title": "Tennis For Dummies (2nd Edition)",
        "author": "Patrick McEnroe",
        "year": "2009",
        "publisher": "Wiley",
        "category": "Beginner",
        "intro": (
            "Patrick McEnroe's Tennis For Dummies is one of the most widely-used beginner tennis books in the world. As the "
            "younger brother of John McEnroe, Patrick brought credibility from a long professional career (he won the 1993 "
            "French Open doubles title) and the ability to explain the game in approachable language.\n\n"
            "The book covers everything from choosing a racket to running an attack on match point. It uses the trademark "
            "Dummies format of clear sections, icon-based sidebars, and humour to make the material feel friendly.\n\n"
            "Why it's in the vault: For the complete beginner, this is the right first book. It's also an excellent reference "
            "for parents learning tennis alongside their children."
        ),
    },
    {
        "id": "Tennis_Fundamentals",
        "title": "Tennis Fundamentals (Sports Fundamentals Series)",
        "author": "USTA / Human Kinetics",
        "year": "2000s",
        "publisher": "Human Kinetics",
        "category": "Beginner",
        "intro": (
            "Tennis Fundamentals is part of the Sports Fundamentals Series from Human Kinetics — a uniform-format series covering "
            "many sports. The tennis volume uses the 'learn-by-doing' approach: every chapter ends with a clearly-defined drill "
            "you can do at home or with a partner.\n\n"
            "Why it's in the vault: For the absolute beginner who wants a methodical progression, this book is among the best "
            "of the many similar titles."
        ),
    },
    {
        "id": "Tennis_Fundamentals_-_Carol_Matsuzaki",
        "title": "Tennis Fundamentals (Carol Matsuzaki edition)",
        "author": "Carol Matsuzaki",
        "year": "2000s",
        "publisher": "Human Kinetics",
        "category": "Beginner",
        "intro": (
            "This is a parallel edition to the USTA's Tennis Fundamentals, written by Carol Matsuzaki. Matsuzaki was a longtime "
            "USTA coach and contributor to many of their publications.\n\n"
            "Why it's in the vault: For the same reason as the other Tennis Fundamentals — a different voice on the same core "
            "curriculum is useful for coaches and teachers."
        ),
    },
    {
        "id": "Tennis_Medicine_-_Di_giacomo",
        "title": "Tennis Medicine",
        "author": "Giovanni Di Giacomo, Todd S. Ellenbecker, and W. Ben Kibler (editors)",
        "year": "2018",
        "publisher": "Springer",
        "category": "Medicine",
        "intro": (
            "Tennis Medicine is the most comprehensive contemporary medical textbook for tennis. Edited by three of the leading "
            "figures in tennis sports medicine — orthopaedic surgeon Giovanni Di Giacomo, physical therapist Todd Ellenbecker, "
            "and orthopaedic surgeon W. Ben Kibler — it covers every major injury and medical condition that affects tennis "
            "players.\n\n"
            "The book is organized anatomically (shoulder, elbow, wrist, hip, knee, foot/ankle, spine) and within each section "
            "covers the most common pathologies, their diagnosis, conservative treatment, and surgical options. It also has "
            "chapters on special populations — youth, senior, and professional players.\n\n"
            "Why it's in the vault: For coaches working with injured players and for medical practitioners who treat tennis "
            "players, this is the definitive reference."
        ),
    },
    {
        "id": "Tennis_Science-Behind_Carla_Mooney",
        "title": "Tennis: The Science Behind the Sport",
        "author": "Carla Mooney",
        "year": "2014",
        "publisher": "Sports Illustrated Kids",
        "category": "Science",
        "intro": (
            "Tennis: The Science Behind the Sport is part of the Sports Illustrated Kids series, designed to introduce middle-"
            "school-aged readers to the science underlying their favorite sports. Carla Mooney brings clear writing and excellent "
            "illustrations to topics like the physics of the ball-racket interaction, the biomechanics of the serve, and the "
            "physiology of tennis endurance.\n\n"
            "Why it's in the vault: For the 10-14 age group who wants to understand the why behind the how, this is the right "
            "book. Henry uses it in his junior tennis+science outreach events."
        ),
    },
    {
        "id": "Tennis_Strokes_and_Tactics_to_Improve_Your_Game",
        "title": "Tennis Strokes and Tactics to Improve Your Game",
        "author": "USTA",
        "year": "1990s",
        "publisher": "Human Kinetics",
        "category": "Technique",
        "intro": (
            "Tennis Strokes and Tactics to Improve Your Game is a USTA handbook focused on stroke refinement and tactical "
            "patterns. It is organized by stroke (forehand, backhand, serve, volley, overhead, slice, lob) and within each "
            "chapter discusses both the mechanics and the tactical use of that stroke.\n\n"
            "Why it's in the vault: This is one of Henry's most-cited books when working with intermediate players. The "
            "stroke-by-stroke, tactic-by-tactic organization is easy to reference."
        ),
    },
    {
        "id": "Tennis__steps_to_success",
        "title": "Tennis: Steps to Success",
        "author": "Carol V. Wright and Brent S. Armstrong",
        "year": "1991",
        "publisher": "Human Kinetics",
        "category": "Beginner",
        "intro": (
            "Tennis: Steps to Success is part of the long-running 'Steps to Success' series from Human Kinetics — a uniform-"
            "format series used in physical education curricula nationwide. The tennis volume uses a progressive step system: "
            "each step builds on the previous one, with clear success criteria for each level.\n\n"
            "Why it's in the vault: For the absolute beginner who wants to track their progress in a measurable way, this book "
            "is excellent. The step-numbering makes it easy to know where you are."
        ),
    },
    {
        "id": "Tennis_and_the_mind",
        "title": "Tennis and the Mind",
        "author": "Robert J. Davis",
        "year": "1990s",
        "publisher": "Betterway Publications",
        "category": "Mental",
        "intro": (
            "Tennis and the Mind is a sport-psychology book by Robert Davis (also author of Doubles Strategy). It addresses the "
            "psychology of competition at all levels — from club to professional — and emphasizes the practical tools a player "
            "can use to manage nerves, focus, and self-talk.\n\n"
            "Why it's in the vault: For coaches and players who want to work on the mental game, this is one of the most "
            "practical older books."
        ),
    },
    {
        "id": "Tennis_beyond_big_shots",
        "title": "Tennis Beyond Big Shots",
        "author": "USTA",
        "year": "1990s",
        "publisher": "Human Kinetics",
        "category": "Mental",
        "intro": (
            "Tennis Beyond Big Shots argues — counter to much of the modern game's emphasis on big serves and bigger forehands — "
            "that most matches are won by players who make few errors rather than players who hit spectacular winners. The book "
            "is a celebration of percentage tennis.\n\n"
            "Why it's in the vault: For the player who keeps trying to hit winners and keeps losing, this book is a useful "
            "course correction."
        ),
    },
    {
        "id": "Tennis_course",
        "title": "Tennis Course (Volume 2: Teaching and Training)",
        "author": "USTA",
        "year": "1990s",
        "publisher": "Human Kinetics",
        "category": "Coaching",
        "intro": (
            "Tennis Course Volume 2 is the USTA's coaching-focused curriculum, supplementing the player-facing Volume 1. It "
            "covers lesson planning, practice organization, the teaching of each stroke to different age groups, and the "
            "evaluation of progress.\n\n"
            "Why it's in the vault: For working coaches, this is one of the most practically useful USTA books."
        ),
    },
    {
        "id": "Tennis_doubles__tactics_and_formations",
        "title": "Tennis Doubles: Tactics and Formations",
        "author": "USTA / various",
        "year": "1990s",
        "publisher": "Human Kinetics",
        "category": "Tactics",
        "intro": (
            "Tennis Doubles: Tactics and Formations is one of the USTA's dedicated doubles books, covering the major formations "
            "(one-up-one-back, two-back, I-formation, Australian) and the tactical patterns each is designed to enable.\n\n"
            "Why it's in the vault: For the doubles player who wants to understand formations, this book is the cleanest "
            "introduction."
        ),
    },
    {
        "id": "Tennis_for_the_player,_teacher,_and_coach",
        "title": "Tennis for the Player, Teacher, and Coach",
        "author": "Chet Murphy",
        "year": "1979",
        "publisher": "Lippincott",
        "category": "Coaching",
        "intro": (
            "Chet Murphy coached tennis at the University of California, Berkeley for decades and was one of the most respected "
            "American coaches of the late 20th century. Tennis for the Player, Teacher, and Coach is his masterwork, organized "
            "to serve three audiences simultaneously — the player, the teacher, and the coach — with each chapter offering "
            "perspectives for all three.\n\n"
            "Why it's in the vault: Murphy is one of Henry's favourite coaching voices. The book is the right blend of "
            "practical and principled."
        ),
    },
    {
        "id": "Tennis_handbook",
        "title": "Tennis Handbook",
        "author": "USTA",
        "year": "1990s",
        "publisher": "Human Kinetics",
        "category": "Beginner",
        "intro": (
            "Tennis Handbook is a USTA companion book to many of their teaching texts — a quick-reference format with practical "
            "tips and diagrams. It is small enough to carry to the court.\n\n"
            "Why it's in the vault: For the player who wants something portable, this is the right size."
        ),
    },
    {
        "id": "Tennis_skills_&_drills",
        "title": "Tennis Skills & Drills",
        "author": "USTA",
        "year": "1990s",
        "publisher": "Human Kinetics",
        "category": "Coaching",
        "intro": (
            "Tennis Skills & Drills is one of the USTA's most popular coaching books, organized entirely around drills. Each "
            "drill has a clear purpose, instructions, common errors, and progression tips.\n\n"
            "Why it's in the vault: For coaches building a practice plan, this is the most practical single book — over 80 "
            "drills organized by skill area."
        ),
    },
    {
        "id": "Tennis_strokes_and_strategies",
        "title": "Tennis Strokes and Strategies",
        "author": "USTA / various",
        "year": "1990s",
        "publisher": "Human Kinetics",
        "category": "Tactics",
        "intro": (
            "Tennis Strokes and Strategies is a tactical companion to the USTA's stroke-mechanics books. It focuses on how "
            "strokes are used in matches — patterns, point construction, and the percentages that make some patterns more "
            "likely to win than others.\n\n"
            "Why it's in the vault: For the coach or player who has the strokes and wants to use them tactically, this is "
            "the right book."
        ),
    },
    {
        "id": "Tennis_tactics__singles_and_doubles",
        "title": "Tennis Tactics: Singles and Doubles",
        "author": "USTA / Josh Purtle",
        "year": "1990s",
        "publisher": "Human Kinetics",
        "category": "Tactics",
        "intro": (
            "Tennis Tactics: Singles and Doubles is one of the most focused tactical books in the USTA catalogue. It treats "
            "tactics as a separate discipline and provides specific patterns for both singles and doubles.\n\n"
            "Why it's in the vault: For the coach who wants to teach tactics as a distinct skill, this book provides the "
            "framework."
        ),
    },
    {
        "id": "Tennis_weaknesses_&_remedies",
        "title": "Tennis Weaknesses & Remedies",
        "author": "USTA",
        "year": "1990s",
        "publisher": "Human Kinetics",
        "category": "Technique",
        "intro": (
            "Tennis Weaknesses & Remedies is a USTA troubleshooting book — what to do when specific strokes aren't working. "
            "Each chapter addresses a common weakness (e.g. 'my forehand breaks down in matches', 'my second serve gets attacked') "
            "and proposes a series of remedies.\n\n"
            "Why it's in the vault: For the player stuck in a plateau, this book is structured exactly to their problem."
        ),
    },
    {
        "id": "Tennis_without_lessons",
        "title": "Tennis Without Lessons",
        "author": "USTA",
        "year": "1990s",
        "publisher": "Human Kinetics",
        "category": "Beginner",
        "intro": (
            "Tennis Without Lessons is one of the USTA's outreach titles for players who want to learn on their own, without "
            "a coach. It uses self-paced drills and progression charts to help the reader develop independently.\n\n"
            "Why it's in the vault: For the self-directed learner — and many of Henry's readers are exactly this — this book "
            "is the right one."
        ),
    },
    {
        "id": "The tennis handbook",
        "title": "The Tennis Handbook",
        "author": "Pam Shriver and others",
        "year": "2000s",
        "publisher": "Human Kinetics",
        "category": "Technique",
        "intro": (
            "The Tennis Handbook is a contemporary instructional book featuring Pam Shriver and other modern voices. It covers "
            "the basic strokes, equipment, fitness, and the mental game in a friendly, photo-rich format.\n\n"
            "Why it's in the vault: Pam Shriver's voice brings a fresh perspective to the canonical USTA content."
        ),
    },
    {
        "id": "The_Handbook_Of_Tennis_-_Paul_Douglas",
        "title": "The Handbook of Tennis",
        "author": "Paul Douglas",
        "year": "1980s",
        "publisher": "Dorling Kindersley",
        "category": "Technique",
        "intro": (
            "Paul Douglas's The Handbook of Tennis is part of the classic Dorling Kindersley illustrated series — oversized "
            "books with high-quality photographs and detailed diagrams. It covers the game's history, the strokes, the rules, "
            "and the equipment with DK's trademark visual clarity.\n\n"
            "Why it's in the vault: For the visual learner, this is one of the best tennis books ever produced. The "
            "photographs and diagrams are exceptional."
        ),
    },
    {
        "id": "The_Mental_Emotional_Tennis_Work_Book-Blun_-_Frank_Giampaolo",
        "title": "The Mental Emotional Tennis Workbook",
        "author": "Frank Giampaolo",
        "year": "2000s",
        "publisher": "Westside Publications",
        "category": "Mental",
        "intro": (
            "Frank Giampaolo is one of the most respected mental-game coaches in American tennis, and The Mental Emotional "
            "Tennis Workbook is his signature work. Written in a workbook format with exercises and self-assessment tools, "
            "it covers every aspect of competitive psychology.\n\n"
            "Why it's in the vault: For the player who wants to do structured mental-game work rather than just read about "
            "it, the workbook format is uniquely useful."
        ),
    },
    {
        "id": "The_Tennis_King_Equation",
        "title": "The Tennis King Equation",
        "author": "Independent author",
        "year": "2010s",
        "publisher": "Self-published",
        "category": "Mental",
        "intro": (
            "The Tennis King Equation is one of the more recent independent publications, offering a motivational and "
            "mental-game framework. The 'equation' of the title is a model for combining technique, fitness, and mental "
            "toughness into a winning formula.\n\n"
            "Why it's in the vault: For the recreational player who wants a motivational book more than a technical one, "
            "this is a useful recent option."
        ),
    },
    {
        "id": "The_art_of_doubles__winning_tennis_strategies_&_drills",
        "title": "The Art of Doubles: Winning Tennis Strategies & Drills",
        "author": "Pat Blaskower",
        "year": "2007",
        "publisher": "Tennis Welcome Publishing",
        "category": "Tactics",
        "intro": (
            "Pat Blaskower's The Art of Doubles is one of the most respected modern doubles books. Blaskower played "
            "competitively for years before becoming a coach, and she brings both perspectives to the book.\n\n"
            "The book covers formations, poaching, communication, and the doubles-specific drills that build chemistry. "
            "Her chapter on 'winning doubles strategy' is widely quoted.\n\n"
            "Why it's in the vault: This is the right modern doubles book. Henry recommends it to every doubles team he coaches."
        ),
    },
    {
        "id": "The_biomechanics_of_tennis__body_movement_studies_with_case_histories",
        "title": "The Biomechanics of Tennis: Body Movement Studies with Case Histories",
        "author": "Various academic authors",
        "year": "1980s-90s",
        "publisher": "Academic press",
        "category": "Science",
        "intro": (
            "The Biomechanics of Tennis is one of the few academic books dedicated entirely to tennis biomechanics. It collects "
            "research papers on the kinematics and kinetics of tennis strokes, with case studies of professional players.\n\n"
            "Why it's in the vault: For coaches who want to ground their technique work in published biomechanics research, "
            "this is one of the few sources."
        ),
    },
    {
        "id": "The_family_tennis_book",
        "title": "The Family Tennis Book",
        "author": "USTA / various",
        "year": "1990s",
        "publisher": "Human Kinetics",
        "category": "Family",
        "intro": (
            "The Family Tennis Book is the USTA's title for parents and families who want to play tennis together. It covers "
            "everything from how to introduce a 4-year-old to the sport, to how to organize a family tournament, to how to "
            "find a coach for a gifted child.\n\n"
            "Why it's in the vault: For parents, this is the right starting book."
        ),
    },
    {
        "id": "The_game_of_doubles_in_tennis",
        "title": "The Game of Doubles in Tennis",
        "author": "Bill Talbert and Bruce Olde",
        "year": "1976",
        "publisher": "Lippincott",
        "category": "Tactics",
        "intro": (
            "Bill Talbert was one of the greatest American doubles players of the pre-Open era, winning five US National "
            "Doubles titles. The Game of Doubles in Tennis, written with Bruce Olde, is his treatise on the discipline.\n\n"
            "Talbert writes with the authority of a man who played at the highest level for over two decades, and his tactical "
            "wisdom remains relevant today. The book covers doubles history, partner selection, formations, and the specific "
            "patterns of professional doubles.\n\n"
            "Why it's in the vault: For the serious doubles player, Talbert's voice is essential. He represents the 'lost' "
            "American doubles tradition."
        ),
    },
    {
        "id": "The_mental_ADvantage__developing_your_psychological_skills_in_tennis",
        "title": "The Mental Advantage: Developing Your Psychological Skills in Tennis",
        "author": "Robert J. Schinke",
        "year": "1990s",
        "publisher": "Human Kinetics",
        "category": "Mental",
        "intro": (
            "Robert Schinke is one of the most academically credible sport-psychology authors in tennis. The Mental Advantage "
            "is his textbook — a comprehensive treatment of the psychology of competitive tennis grounded in research but "
            "written for coaches and players.\n\n"
            "Why it's in the vault: For coaches who want to teach the mental game with academic rigor, this is the right book."
        ),
    },
    {
        "id": "The_tennis_drill_book",
        "title": "The Tennis Drill Book",
        "author": "USTA / various",
        "year": "1990s",
        "publisher": "Human Kinetics",
        "category": "Coaching",
        "intro": (
            "The Tennis Drill Book is one of the USTA's most-used coaching resources — over 100 drills organized by skill area "
            "with clear instructions, common errors, and progressions.\n\n"
            "Why it's in the vault: For the coach building practice plans, this is the right first book to own."
        ),
    },
    {
        "id": "The_ultimate_tennis_book",
        "title": "The Ultimate Tennis Book",
        "author": "Various",
        "year": "1990s",
        "publisher": "Dorling Kindersley",
        "category": "Reference",
        "intro": (
            "The Ultimate Tennis Book is a Dorling Kindersley coffee-table volume — large format, lavish photography, "
            "covering the history of tennis, the great players, the great matches, and the modern game.\n\n"
            "Why it's in the vault: For the visual reference and the historical content, this is a beautiful book."
        ),
    },
    {
        "id": "The_young_tennis_player",
        "title": "The Young Tennis Player",
        "author": "USTA / various",
        "year": "1990s",
        "publisher": "Human Kinetics",
        "category": "Junior",
        "intro": (
            "The Young Tennis Player is the USTA's title for the under-14 player, written in an engaging, age-appropriate voice. "
            "It uses illustrations and games to introduce tennis concepts.\n\n"
            "Why it's in the vault: For the child reader aged 8-14, this is the right book to give as a gift or use in a "
            "school program."
        ),
    },
    {
        "id": "Think to Win",
        "title": "Think to Win",
        "author": "USTA / various",
        "year": "1990s",
        "publisher": "Human Kinetics",
        "category": "Mental",
        "intro": (
            "Think to Win is the USTA's title for the tactical and strategic side of the game — the 'thinking' part of tennis. "
            "It covers pattern recognition, point construction, and the percentage decisions that win close matches.\n\n"
            "Why it's in the vault: For the player who wants to play smarter, this is the right book."
        ),
    },
    {
        "id": "Top_coach_tennis",
        "title": "Top Coach Tennis",
        "author": "Mark Cox (foreword) and various",
        "year": "1980s",
        "publisher": "British tennis publications",
        "category": "Coaching",
        "intro": (
            "Top Coach Tennis is a British title with contributions from many leading coaches of the era. Mark Cox (former "
            "British Davis Cup player) wrote the foreword. The book is methodologically rich, drawing on British coaching tradition.\n\n"
            "Why it's in the vault: For the British voice on tennis coaching, this is a useful primary source."
        ),
    },
    {
        "id": "Topspin_to_better_tennis",
        "title": "Topspin to Better Tennis",
        "author": "USTA / various",
        "year": "1990s",
        "publisher": "Human Kinetics",
        "category": "Technique",
        "intro": (
            "Topspin to Better Tennis focuses on one of the most important shots in modern tennis — the topspin forehand and "
            "the role of topspin in point construction. It is one of the USTA's most useful single-shot books.\n\n"
            "Why it's in the vault: For the player whose forehand needs more topspin, this book is the right focused treatment."
        ),
    },
    {
        "id": "Total_health_tennis__a_lifestyle_approach",
        "title": "Total Health Tennis: A Lifestyle Approach",
        "author": "USTA / various",
        "year": "1990s",
        "publisher": "Human Kinetics",
        "category": "Fitness",
        "intro": (
            "Total Health Tennis: A Lifestyle Approach is the USTA's fitness-and-lifestyle book, treating tennis as part of "
            "an overall healthy life. It covers conditioning, nutrition, injury prevention, and the mental aspects of "
            "maintaining a long tennis-playing career.\n\n"
            "Why it's in the vault: For the senior player or the player recovering from injury, the lifestyle approach is "
            "the right framing."
        ),
    },
    {
        "id": "USA_tennis_course",
        "title": "USA Tennis Course",
        "author": "USTA",
        "year": "1990s",
        "publisher": "Human Kinetics",
        "category": "Beginner",
        "intro": (
            "USA Tennis Course is the USTA's flagship beginner program in book form, used in conjunction with their on-court "
            "group lessons. It is friendly, methodical, and well-illustrated.\n\n"
            "Why it's in the vault: For the absolute beginner in the USTA's beginner program, this is the right book."
        ),
    },
    {
        "id": "Ultimate_tennis",
        "title": "Ultimate Tennis",
        "author": "USTA / various",
        "year": "1990s",
        "publisher": "Human Kinetics",
        "category": "Technique",
        "intro": (
            "Ultimate Tennis is one of the USTA's comprehensive titles — covering technique, tactics, fitness, and mental "
            "game in a single volume. It is often used as the textbook for the USTA's intermediate certification.\n\n"
            "Why it's in the vault: For the intermediate player who wants one comprehensive book, this is the right one."
        ),
    },
    {
        "id": "Vic_Braden's_Tennis_for_the_future",
        "title": "Vic Braden's Tennis for the Future",
        "author": "Vic Braden with Robert J. Ferrigno",
        "year": "1977",
        "publisher": "Atheneum",
        "category": "Technique",
        "intro": (
            "Vic Braden was one of the most respected American coaches of the 20th century — a UCLA-trained psychologist, "
            "a renowned teacher, and a beloved TV commentator. Tennis for the Future is one of his signature works, written "
            "with the optimism of its title.\n\n"
            "Braden's distinctive contribution was his use of video and humour in coaching — both are evident in this book. "
            "His chapter on the '70% rule' (hit the ball at 70% of maximum power to maximize consistency) became one of the "
            "most-cited pieces of tennis wisdom of all time.\n\n"
            "Why it's in the vault: Braden is one of Henry's most-quoted coaches. The '70% rule' has its own entry in "
            "the Tennis-WIKI because of how widely it's referenced."
        ),
    },
    {
        "id": "Vic_Braden's_laugh_and_win_at_doubles",
        "title": "Vic Braden's Laugh and Win at Doubles",
        "author": "Vic Braden",
        "year": "1981",
        "publisher": "Atheneum",
        "category": "Tactics",
        "intro": (
            "Vic Braden's Laugh and Win at Doubles is the doubles companion to his other books. It covers the doubles-specific "
            "tactics and the team-chemistry aspects that determine doubles success.\n\n"
            "Why it's in the vault: For the recreational doubles team, Braden's friendly tone and practical advice is ideal."
        ),
    },
    {
        "id": "Vic_Braden's_mental_tennis__how_to_psych_yourself_to_a_winning_game",
        "title": "Vic Braden's Mental Tennis: How to Psych Yourself to a Winning Game",
        "author": "Vic Braden",
        "year": "1982",
        "publisher": "Atheneum",
        "category": "Mental",
        "intro": (
            "Vic Braden's Mental Tennis is one of the classics of tennis sport psychology. Written with Braden's trademark "
            "humour and warmth, it covers the mental-game topics that every competitive player faces: nerves, momentum, focus, "
            "and the pressure of close matches.\n\n"
            "Why it's in the vault: For any player serious about the mental game, Braden's book is essential reading. Henry "
            "frequently references it in his coaching."
        ),
    },
    {
        "id": "Visual_tennis__mental_imagery_and_the_quest_for_the_winning_edge",
        "title": "Visual Tennis: Mental Imagery and the Quest for the Winning Edge",
        "author": "Richard Y. Moody and various",
        "year": "1990s",
        "publisher": "Sports Imagery Publications",
        "category": "Mental",
        "intro": (
            "Visual Tennis is one of the few books entirely dedicated to mental imagery in tennis. Drawing on sports-psychology "
            "research, it covers how to use visualization to improve stroke mechanics, tactical decision-making, and match "
            "preparation.\n\n"
            "Why it's in the vault: For the player who wants to add visualization to their mental-game toolkit, this is "
            "the most focused treatment available."
        ),
    },
    {
        "id": "Winning_doubles",
        "title": "Winning Doubles",
        "author": "USTA / various",
        "year": "1990s",
        "publisher": "Human Kinetics",
        "category": "Tactics",
        "intro": (
            "Winning Doubles is one of the USTA's tactical doubles books, covering the major formations and the patterns "
            "that win at the club and tournament level.\n\n"
            "Why it's in the vault: For the doubles player who wants a tactical reference, this is the right book."
        ),
    },
    {
        "id": "Winning_tennis",
        "title": "Winning Tennis",
        "author": "USTA / various",
        "year": "1990s",
        "publisher": "Human Kinetics",
        "category": "Tactics",
        "intro": (
            "Winning Tennis is the USTA's tactical handbook for singles play. It covers pattern recognition, point construction, "
            "and the percentage decisions that separate winners from losers.\n\n"
            "Why it's in the vault: For the singles player who has the strokes and wants to use them tactically, this is "
            "the right book."
        ),
    },
    {
        "id": "Winning_tennis__complete_guide_for_coaches_and_advanced_players",
        "title": "Winning Tennis: Complete Guide for Coaches and Advanced Players",
        "author": "Steve Schuyler",
        "year": "2000s",
        "publisher": "Human Kinetics",
        "category": "Technique",
        "intro": (
            "Steve Schuyler was a longtime college coach (Yale, Dartmouth, Trinity) and a respected teaching pro. Winning Tennis "
            "is his comprehensive guide for the advanced coach and player.\n\n"
            "The book covers advanced technique, the tactical patterns of high-level play, and the coaching methods that "
            "produce competitive players. Schuyler writes with the authority of someone who coached for decades.\n\n"
            "Why it's in the vault: For the advanced coach or ambitious player, Schuyler's voice is essential."
        ),
    },
    {
        "id": "Winning_tennis_doubles",
        "title": "Winning Tennis Doubles",
        "author": "USTA / various",
        "year": "1990s",
        "publisher": "Human Kinetics",
        "category": "Tactics",
        "intro": (
            "Winning Tennis Doubles is the USTA's tactical doubles book, covering formations and patterns. It is a useful "
            "supplement to other doubles books in this collection.\n\n"
            "Why it's in the vault: For the doubles player who wants multiple perspectives on the same topic."
        ),
    },
    {
        "id": "Zen_tennis__eastern_wisdom_for_western_sport",
        "title": "Zen Tennis: Eastern Wisdom for Western Sport",
        "author": "Cynthia Whitney",
        "year": "1987",
        "publisher": "Japan Publications",
        "category": "Philosophy",
        "intro": (
            "Zen Tennis is one of the more unusual books in the vault — a blend of Zen philosophy and practical tennis "
            "coaching. Cynthia Whitney draws on her years of playing tennis in Japan and her study of Zen meditation to "
            "propose a different relationship with the game.\n\n"
            "The book covers breathing, presence, and the concept of 'mushin' (no-mind) in tennis. It is not a how-to "
            "manual, but it is a useful complement to the more mechanical books.\n\n"
            "Why it's in the vault: For the player interested in the philosophical and meditative side of tennis, this is "
            "the right book. It is also useful for coaches who want to broaden their perspective."
        ),
    },
]


def main():
    out = Path('docs-source/books-index.json')
    out.parent.mkdir(parents=True, exist_ok=True)

    by_id = {b['id']: b for b in BOOKS}
    print(f'Books with intros: {len(BOOKS)}')

    out.write_text(json.dumps(BOOKS, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Wrote {out}')

    # Verify all 97 indexed books have intros
    manifest = json.loads(Path('docs-source/_manifest.json').read_text(encoding='utf-8'))
    from collections import defaultdict
    by_book = defaultdict(int)
    for c in manifest['chunks']:
        if c['section'] == 'books':
            by_book[c['title']] += 1

    print(f'\\nIndexed books: {len(by_book)}')
    missing = [t for t in by_book if t not in by_id]
    if missing:
        print(f'Missing intros for: {missing}')
    else:
        print('All indexed books have intros.')


if __name__ == '__main__':
    main()