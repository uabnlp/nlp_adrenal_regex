# Adrenal Regex Classifier

This is a regular expression classifier for Adrenal concepts.  It takes in
electronic health records as text files.  It outputs to our custom CoNLL
file format.



The typs of electronic health record that classifier is ran on are:
* CT 3D Body Requiring Indep Wkst
* CT Abdomen and Pelvis w contrast
* CT Abdomen and Pelvis wo contrast
* CT Abdomen and Pelvis wo IV contrast'
* CT Abdomen and Pelvis wo+w contrast
* CT Abdomen Partial Study
* CT Abdomen Partial Study with contrast
* CT Abdomen Partial Study wo+w contrast
* CT Abdomen Pelvis wo IV contrast PO PRN
* CT Abdomen with contrast
* CT Abdomen wo contrast
* CT Abdomen wo IV contrast
* CT Abdomen wo IV contrast PO PRN
* CT Abdomen wo+w contrast
* CT Angio Abdomen and or Pelvis w Runoff
* CT Angio Abdomen and Pelvis
* CT Angio Abdomen Partial Study
* CT Angio Abdomen wo+w contrast
* CT Guided Procedure Body
* CT Outside images
* CT Outside Images Abdomen
* CT Pelvis wo IV contrast
* CTA Abdomen and Pelvis with Robotics
* Interpretation of Outside Films Abdomen
* Interpretation of Outside Films CT Body
* Interpretation of Outside Films MR Body
* MR 3D Body Requiring Indep Wkst
* MR Abdomen Ltd for PKD
* MR Abdomen Partial Study
* MR Abdomen with contrast
* MR Abdomen wo contrast
* MR Abdomen wo+w contrast
* MR Angio Abdomen wo contrast
* MR Angio Abdomen wo+w contrast
* MR Angio Chest wo+w contrast
* MR Angio Pelvis wo contrast
* MR Angio Pelvis wo+w contrast
* MR Outside Images
* MR Pelvis with contrast
* MR Pelvis wo contrast
* MR Pelvis wo+w contrast
* US Abdomen


The results are a [custom CoNLL file format](CoNLL.md).  This pipeline will give
PREDICTED_VALUE of O for anything which is not to be classified (The "O" mean
Outside in IOB tagging).  These can be removed using the `--silence-o` option.

The CoNLL file format is outputted as a `.txt` file.


## What the Classifier Does

It uses regular expressions to search for section with "ADRENAL:" or "ADRENALS:"
on the report. Within that section, it searches using regular expression for the
following keywords: "adenoma", "lesion", "metastasis", "nodule", "nodularity",
"mass", "measuring". It is also searches for measurement units in cm or mm, and
will accept a width x height unit so "5.0 x 8.0 mm".  Any nodules that are under
1 cm in both dimensions are "unmarked" by the algorithm (meaning discarded as a
match).  So it would not mark any measurement under 1 cm, and 1 cm+ measurements
would be marked. Also, the algorithm looks for negation words in a sentance.  So
if the report had "no nodule", would be and example of negation and that would
not be marked in the NEGATION field's output.

# Installation

Requires Python 3.7+

The only dependency is [NLTK](https://www.nltk.org/).  The requirements file
specifies the latest version of NLTK 3.8.1 at this time, however the software
was programmed using 3.6.2.  The current NLTK's website says that its
version 3.8.1 supports Python versions 3.7-3.11.

1. It is best practice to create a virtual environment for a Python program.
These are the instructions for [venv](https://docs.python.org/3/tutorial/venv.html).  
Anaconda, poetry, and virtualenv are all other valid ways to create virtual environments.

```bash
python -m venv adrenal_venv
```

2. Activate the virtual environment.

**Linux/MacOs (bash/zsh)**

```bash
$ source adrenal_venv/bin/activate
```

**Windows**

```powershell
C:..\adrenal> adrenal_venv\Scripts\activate
-- or --
C:..\adrenal> adrenal_venv\Scripts\activate.bat
```

3. Install the requirements (NLTK).

```bash
pip install -r requirements.txt
```


# Running

Put electronic medical records in a text files in the `folder/input`. Activate the environment, if not already in
it (as above).

Run cc_adrenal.py:
```
python cc_adernal.py --input-dir folder/input --output-dir folder/output
```

Help from console:
```
$ python cc_adrenal.py --help
usage: cc_adrenal.py [-h] -i INPUT_DIR -o OUTPUT_DIR [--log_dir LOG_DIR] [-v] [--silence-o]

Adrenal Regex Classifier (version 1.0.0) processes a Adrenal Documents for Cheaha. Text files -> CoNLL files

options:
  -h, --help            show this help message and exit
  -i INPUT_DIR, --input_dir INPUT_DIR
                        Input Directory of text files to process
  -o OUTPUT_DIR, --output_dir OUTPUT_DIR
                        Output Directory for CoNLL files.
  --log_dir LOG_DIR     Directory to store log files in. If not provided output will be to console.
  -v, --verbose         Verbose output. Sets logger to DEBUG.
  --silence-o           Silences default PREDICTED_VALUES of O in the output CoNLL files.
```

# License
Apache License 2.0

# Credits
This is work done in the Informatics Institute of University of Alabama at Birmingham.
This is now the Department of Biomedical Informatics and Data Science.

Tobias O'Leary, John D. Osborne, Micah D. Cochran