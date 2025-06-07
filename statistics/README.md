# Statistics

This folder contains a script (./scripts/generate.py) that is used to
pre-process data, generate the .csv files contained in this directory and
generate plots and markdown documents in ../website/

The .csv files contain clean raw data for the events 2024.


## Setup

Install [uv](https://docs.astral.sh/uv/getting-started/installation/).

```bash
uv sync
uv sync --dev
```

## Linting and Formatting

```bash
uv run ruff check --fix
uv run ruff format
```

If you are using Ju Jutsu VCS you can also add the following to
`../.jj/repo/config.toml`:

```toml
[fix.tools.ruff-check]
command = ["uv", "run", "ruff", "check", "--fix", "-", "--stdin-filename=$path"]
patterns = ["glob:'statistics/**/*.py'"]

[fix.tools.ruff-format]
command = ["uv", "run", "ruff", "format", "-", "--stdin-filename=$path"]
patterns = ["glob:'statistics/**/*.py'"]
```

And then execute:

```bash
jj fix
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
uv run scripts/parse.py
uv run scripts/generate.py
```
