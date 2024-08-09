"""
Script for Processing Adernal Directories

This script is intended to plug into the cheaha_cron_consumer.
It is provided with 3 arguments
* -i (input_dir) INPUT_DIR - Files to be processed
* -o (output_path) OUTPUT_DIR - Where results to be output to
* -l (log_dir) LOG_PATH - Optional... (Will log to console if not provided)
* -v (-verbose) Optional... Flag for verbose (sets logger in debug mode)
"""


# Copyright 2024 University of Alabama at Birmingham
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
import argparse
import logging
import logging.handlers
import os
import os.path as path
from typing import List, Tuple

import nltk

from AdrenalRegex import AdrenalRegex

__version__ = "1.0.0"


class AdrenalCheahaProcessor:

    def __init__(self, input_dir: str, output_dir: str, logger: logging.Logger, adrenalRegex: AdrenalRegex, silence_o: bool = False):
        """
        Initialization method of AdernalCheahaProcessor

        :param input_dir: directory to process
        :param output_dir: directory to output results to
        :param logger: Configured logging to use for logging
        :param adrenalRegex: The class that finds adrenal groups
        """
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.logger = logger
        self.adrenalRegex = adrenalRegex
        self.silence_o = silence_o

    def run(self):
        with open(path.join(self.output_dir, 'phrases.txt'), 'w') as phrases:
            phrases.write('')
        self.process_dir(self.input_dir, self.output_dir)

    def process_dir(self, input_dir: str, output_dir: str):
        if not os.path.exists(input_dir):
            msg = f"{os.path.basename(__file__)}: process_dir(), Path in input_dir '{input_dir}' was not found"
            self.logger.info(msg)

        files = [path.join(input_dir, file) for file in os.listdir(input_dir) if not path.splitext(file)[1] or path.splitext(file)[1] == '.txt']
        files = [file for file in files if path.isfile(file)]

        for file in files:
            output_file = path.join(output_dir, path.basename(file))
            output_content = self.process_file(file, output_file)

    def process_file(self, input_path: str, output_path: str) -> str:
        self.adrenalRegex.current_filepath = input_path
        with open(input_path, 'r') as f:
            input_content = f.read()
        output_content = self.process_content(input_content)

        if output_path:
            with open(output_path, 'w') as fw:
                fw.write(output_content)

        return output_content

    def groups_to_conll_output(self, content:str, found_phrases: List[Tuple[str, Tuple[int, int]]]):
        """

        :param content: Text of the content that was process
        :param found_phrases: phrases found by the adrenalRegex - list of text with spans.
        :return: conll output acceptable for UDAS
        """
        out_lines = []

        tokens, spans = self.gather_tokens_and_spans(content)

        for i, token in enumerate(tokens):
            mark_token = False
            token_span = spans[i]

            for phrase in found_phrases:
                if self.spans_overlap(token_span, phrase[1]):
                    mark_token = True
                    break

            if self.silence_o and not mark_token:
                # skip to next token because this one has no Adrenal concepts.
                continue

            gold_value = 'None'
            predict_value = 'Adrenal' if mark_token else 'O'
            confidence = 'None'
            span = f'{token_span[0]}:{token_span[1]}'
            cui = "C0521428" if mark_token else 'None'
            semanticType = "Finding" if mark_token else 'None'
            negated = "None"

            line_values = [token, gold_value, predict_value, confidence, span, cui, semanticType, negated]

            out_lines.append(' '.join(line_values))

        return '\n'.join(out_lines)

    def process_content(self, content: str,) -> str:

        found_phrases = self.adrenalRegex.process_content(content)
        if len(found_phrases) > 0:
            with open(path.join(self.output_dir, 'phrases.txt'), 'a') as phrases:
                phrases.write(self.adrenalRegex.current_filepath + ':' + '\n')
                for phrase in found_phrases:
                    context_before = content[max(0, phrase[1][0] - 30):phrase[1][0]]
                    context_after = content[phrase[1][1]:min(len(content), phrase[1][1] + 30)]
                    output = re.sub(r'\n+', ' ', f'* {context_before}>>{phrase[0]}<<{context_after}')
                    phrases.write(output + '\n')

        conll_output = self.groups_to_conll_output(content, found_phrases)

        return conll_output

    def spans_overlap(self, s1: Tuple[int, int], s2: Tuple[int, int]) -> bool:
        if s1[0] == s1[1] or s2[0] == s2[1]:
            return False
        #else
        return s1[0] <= s2[1] and s2[0] <= s1[1]

    def gather_tokens_and_spans(self, text: str) -> Tuple[List[str], List[Tuple[int, int]]]:
        """
        Gathers tokens and spans.

        :param text: text to divide into tokens.
        :return: Two lists one is of text and one is start and stop of the span in the line parameter
        """

        tokenizer = nltk.WordPunctTokenizer()

        spans = list(tokenizer.span_tokenize(text))
        tokens = [text[span[0]:span[1]] for span in spans]

        return tokens, spans


def setup_logger(log_dir: str, verbose: bool) -> logging.Logger:
    if log_dir is None:
        handler: logging.Handler = logging.StreamHandler(stream=sys.stdout)
    else:
        handler: logging.Handler = logging.handlers.TimedRotatingFileHandler(
            'cc_adernal.log',
            when='D',
            interval=1,
            backupCount=14,
        )

    logger: logging.Logger = logging.getLogger(path.basename(__file__))
    logger.addHandler(handler)

    logger.setLevel(logging.INFO)
    if verbose:
        logger.setLevel(logging.DEBUG)

    return logger


def process_args() -> Tuple[str, str, str, bool, bool]:

    parser = argparse.ArgumentParser(
#        prog=f"Adrenal Regex Classifier version ",
        prog=os.path.basename(__file__),
        description=f"Adrenal Regex Classifier (version {__version__}) processes a Adrenal Documents for Cheaha. Text files -> CoNLL files",
    )

    parser.add_argument('-i', '--input_dir', type=str, required=True, help='Input Directory of text files to process')
    parser.add_argument('-o', '--output_dir', type=str, required=True, help='Output Directory for CoNLL files.')
    parser.add_argument('--log_dir', type=str, required=False, default=None, help="Directory to store log files in. If not provided output will be to console.")
    parser.add_argument('-v', '--verbose', action='store_true', required=False, default=False, help="Verbose output. Sets logger to DEBUG.")
    parser.add_argument("--silence-o", action="store_true", help="Silences default PREDICTED_VALUES of O in the output CoNLL files.")

    args = parser.parse_args()

    input_dir = path.expanduser(path.expandvars(args.input_dir))
    output_dir = path.expanduser(path.expandvars(args.output_dir))
    log_dir = path.expanduser(path.expandvars(args.log_dir)) if args.log_dir else None

    return input_dir, output_dir, log_dir, args.verbose, args.silence_o


if __name__ == '__main__':

    # Process arguments
    input_dir, output_dir, log_dir, verbose, silence_o = process_args()

    # create missing directories
    if output_dir and not path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    if log_dir and not path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    # Setup Logger
    logger: logging.Logger = setup_logger(log_dir, verbose)

    # Write Arguments Information
    logger.debug(f'{path.basename(__file__)} arguments:\n  * input_dir: {input_dir}\n  * output_dir: {output_dir}')
    if log_dir:
        logger.debug(f'  * log_dir: {log_dir}')
    if verbose:
        logger.debug(f'  * verbose: {verbose}')

    # Create and Run Processor
    processor = AdrenalCheahaProcessor(input_dir, output_dir, logger, AdrenalRegex(), silence_o)
    processor.run()
