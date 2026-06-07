from __future__ import annotations
import json
import random
import re
from pathlib import Path
from app.config import WORDS_DIR, QUOTES_FILE


class TextGenerator:
    def __init__(self):
        self._word_lists: dict[str, list[str]] = {}
        self._quotes: list[dict] = []
        self._load_data()

    def _load_data(self):
        if WORDS_DIR.exists():
            for json_file in WORDS_DIR.glob("*.json"):
                key = json_file.stem
                try:
                    with open(json_file, encoding="utf-8") as f:
                        self._word_lists[key] = json.load(f)
                except Exception:
                    pass

        if QUOTES_FILE.exists():
            try:
                with open(QUOTES_FILE, encoding="utf-8") as f:
                    self._quotes = json.load(f)
            except Exception:
                pass

    def generate_words(self, word_list: str = "english_200", count: int = 25,
                       punctuation: bool = False, numbers: bool = False) -> str:
        words = self._word_lists.get(word_list, self._word_lists.get("english_200", []))
        if not words:
            words = ["the", "quick", "brown", "fox", "jumps", "over", "lazy", "dog"]

        num_list = self._word_lists.get("numbers", ["0", "1", "2", "3", "4", "5"])

        selected: list[str] = []
        for _ in range(count):
            if numbers and num_list and random.random() < 0.15:
                selected.append(random.choice(num_list))
            else:
                selected.append(random.choice(words))

        if punctuation:
            selected = self._apply_punctuation(selected)

        return " ".join(selected)

    def _apply_punctuation(self, words: list[str]) -> list[str]:
        result = []
        i = 0
        while i < len(words):
            word = words[i]
            r = random.random()
            if r < 0.08 and i < len(words) - 1:
                word = word + ","
            elif r < 0.12 and i < len(words) - 1:
                word = word + "."
                if i + 1 < len(words):
                    words[i + 1] = words[i + 1].capitalize()
            elif r < 0.15:
                word = '"' + word
                if i + 2 < len(words):
                    words[i + 2] = words[i + 2] + '"'
            result.append(word)
            i += 1
        return result

    def generate_timed_words(self, word_list: str = "english_200",
                             punctuation: bool = False, numbers: bool = False):
        words = self._word_lists.get(word_list, self._word_lists.get("english_200", []))
        if not words:
            words = ["the", "quick", "brown", "fox"]
        while True:
            yield random.choice(words)

    def generate_quote(self) -> str:
        if not self._quotes:
            return "The quick brown fox jumps over the lazy dog."
        quote = random.choice(self._quotes)
        if isinstance(quote, dict):
            return quote.get("text", "")
        return str(quote)

    def generate_custom(self, text: str) -> str:
        cleaned = re.sub(r"\s+", " ", text.strip())
        return cleaned

    def generate_code(self, language: str = "python", line_count: int = 10) -> str:
        key = f"code_{language}"
        snippets = self._word_lists.get(key, [])
        if not snippets:
            snippets = ["def", "class", "import", "return", "for", "in", "range", "print"]
        lines = []
        indent = ""
        for _ in range(line_count):
            if random.random() < 0.3 and snippets:
                indent = "    " if random.random() < 0.5 else ""
            line = indent + " ".join(random.choices(snippets, k=random.randint(2, 5)))
            lines.append(line)
        return "\n".join(lines)

    def get_word_lists(self) -> list[str]:
        return list(self._word_lists.keys())
