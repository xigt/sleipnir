Sleipnir
========

Sleipnir is a Xigt database interface that provides both a Python API to
various database backends as well as a REST API for web frontends.

### Actions

* Requesting data
  - [List corpora](#list-corpora)
  - [Get a corpus summary](#get-a-corpus-summary)
  - [Get a corpus](#get-a-corpus)
  - [List IGTs for a corpus](#list-igts-for-a-corpus)
  - [Get an IGT](#get-an-igt)
* Adding new data
  - [Add corpora](#add-corpora)
  - [Add IGTs to a corpus](#add-igts-to-a-corpus)
* Assigning or replacing data 
  - [Assign or replace a corpus](#assign-or-replace-a-corpus)
  - [Assign or replace an IGT](#assign-or-replace-an-igt)
* Partial updates
  - [Update a corpus](#update-a-corpus)
  - [Update an IGT](#update-an-igt)
* Deleting data
  - [Delete a corpus](#delete-a-corpus)
  - [Delete an IGT](#delete-an-igt)

#### List corpora

###### Python Function

```python
>>> sleipnir.dbi.list_corpora()
[{'igt_count': 7, 'name': 'yux', 'id': '572ba99a-8940-4ae5-8937-8043f8595da1'}]
```

###### REST URI

```http
GET /corpora
```

```bash
$ curl -i http://localhost:5000/v1/corpora
HTTP/1.0 200 OK
Content-Type: application/json
Content-Length: 149

{
  "corpora": [
    {
      "id": "572ba99a-8940-4ae5-8937-8043f8595da1",
      "igt_count": 7,
      "name": "yux"
    }
  ],
  "corpus_count": 1
}
```

#### Get a corpus summary

###### Python Function

```python
>>> sleipnir.dbi.corpus_summary('572ba99a-8940-4ae5-8937-8043f8595da1')
{'igt_ids': ['igt1323-2', 'igt1323-3', 'igt3086-16', 'igt3086-50', 'igt3637-1', 'igt3883-5', 'igt3883-6'], 'igt_count': 7, 'name': 'yux'}
```

###### REST URI

```http
GET /corpora/<corpus_id>/summary
```

```http
$ curl -i http://localhost:5000/v1/corpora/572ba99a-8940-4ae5-8937-8043f8595da1/summary
HTTP/1.0 200 OK
Content-Type: application/json
Content-Length: 177

{
  "igt_count": 7,
  "igt_ids": [
    "igt1323-2",
    "igt1323-3",
    "igt3086-16",
    "igt3086-50",
    "igt3637-1",
    "igt3883-5",
    "igt3883-6"
  ],
  "name": "yux"
}
```

#### Get a corpus

###### Python Function

If you want to get the corpus as a Python object, `get_corpus()` will
return it.

```python
>>> sleipnir.dbi.get_corpus('572ba99a-8940-4ae5-8937-8043f8595da1')
<XigtCorpus object (id: --) with 7 Igts at 139781971300168>
```

It's also possible to get the original serialized corpus as a string
if the database supports it. This is mainly useful when the serialized
form is desired, because it doesn't need to deserialize and serialize
the corpus, and is thus quicker than `get_corpus()`.

```python
>>> sleipnir.dbi.raw_formats
['application/xml']
>>> sleipnir.dbi.fetch_raw_corpus('572ba99a-8940-4ae5-8937-8043f8595da1', 'application/xml')
'<xigt-corpus ...'
>>> sleipnir.dbi.fetch_raw_corpus('572ba99a-8940-4ae5-8937-8043f8595da1', 'application/json')
Traceback (most recent call last):
...
    'Unsupported mimetype for raw corpus: %s' % mimetype
sleipnir.errors.SleipnirDbError
```

###### REST URI

```http
GET /corpora/<corpus_id>
```

The response body will be either a [XigtXML] or [XigtJSON] serialized
corpus, depending on the value of the `ACCEPT` header. Valid values are
`application/xml` and `application/json`. If unspecified, the default is
`application/json`.

```http
$ curl -i http://localhost:5000/v1/corpora/572ba99a-8940-4ae5-8937-8043f8595da1
HTTP/1.0 200 OK
Content-Type: application/json
Content-Length: 16996

{...serialized XigtJSON corpus...}
```

```http
$ curl -H"ACCEPT: application/xml" -i http://localhost:5000/v1/corpora/572ba99a-8940-4ae5-8937-8043f8595da1
HTTP/1.0 200 OK
Content-Type: application/xml; charset=utf-8
Content-Length: 13763

<xigt-corpus>...serialized XigtXML corpus</xigt-corpus>
```

#### List IGTs for a corpus

###### Python Function

```python
>>> sleipnir.dbi.get_igts('572ba99a-8940-4ae5-8937-8043f8595da1')
[<Igt object (id: igt1323-2) with 3 Tiers at 139781971298888>, <Igt object (id: igt1323-3) with 3 Tiers at 139781978196152>, <Igt object (id: igt3086-16) with 3 Tiers at 139781971317448>, <Igt object (id: igt3086-50) with 3 Tiers at 139781978216152>, <Igt object (id: igt3637-1) with 3 Tiers at 139781970899256>, <Igt object (id: igt3883-5) with 3 Tiers at 139781978148040>, <Igt object (id: igt3883-6) with 3 Tiers at 139781970902616>]
>>> sleipnir.dbi.get_igts('572ba99a-8940-4ae5-8937-8043f8595da1', ids=['igt1323-2', 'igt1323-3'])
[<Igt object (id: igt1323-2) with 3 Tiers at 140135406564360>, <Igt object (id: igt1323-3) with 3 Tiers at 140135406565800>]
>>> sleipnir.dbi.get_igts('572ba99a-8940-4ae5-8937-8043f8595da1', matches=['metadata//dc:subject[text()="Kolyma"]'])
[<Igt object (id: igt1323-2) with 3 Tiers at 140135399438920>, <Igt object (id: igt1323-3) with 3 Tiers at 140135399017432>, <Igt object (id: igt3086-16) with 3 Tiers at 140135399043704>, <Igt object (id: igt3086-50) with 3 Tiers at 140135399559720>]
```

###### REST URI

```http
GET /corpora/<c_id>/igts
```

Without any parameters, this is the same as [getting a corpus](#get-a-corpus),
except that it doesn't include metadata. With parameters, the IGTs that are
returned can be filtered.

Parameters:

| Name  | Type   | Description                     |
| ----- | ------ | ------------------------------- |
| id    | string | Comma-separated list of IGT ids |
| match | string | An [XPath][] (or [XigtPath]) expression for matching IGTs |

```http
$ curl -i http://localhost:5000/v1/corpora/572ba99a-8940-4ae5-8937-8043f8595da1/igts
HTTP/1.0 200 OK
Content-Type: application/json
Content-Length: 35758

{
  "igt_count": 7,
  "igts": [
    ...serialized XigtJSON IGTs...
  ]
}

$ curl -i http://localhost:5000/v1/corpora/572ba99a-8940-4ae58937-8043f8595da1/igts?id=igt1323-2%2Cigt1323-3
HTTP/1.0 200 OK
Content-Type: application/json
Content-Length: 8365

{
  "igt_count": 2,
  "igts": [
    ...serialized XigtJSON IGTs...
  ]
}

```

#### Get an IGT

###### Python Function

```python
>>> sleipnir.dbi.get_igt('572ba99a-8940-4ae5-8937-8043f8595da1', 'igt1323-2')
<Igt object (id: igt1323-2) with 3 Tiers at 140135399045624>
```

###### REST URI

```http
GET /corpora/<c_id>/igts/<i_id>
```

```http
$ curl -i http://localhost:5000/v1/corpora/572ba99a-8940-4ae5-8937-8043f8595da1/igts/igt1323-2
HTTP/1.0 200 OK
Content-Type: application/json
Content-Length: 3832

{...serialized XigtJSON IGT...}

```

#### Add corpora

###### Python Function

```python
```

###### REST URI

```http
POST /corpora
```

```http

```

#### Add IGTs to a corpus

###### Python Function

```python
```

###### REST URI

```http
POST /corpora/<c_id>/igts
```

```http

```

#### Assign or Replace a corpus

###### Python Function

```python
```

###### REST URI

```http
PUT /corpora/<c_id>
```

```http

```

#### Assign or Replace an IGT

###### Python Function

```python
```

###### REST URI

```http
PUT /corpora/<c_id>/igts/<i_id>
```

```http

```

#### Update a corpus

###### Python Function

```python
```

###### REST URI

```http
PATCH /corpora/<c_id>
```

```http

```

#### Update an IGT

###### Python Function

```python
```

###### REST URI

```http
PATCH /corpora/<c_id>/igts/<i_id>
```

```http

```

#### Delete a corpus

###### Python Function

```python
```

###### REST URI

```http
DELETE /corpora/<c_id>
```

```http

```

#### Delete an IGT

###### Python Function

```python
```

###### REST URI

```http
DELETE /corpora/<c_id>/igts/<i_id>
```

```http

```

### Installation and Requirements

## Configuration

The `config.py` module can be edited to configure Sleipnir.
Configuration options include:

* `DATABASE` - type of database used (default: `filesystem`)
* `DATABASE_PATH` - location of database file or directory (default: `db/`)

[XigtCorpus]: https://github.com/goodmami/xigt/wiki/Data%20Model#xigt-corpus
[XigtXML]: https://github.com/goodmami/xigt/wiki/Codecs#xigtxml
[XigtJSON]: https://github.com/goodmami/xigt/wiki/Codecs#xigtjson
[XPath]: http://www.w3.org/TR/xpath/
[XigtPath]: https://github.com/goodmami/xigt/wiki/XigtPath
