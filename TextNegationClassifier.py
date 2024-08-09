# Copyright 2024 The University of Alabama at Birmingham
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import re
from typing import List, Optional, Tuple

import nltk

nltk.download("punkt")


class TextNegationClassifier:
    _sentence_cache = None
    _text_cache = None

    def __init__(self, negation_words: Optional[List[str]] = None):
        if negation_words is None:
            self.negation_words = ["not", "no", "without", "never", "none", "nobody", "nowhere", "nothing", "neither", "nor"]
        else:
            self.negation_words = negation_words

    def _get_nltk_sentences_for_text(self, text):
        if self._text_cache is not None and self._sentence_cache is not None and text == self._text_cache:
            sentences = self._sentence_cache
        else:
            sentences = nltk.sent_tokenize(text)
            self._text_cache = text
            self._sentence_cache = sentences
        return sentences

    def is_negated_in_range(self, text, target_text_range: Tuple[int, int]) -> bool:
        text = text.replace('\n', ' ')
        target_text = text[target_text_range[0]:target_text_range[1]]
        sentences = self._get_nltk_sentences_for_text(text)

        for sentence in sentences:
            if target_text in sentence and target_text_range[0] >= text.index(sentence) \
                    and target_text_range[1] <= (text.index(sentence) + len(sentence)):
                return self.is_negated(text, target_text)

        return False

    def is_negated(self, text: str, target_text: str) -> bool:
        text = text.replace('\n', ' ')
        sentences = self._get_nltk_sentences_for_text(text)
        for sentence in sentences:
            if self._has_negation_word(sentence) and self._has_target_text(sentence, target_text):
                return True
        return False

    def _has_negation_word(self, sentence) -> bool:
        sentence = sentence.lower()
        for word in self.negation_words:
            if re.search(rf'\b{word}\b', sentence):
                return True
        return False

    def _has_target_text(self, sentence, target_text: str) -> bool:
        sentence = sentence.lower()
        target_text = target_text.lower()
        return re.search(re.escape(target_text), sentence)
