[![Code Style](https://github.com/mathun3003/quotes-recommender/actions/workflows/code-style.yaml/badge.svg)](https://github.com/mathun3003/quotes-recommender/actions/workflows/code-style.yaml)

# SageSnippets - Quotes Recommender
<img src="resources/sagesnippet_logo.png" alt="drawing" width="100"/>

## Table of Contents
- [Description](#description)
- [Installation](#installation)
- [Usage](#usage)
- [Architecture](#architecture)

## Description
## Installation
First, clone this repository to your machine.

If you want to develop/contribute to this project, use [poetry](https://python-poetry.org/) as a dependency manager.
Run from content root where the ```pyproject.toml``` is located:
```shell
poetry install
```
and you are free to go. Feel free to open a PR or open an issue.
## Usage
In case you want to make this project running, you can either use
```shell
docker compose up -d redis qdrant
```
in order to start the databases and subsequently type into the shell
```shell
streamlit run quotes_recommender/app.py
```
Make sure to set the environment variables correctly. Therefore, you can use the [sample.local.env](sample.local.env) file.
## Architecture
## Repository Structure
