Sleipnir
========

Sleipnir is a Xigt database interface that provides both a Python API to
various database backends as well as a REST API for web frontends.

## Actions

* Requesting data
  - [List corpora](API.md#list-corpora)
  - [Get a corpus summary](API.md#get-a-corpus-summary)
  - [Get a corpus](API.md#get-a-corpus)
  - [List IGTs for a corpus](API.md#list-igts-for-a-corpus)
  - [Get an IGT](API.md#get-an-igt)
* Adding new data
  - [Add a corpus](API.md#add-a-corpus)
  - [Add an IGT to a corpus](API.md#add-an-igt-to-a-corpus)
* Assigning or replacing data
  - [Assign or replace an IGT](API.md#assign-or-replace-an-igt)
* Partial updates
  - [Update a corpus](API.md#update-a-corpus)
  - [Update an IGT](API.md#update-an-igt)
* Deleting data
  - [Delete a corpus](API.md#delete-a-corpus)
  - [Delete an IGT](API.md#delete-an-igt)

## Installation and Requirements

Sleipnir is a [Python 2.7 or 3.3+](https://www.python.org/downloads/) application
that runs on a WSGI server. It has the following dependencies:
 - [Flask](http://flask.pocoo.org/)
 - [Xigt](https://github.com/goodmami/xigt)

## Configuration

The `config.py` module can be edited to configure Sleipnir.
Configuration options include:

* `DATABASE` - type of database used (default: `filesystem`)
* `DATABASE_PATH` - location of database file or directory (default: `db/`)
