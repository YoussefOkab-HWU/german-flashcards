#!/usr/bin/env python3
"""
Adds vocab_refs field to every sentence in sentences_100k/.

vocab_refs = list of vocabulary words (from DATA) whose lemma appears
as an exact token in the German sentence. Used by the app to filter
sentences by the user's mastered vocabulary.

Strategy: strip articles/reflexives from vocab words to get bare lemmas,
tokenise the German sentence, check set intersection.
This catches: infinitives, nominative nouns, predicate adjectives/adverbs.

Run: python3 enrich_sentences.py   (~10 seconds)
"""

import json, re
from pathlib import Path

BASE           = Path(__file__).parent
HTML_FILE      = BASE / "index.html"
SENTENCES_DIR  = BASE / "sentences_100k"

STRIP_RE = re.compile(
    r'^(der|die|das|ein|eine|einen|einem|eines|einer|kein|keine|sich)\s+',
    re.IGNORECASE
)

def get_lemma(word: str) -> str:
    """Strip article / reflexive pronoun to get bare lemma."""
    return STRIP_RE.sub("", word).strip().lower()

def tokenise(text: str) -> set[str]:
    return set(re.findall(r'[a-zäöüßA-ZÄÖÜ]+', text.lower()))

def load_vocab() -> dict:
    html = HTML_FILE.read_text(encoding="utf-8")
    m    = re.search(r"const DATA = (\{.*?\});", html, re.DOTALL)
    data = json.loads(m.group(1))
    return {
        w["german"]: cat
        for cat in ("verbs", "nouns", "adjectives", "adverbs")
        for w in data.get(cat, [])
    }

def main():
    vocab = load_vocab()
    print(f"Vocabulary: {len(vocab):,} words")

    # lemma (lowercase) → original vocab entry  (keep last if collision)
    lemma_to_word: dict[str, str] = {}
    for german in vocab:
        lemma = get_lemma(german)
        if lemma:
            lemma_to_word[lemma] = german

    print(f"Unique lemmas: {len(lemma_to_word):,}")

    chunk_files  = sorted(SENTENCES_DIR.glob("chunk_*.json"))
    total_sents  = 0
    total_refs   = 0
    zero_ref     = 0

    for chunk_path in chunk_files:
        sentences = json.loads(chunk_path.read_text(encoding="utf-8"))

        for s in sentences:
            tokens = tokenise(s["german"])
            refs   = [lemma_to_word[t] for t in tokens if t in lemma_to_word]
            s["vocab_refs"] = refs
            total_refs += len(refs)
            if not refs:
                zero_ref += 1
            total_sents += 1

        chunk_path.write_text(
            json.dumps(sentences, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

    avg = total_refs / total_sents if total_sents else 0
    print(f"Enriched:  {total_sents:,} sentences")
    print(f"Avg refs:  {avg:.1f} vocab words per sentence")
    print(f"Zero refs: {zero_ref:,} sentences ({zero_ref/total_sents*100:.1f}%)")
    print("Done.")

if __name__ == "__main__":
    main()
