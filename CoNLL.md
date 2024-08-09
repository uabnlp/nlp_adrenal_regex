# UAB CoNLL Format Spec

version 0.4

Date: 2024-08-02

Document the ConLL format being used and make incremental changes to that format in a manner that does not break the existing pipelines.

## Changes

Changes in v0.4:
    * Noted that NEGATED field is optional, numbered the fields
Changes in v0.3:
    * Added note about PREDICTED_VALUE correspondence to NER_Type column
Brief description of changes in v0.2:
    * Add TERM_MODIFIER field.
    * Deprecate NEGATED field, and prefer output given to TERM_MODIFIER.

## Fields


1.	**TXT** – text token from pipeline, return tokens using `nltk.WordPunctTokenizer()`.
For BERT no sub-tokens can be returned. Mandatory, should not be line breaks.  Replace any spaces including tabs with an underscore (_) character. If you must use line breaks, replace spaces and newlines with a single underscore (_) character for each instance.

2.	**GOLD_VALUE** – human annotation of gold entity.  This is used for development of a pipeline.  Use “None” value if not using.

3.	**PREDICTED_VALUE** – Name of predicted entity.  Pipeline specific.  Examples: “LGB”, “Adrenal”.  O (the letter) is the default and will be ignored it indicates Outside.  There is no need to include O rows in the output.   IOB tagging is not used or supported. This corresponds to the NER Type column in NLP_HITS_EXTENDED; use Cancer for reportable cancer; other categories are Remission, Recurrence, Refractory (When inserted into NLP_HITS_EXTENDED, is copied into the CONCEPT_TEXT field.)

4.	**CONFIDENCE** – Pipeline specific score (0.0-1.0), use “None” value if not using.  (This is translated, in the NLP_HITS_EXTENDED the range is 0-1000 as an integer, using this Java code.)
int score = (int) CONFIDENCE * 1000
Optionally, floor round the output to 3 decimal places behind the decimal point.

5.	**SPAN** – This is the text’s span for where the text begins and ends, colon separated.  These are numeric values.  “{begin}:{end}”, replace the variables with the numeric values.  Mandatory.

6.	**CUI** – UMLS (Unified Medical Language System) Concept Unique Identifier. Defaults to “None”.  Optional. UMLS Metathesaurus Browser can be used to search for concepts:  https://uts.nlm.nih.gov/uts/umls/home 

7.	**SEMANTIC-TYPE** – UMLS Semantic Type.  Use the short name, not `T###` format.  Optional field.  Defaults to “None”. Replace any space or tab in output with an underscore (_) character.  Example: “Finding”  

8.	**NEGATED** – Deprecated, always use “None”, put negation result in next field.  Field is optional and defaults to “None”.

9.	**TERM_MODIFIERS** – Modifiers.  For NEGATED this field overrides the value of anything in that field.  Optional, defaults to “None”.
Example format: “- Negation = false - Subject = patient - Conditional = false - Rule_out = false”
See OMOP v5.4 table note_nlp:  https://ohdsi.github.io/CommonDataModel/cdm54.html#note_nlp

### Notes about Fields

* The format has no header.  
* Fields are a space separated.
* The above order is how these values will appear on the line.
* Use a new line to denote the end of the line.
* The first five (5) fields require a value is required in each field, use “None” if you do not need this field.
* With the optional fields those fields can be omitted for a single line or kept.  The Java parser re-evaluates the line length for every line.  If you keep optional fields, put “None” in the field.

## Example line
```
Column Reference:
  <TXT> <GOLD_VALUE> <PREDICTED_VALUE> <CONFIDENCE> <SPAN> <CUI> <SEMANTIC-TYPE> <NEGATED> <TERM_MODIFIER>
```

An example of what this output looks like:

```
lesbian None LGB None 200:206 C1533642 Population_Group None None
```
The UMLS Concept for “Lesbians” has a CUI of C1533642.

Also valid output:

```
lesbian None LGB None 200:206 C1533642 Population_Group
```