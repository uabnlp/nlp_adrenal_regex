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
import sys
import traceback
from typing import Tuple, List


class ProcessingFileError(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class AdrenalRegex:

    def __init__(self):
        self.total_file_processed = 0
        self.no_adernal_section_count = 0
        self.adernal_normal_count = 0
        self.adernal_phrase_found_count = 0
        self.adernal_size_too_small_count = 0
        self.follow_up_count = 0
        self.current_filepath = ''

    def process_file(self, filepath) -> bool:
        self.current_filepath = filepath
        self.total_file_processed += 1
        content = ''
        with open(filepath, 'r') as f:
            content = f.read()

        process_result: bool = False
        try:
            process_result = self.process_content(content)
        except ProcessingFileError as error:
            print(f'ERROR: Failed to process file {filepath}: {error}')
            traceback.print_exc()
            return False
        except ValueError as error:
            print(f'ERROR: Failed to process file {filepath}: {error}')
            traceback.print_exc()
            return False
        except:
            print(sys.exc_info())
            msg = sys.exc_info()[0] if len(sys.exc_info()) > 0 and sys.exc_info()[0] else "Unknown Exception"
            print("ERROR: ", msg)
            traceback.print_exc()
            return False

        return process_result


    def process_content(self, content) -> List[Tuple[str, Tuple[int, int]]]:
        return self.find_adrenal_nodules_regex(content)

    def get_adrenal_section(self, content: str) -> Tuple[str, Tuple[int, int]]:
        lines = content.split('\n')
        start_adrenal_line_index = -1
        end_adrenal_line_index = -1
        for i, line in enumerate(lines):
            if re.search(r'^\s*ADRENAL', line.upper()):
                start_adrenal_line_index = i
                continue
            if start_adrenal_line_index > -1 and re.search(r'^\s*[A-Z]+', line):
                end_adrenal_line_index = i
                break

        if start_adrenal_line_index == -1 or end_adrenal_line_index == -1:
            # raise ProcessingFileError('Could not find start and end of adrenal section.')
            return '', (start_adrenal_line_index, end_adrenal_line_index)
        #else

        adrenal_section = '\n'.join(lines[start_adrenal_line_index:end_adrenal_line_index])

        # Adrenal information occurs in different sections in a small number of files.
        # So we'll just define the section as just text around the keyword
        if adrenal_section == '' and 'ADRENAL' in content.upper():
            index = content.upper().index('ADRENAL')
            adrenal_section = content[index - 50:index + 50]

        adrenal_span = (content.index(adrenal_section), content.index(adrenal_section) + len(adrenal_section))

        return adrenal_section, adrenal_span

    def process_adrenal_section_text(self, section: str) -> List[Tuple[str, Tuple[int, int]]]:
        """

        Extra Notes from Lindeman
        3. If the section contains any of the following – mark it.
        * "adenoma" – needs follow-up (f/u)
        * "lesion" – needs f/u
        * "metastasis" – likely needs f/u but we may want to differentiate between “known metastasis” and “concern for metastasis”. The known metastasis doesn’t need further f/u (we can presume that patient is already plugged in), whereas the concern for metastasis means it would be more of a new finding that needs additional f/u.
        * "thickening" – DOES NOT need f/u
        * "adrenal nodule" – needs f/u
        * "adrenal nodularity" – this is lower priority for f/u because it means that there’s not a discrete nodule, but the adrenal gland looks lumpy-bumpy. I would exclude for the first pass.
        * "hyperplasia" – also doesn’t need f/u in the incidentaloma clinic
        * "hypoplasia" – DOES NOT need f/u
        4. If the section contains measurements UNDER 1 cm in both dimension – unmark it
        - agree, this doesn’t need f/u
        """
        # print("Processing Section from: " + self.current_filepath)

        positive_pharses = [
            "adenoma",
            "lesion",
            "metastasis",
            "nodule",
            "nodularity",
            "mass",
            "measuring"
        ]

        found_phrases = []
        for phrase in positive_pharses:
            found_index = section.lower().find(phrase.lower())
            if found_index != -1:
                phrase_text = section[found_index:found_index+len(phrase)]
                phrase_span = (found_index, found_index+len(phrase))
                found_phrases.append((phrase_text, phrase_span))
                break

        if len(found_phrases) == 0:
            return []

        #else
        self.adernal_phrase_found_count += 1

        original_section = section
        section = section.replace('\n', ' ')

        # all_matches_with_cm_or_mm = re.findall('^(.*\s(\d+\.?\d+\s?x\s?\d+\.?\d+ cm|mm)|(\d+\.?\d+ cm|mm)\s.*)$', section, re.MULTILINE)
        # all_matches_with_cm_or_mm = re.findall(r'^(.*\s(\d+\.?\d+\s?x\s?\d+\.?\d+\s*(cm|mm))|(\d+\.?\d+\s*(cm|mm))\s.*)$', section, re.MULTILINE)

        regex = re.compile(r'(?:(\d+\.\d+|\d+)\s*)?x?\s*(\d+\.\d+|\d+)\s*([cm]m)')

        for match in regex.finditer(section):

            match_text = original_section[match.span()[0]:match.span()[1]]
            match_span = match.span()

            lstrip_text = match_text.lstrip()
            match_span = (match_span[0] + len(match_text) - len(lstrip_text), match_span[1])

            strip_text = lstrip_text.rstrip()
            match_span = (match_span[0], match_span[1] - (len(lstrip_text) - len(strip_text)))

            found_phrases.append((strip_text, match_span))

            match_group = match.groups()
            dim1 = float(match_group[0]) if match_group[0] and len(match_group[0]) > 0 else 0.0
            dim2 = float(match_group[1]) if match_group[1] and len(match_group[1]) > 0 else 0.0
            unit = match_group[2]
            if unit == 'mm':
                dim1 /= 10.0
                dim2 /= 10.0
            if dim1 < 1.0 and dim2 < 1.0:
                self.adernal_size_too_small_count += 1
                return []

        self.follow_up_count += 1

        return found_phrases

    def find_adrenal_nodules_regex(self, content:str) -> bool:

        if 'ADRENAL' not in content.upper():
            # print(f"!!!NO ADRENAL Section found for {path.basename(self.current_filepath)}")
            self.no_adernal_section_count += 1

            return []

        if 'ADRENALS: Normal'.upper() in content.upper() or 'ADRENALS: Unremarkable'.upper() in content.upper():
            self.adernal_normal_count += 1
            return []
        #else

        adrenal_section_text, adrenal_section_span = self.get_adrenal_section(content)

        phrases = self.process_adrenal_section_text(adrenal_section_text)
        # Updates span to be in whole text not just the section text
        phrases = [(phrase[0], (adrenal_section_span[0] + phrase[1][0], adrenal_section_span[0] + phrase[1][1])) for phrase in phrases]

        for phrase in phrases:
            if content[phrase[1][0]:phrase[1][1]] != phrase[0]:
                print(f"Snippet: >>{content[phrase[1][0]:phrase[1][1]]}<< Phrase: >>{phrase[0]}<<")
            assert content[phrase[1][0]:phrase[1][1]] == phrase[0]

        return phrases
