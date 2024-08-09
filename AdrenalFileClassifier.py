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

import glob
import re
from dataclasses import dataclass
from os import path
from typing import List, Tuple

from TextNegationClassifier import TextNegationClassifier


@dataclass
class Measurement:
    matched_text: str
    sizes_mm: List[float]
    start_index: int
    end_index: int

    @staticmethod
    def create_from_text(text: str) -> List['Measurement']:
        # Regular expression pattern to match centimeter, centimeters, millimeter, millimeters,
        # cm, mm, and their numerical representations
        pattern = r'((\d+(?:\.\s*\d+)?)?(?:\s*(?:[xX-]|and)\s*)?(\d+(?:\.\s*\d+)?)\s*(cm|mm|centimeter|centimeters|millimeter|millimeters|cm\s|mm\s))\b'

        # Find all matches in the text
        matches = re.finditer(pattern, text)

        measurements = []
        for match in matches:
            sizes_mm = []
            matched_text = match.group(0)
            if match.group(2):
                sizes_mm.append(float(match.group(2).replace(' ', '')))

            sizes_mm.append(float(match.group(3).replace(' ', '')))
            unit = match.group(4)
            if unit in ["cm", "centimeter", "centimeters"]:
               for i in range(len(sizes_mm)):
                   sizes_mm[i] = sizes_mm[i] * 10
            start_index = match.start()
            end_index = match.end()

            measurement = Measurement(matched_text, sizes_mm, start_index, end_index)
            measurements.append(measurement)

        return measurements

    def debug_str(self, prefix) -> str:
        debug_str = f'{prefix}Measurement: {self.matched_text} [{self.start_index}:{self.end_index}] MM: {self.sizes_mm}'
        return debug_str

    def __eq__(self, other):
        if not isinstance(other, Measurement):
            return False
        return (
                self.matched_text == other.matched_text
                and self.size_mm == other.size_mm
                and self.start_index == other.start_index
                and self.end_index == other.end_index
        )


@dataclass
class KeywordMatch:
    text: str
    start_index: int  # this is in the section text
    end_index: int  # this is in the section text

    def debug_str(self, prefix: str):
        debug_str = f'{prefix}KeywordMatch: {self.text} [{self.start_index}:{self.end_index}]'
        return debug_str

    def __eq__(self, other):
        if not isinstance(other, KeywordMatch):
            return False
        retVal = (
                self.text == other.text
                and self.start_index == other.start_index
                and self.end_index == other.end_index
        )
        return retVal


@dataclass
class Section:
    file_path: str
    line_index: int
    title: str
    text: str
    start_index: int  # this is in the file text
    end_index: int  # this is in the file text
    keyword_matches: List[KeywordMatch] = None
    negated_matches: List[KeywordMatch] = None
    _measurements: List[Measurement] = None

    def extend_keyword_matches(self, keywords: List[str]) -> List[KeywordMatch]:
        if self.keyword_matches is None:
            self.keyword_matches = []
        keyword_pattern = '|'.join(keywords)
        pattern = r'\b(' + keyword_pattern + r')\b'
        matches = re.finditer(pattern, self.text, re.IGNORECASE)  # Case-insensitive search

        new_keyword_matches = []
        for match in matches:
            matched_text = match.group(0)
            start_index = match.start()
            end_index = match.end()
            new_keyword_matches.append(KeywordMatch(matched_text, start_index, end_index))

        self.keyword_matches.extend(new_keyword_matches)
        return new_keyword_matches

    @property
    def measurements(self) -> List[Measurement]:
        if self._measurements is None:
            self._measurements = Measurement.create_from_text(self.text)
        return self._measurements

    def debug_str(self, prefix: str):
        debug_lines = [f'Path: {self.file_path}[{self.start_index}:{self.end_index}]',
                       f'[{self.line_index}] - {self.title}']
        debug_lines.extend(self.text.splitlines(keepends=False))
        debug_lines.extend([km.debug_str('* ') for km in self.keyword_matches])
        debug_lines.extend([km.debug_str('* Negated ') for km in self.negated_matches])
        debug_lines.extend([m.debug_str('* ') for m in self.measurements])
        debug_str = prefix + f'\n{prefix}'.join(debug_lines)

        return debug_str

    def print_debug(self, prefix: str):
        print(self.debug_str(prefix))


class AdrenalFileClassifier:
    file_path: str = ''
    lines: List[str] = []
    line_indices: List[Tuple[int, int]] = []  # indices in the text for each line.
    all_section_matches: List[Tuple[int, str]]  # (line_index, section_title_string)
    all_adrenal_sections: List[Section]
    matched_adrenal_sections: List[Section]

    negationClassifier: TextNegationClassifier = TextNegationClassifier()

    ADRENAL_SECTION_TITLES = [
        "ADRENAL:",
        'ADRENALS:'
    ]

    def classify_text(self, text: str):
        self.lines = text.splitlines(keepends=True)

        self.line_indices = self._build_line_indices()
        self.all_section_matches = self._extract_section_title_matches()

        adrenal_section_positive_words = [w.lower() for w in self.ADRENAL_SECTION_TITLES]
        is_adrenal_section = self._func_gen_section_contains_a_positive_word(adrenal_section_positive_words)

        adrenal_sections = filter(is_adrenal_section, self.all_section_matches)
        self.all_adrenal_sections = [self._build_section_class(s) for s in adrenal_sections]

        self.matched_adrenal_sections = list(filter(self._classify_adrenal_section, self.all_adrenal_sections))

        return len(self.matched_adrenal_sections) > 0

    def classify_file(self, file_path: str):
        self.file_path = file_path
        file_text = self._read_file(file_path)
        return self.classify_text(file_text)

    def _read_file(self, file_path: str) -> str:
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read()
        except FileNotFoundError:
            print(f"File not found: {file_path}")
        except Exception as e:
            print(f"Error reading file {file_path}: {str(e)}")
        return text

    def _build_line_indices(self):
        text = ''.join(self.lines)
        line_indices = []
        current_index = 0

        for line in self.lines:
            start_index = text.find(line, current_index)
            end_index = start_index + len(line)
            line_indices.append((start_index, end_index))
            current_index = end_index

        return line_indices

    def _func_gen_section_contains_a_positive_word(self, positive_words):
        return lambda section_match: any(pword in section_match[1].lower() for pword in positive_words)

    def _extract_section_title_matches(self) -> List[Tuple[int, str]]:
        matches = []
        for line_index, line in enumerate(self.lines):
            match = re.match(r'^\s*([A-Z]+\s*:)', line)
            if match:
                group = match.group(1)
                matches.append((line_index, group))
        return matches

    def _get_section_text(self, specific_section):

        sindex = specific_section[0]
        if sindex + 1 > len(self.lines):
            nindex = len(self.lines)
        else:
            try:

                next_section_index = self.all_section_matches.index(specific_section) + 1
                if next_section_index < len(self.all_section_matches):
                    next_section = self.all_section_matches[next_section_index]
                    nindex = next_section[0]
                else:
                    nindex = len(self.lines)
            except ValueError:
                assert False, f"{specific_section} not found in section_matches."
            except IndexError:
                assert False, f"{specific_section} does not have a next section."
        section_text = ''.join(self.lines[sindex:nindex])
        return section_text.strip()

    def _build_section_class(self, section_match: Tuple[int, str]) -> Section:
        start_index = self.line_indices[section_match[0]][0]
        section_text = self._get_section_text(section_match)
        end_index = start_index + len(section_text)

        # assert ''.join(self.lines)[start_index:end_index] == section_text

        return Section(file_path=self.file_path,
                       line_index=section_match[0],
                       title=section_match[1],
                       start_index=start_index,
                       end_index=end_index,
                       text=section_text)

    def _classify_adrenal_section(self, section: Section):
        positive_words = [
            "adenoma",
            "lesion",
            "metastasis",
            "nodule",
            "nodularity",
            "mass",
            "measuring"
        ]
        section.extend_keyword_matches(positive_words)
        negated_keywords = []
        for kw in section.keyword_matches:
            if self.negationClassifier.is_negated_in_range(section.text, (kw.start_index, kw.end_index)):
                negated_keywords.append(kw)
        section.negated_matches = negated_keywords
        section.keyword_matches = list(filter(lambda kw: kw not in section.negated_matches, section.keyword_matches))

        if len(section.keyword_matches) > 0:
            if len(section.measurements) > 0:

                return any(size_mm >= 10 for size_mm in [s for sizes_mm in [m.sizes_mm for m in section.measurements] for s in sizes_mm])
            else:
                return True
        return False


def text_files_in_directory(directory_path: str) -> List[str]:
    text_files = []
    for file_path in glob.glob(path.join(directory_path, '*.txt')):
        if path.isfile(file_path):
            text_files.append(file_path)
    return text_files


if __name__ == '__main__':

    directory = r'C:\Users\oleaj\web\nlp\adernal-project\tmp_output\files'

    text_files = text_files_in_directory(directory)
    total_matches = 0
    positive_classifiers: List[AdrenalFileClassifier] = []
    for index, text_file in enumerate(text_files):
        classifier = AdrenalFileClassifier()

        if classifier.classify_file(text_file):
            positive_classifiers.append(classifier)

    for c in positive_classifiers:
        print(f'Matched Adrenal Sections ({len(c.matched_adrenal_sections)}):')
        [s.print_debug('  ') for s in c.matched_adrenal_sections]

    total_matches = sum([len(c.matched_adrenal_sections) for c in positive_classifiers])
    print(f'Total Matches: {total_matches}')
