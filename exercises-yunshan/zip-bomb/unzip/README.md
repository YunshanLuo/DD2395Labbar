
# Instructions for Using `safe_unzip.py`

This directory contains the script `safe_unzip.py`, which is used to safely verify zip files and check their compression rates.

## Setup

While not strictly necessary, it is recommended that the script is run within a [python virtual environment](https://realpython.com/python-virtual-environments-a-primer/#why-do-you-need-virtual-environments) (venv). All script dependencies will then be installed in the venv instead of polluting your global python environment. The provided `Makefile` simplifies the process.

`cd` into this directory, then run:
```bash
make venv_setup
```
This creates the venv and installs all requirements.

## Running the Script on a File

To **activate the venv**, run:
```bash
source .venv/bin/activate
```

Within the venv, simply **run the script**:
```bash
python3 safe_unzip.py <zip_file>
```

Once you are finished, you can **deactivate the venv**:
```bash
deactivate
```

## Example

After running `make venv_setup`, the process of running the script on the example file should look something like this:

```bash
name@computer:<path_to_lab>$ cd unzip/
name@computer:<path_to_lab>/unzip$ source .venv/bin/activate
(.venv) name@computer:<path_to_lab>/unzip$ python3 safe_unzip.py ../examples/zbsm.zip
Zipped size: 0.04 MB
Unpacking: 5208.31 MB, Compression ratio: 128.9k
Successfully finished unzipping
(.venv) name@computer:<path_to_lab>/unzip$ deactivate
name@computer:<path_to_lab>/unzip$
```

## Removal of venv

To remove the venv, simply run
```bash
make clean
```
