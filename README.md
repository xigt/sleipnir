Sleipnir
========

## GET Routes

The following always respond with JSON:

* `/corpora` - get a listing of available corpora
* `/corpora/<corpus_id>/summary` - retrieve a summary of the contents
  of a corpus

The following always return a serialization of a [XigtCorpus]. If the
`ACCEPT` header is set to `application/xml`, the corpus will be
serialized with [XigtXML], otherwise with XigtJSON.

* `/corpora/<corpus_id>` - retrieve a full corpus
* `/corpora/<corpus_id>/igts` - retrieve a sublist of igts

Parameters for `/corpora/<corpus_id>/igts` include:

| Name  | Type   | Description                     |
| ----- | ------ | ------------------------------- |
| id    | string | Comma-separated list of IGT ids |
| match | string | An [XPath][] (or [XigtPath]) expression for matching IGTs |

## POST Routes

* `/corpora` - add a corpus to the collection
* `/corpora/<corpus_id>/igts` - add IGTs to a corpus

## PATCH Routes

* `/corpora/<corpus_id>` - update a corpus

## Configuration

The `config.py` module can be edited to configure Sleipnir.
Configuration options include:

* `DATABASE` - type of database used (default: `filesystem`)
* `DATABASE_PATH` - location of database file or directory (default: `db/`)

[XigtCorpus]: https://github.com/goodmami/xigt/wiki/Data%20Model#xigt-corpus
[XigtXML]: https://github.com/goodmami/xigt/wiki/Codecs#xigtxml
[XPath]: http://www.w3.org/TR/xpath/
[XigtPath]: https://github.com/goodmami/xigt/wiki/XigtPath
