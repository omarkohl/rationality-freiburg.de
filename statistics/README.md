# Statistics

This folder contains a script (./scripts/generate.py) that is used to
pre-process data, generate the .csv files contained in this directory and
generate plots and markdown documents in ../website/

The .csv files contain clean raw data for the events 2024.


## Setup

```bash
poetry install
```


## Re-generate .csv files

Note you need special access permissions to be able to do this.

* In the Google Calc document 'Event Feedback (Responses)' download both the
  'EN' and the 'DE' sheet as CSV files.
* Open the attendance-statistics.ods file and 'Save a Copy...' of the
  'People 2024' sheet in .csv format.
  * Field delimiter ;
  * String delimiter "
  * Uncheck all 4 checkboxes
* Place the above files in the current directory.

Execute:

```bash
poetry run scripts/generate.py
```
