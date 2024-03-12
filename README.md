[![Python 3.11 | 3.12](https://img.shields.io/badge/Python-3.11%20%7C%203.12-blue)](https://www.python.org/downloads)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)

[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/Preocts/objeggtives-discord-bot/main.svg)](https://results.pre-commit.ci/latest/github/Preocts/objeggtives-discord-bot/main)
[![Python tests](https://github.com/Preocts/objeggtives-discord-bot/actions/workflows/python-tests.yml/badge.svg?branch=main)](https://github.com/Preocts/objeggtives-discord-bot/actions/workflows/python-tests.yml)

# objeggtives-discord-bot

A discord bot to create objeggtives to be completed. Objeggtives are created
with a comment, linked to the current message or a reply.  Priority can be set
and objeggtives can be closed with additional commands.

---

# Local developer installation

The following steps outline how to install this repo for local development. See
the [CONTRIBUTING.md](CONTRIBUTING.md) file in the repo root for information on
contributing to the repo.

## Prerequisites

### Clone repo

```console
git clone https://github.com/Preocts/objeggtives-discord-bot

cd objeggtives-discord-bot
```

### Virtual Environment

Use a ([`venv`](https://docs.python.org/3/library/venv.html)), or equivalent,
when working with python projects. Leveraging a `venv` will ensure the installed
dependency files will not impact other python projects or any system
dependencies.

**Linux/Mac users**: Replace `python`, if needed, with the appropriate call to
the desired version while creating the `venv`. (e.g. `python3` or `python3.8`)

Once inside an active `venv` all systems should allow the use of `python` for
command line instructions. This will ensure you are using the `venv`'s python
and not the system level python.

### Create the `venv`:

```console
python -m venv venv
```

Activate the `venv`:

```console
. venv/bin/activate
```

The command prompt should now have a `(venv)` prefix on it. `python` will now
call the version of the interpreter used to create the `venv`

To deactivate (exit) the `venv`:

```console
deactivate
```

---

## Developer Installation Steps

### Install editable library and development requirements

```console
python -m pip install --editable .[dev,test]
```

### Install pre-commit [(see below for details)](#pre-commit)

```console
pre-commit install
```

---

## Pre-commit and nox tools

### Run pre-commit on all files

```console
pre-commit run --all-files
```

### Run tests with coverage (quick)

```console
nox -e coverage
```

### Run tests (slow)

```console
nox
```

### Build dist

```console
nox -e build
```

---

## Updating dependencies

New dependencys can be added to the `requirements-*.in` file. It is recommended
to only use pins when specific versions or upgrades beyond a certain version are
to be avoided. Otherwise, allow `pip-compile` to manage the pins in the
generated `requirements-*.txt` files.

Once updated following the steps below, the package can be installed if needed.

### Update the generated files with changes

```console
nox -e update
```

### Upgrade all generated dependencies

```console
nox -e upgrade
```

---

## [pre-commit](https://pre-commit.com)

> A framework for managing and maintaining multi-language pre-commit hooks.

This repo is setup with a `.pre-commit-config.yaml` with the expectation that
any code submitted for review already passes all selected pre-commit checks.

---

## Error: File "setup.py" not found

Update `pip` to at least version 22.3.1
