# Sleipnir API documentation

### Actions

* Requesting data
  - [List corpora](list-corpora)
  - [Get a corpus summary](get-a-corpus-summary)
  - [Get a corpus](get-a-corpus)
  - [List IGTs for a corpus](list-igts-for-a-corpus)
  - [Get an IGT](get-an-igt)
* Adding new data
  - [Add a corpus](add-a-corpus)
  - [Add an IGT to a corpus](add-an-igt-to-a-corpus)
* Assigning or replacing data
  - [Assign or replace an IGT](assign-or-replace-an-igt)
* Partial updates
  - [Update a corpus](update-a-corpus)
  - [Update an IGT](update-an-igt)
* Deleting data
  - [Delete a corpus](delete-a-corpus)
  - [Delete an IGT](delete-an-igt)

#### List corpora

###### Python Function

```python
>>> sleipnir.dbi.list_corpora()
[{'name': 'Yukaghir Corpus', 'igt_count': 7, 'id': 'TtWe4dSUSwe4KIMzUvBtLA'}]
```

###### REST URI

```http
GET /corpora
```

```bash
$ curl -i localhost:5000/v1/corpora
HTTP/1.0 200 OK
Content-Type: application/json
Content-Length: 337

{
  "corpora": [
    {
      "id": "572ba99a-8940-4ae5-8937-8043f8595da1",
      "igt_count": 7,
      "name": "yux",
      "summary_url": "http://localhost:5000/v1/corpora/572ba99a-8940-4ae5-8937-8043f8595da1/summary",
      "url": "http://localhost:5000/v1/corpora/572ba99a-8940-4ae5-8937-8043f8595da1"
    }
  ],
  "corpus_count": 1
}```

#### Get a corpus summary

###### Python Function

```python
>>> sleipnir.dbi.corpus_summary('TtWe4dSUSwe4KIMzUvBtLA')
{'name': 'Yukaghir Corpus', 'igt_count': 7, 'id': 'TtWe4dSUSwe4KIMzUvBtLA', 'igt_ids': ['igt1323-2', 'igt1323-3', 'igt3086-16', 'igt3086-50', 'igt3637-1', 'igt3883-5', 'igt3883-6']}
```

###### REST URI

```http
GET /corpora/<corpus_id>/summary
```

```http
$ curl -i localhost:5000/v1/corpora/572ba99a-8940-4ae5-8937-8043f8595da1/summary
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
>>> sleipnir.dbi.get_corpus('TtWe4dSUSwe4KIMzUvBtLA')
<XigtCorpus object (id: --) with 7 Igts at 139971557389480>
```

It's also possible to get the original serialized corpus as a string
if the database supports it. This is mainly useful when the serialized
form is desired, because it doesn't need to deserialize and reserialize
the corpus, and is thus quicker than `get_corpus()`.

```python
>>> sleipnir.dbi.raw_formats
['application/xml']
>>> sleipnir.dbi.fetch_raw_corpus('TtWe4dSUSwe4KIMzUvBtLA', 'application/xml')
'<xigt-corpus ...'
>>> sleipnir.dbi.fetch_raw_corpus('TtWe4dSUSwe4KIMzUvBtLA', 'application/json')
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
$ curl -i localhost:5000/v1/corpora/572ba99a-8940-4ae5-8937-8043f8595da1
HTTP/1.0 200 OK
Content-Type: application/json
Content-Length: 16996

{"...serialized XigtJSON corpus..."}
```

```http
$ curl -H'ACCEPT: application/xml' -i localhost:5000/v1/corpora/572ba99a-8940-4ae5-8937-8043f8595da1
HTTP/1.0 200 OK
Content-Type: application/xml; charset=utf-8
Content-Length: 13763

<xigt-corpus>...serialized XigtXML corpus...</xigt-corpus>
```

#### List IGTs for a corpus

Without any parameters, this is the same as [getting a corpus](#get-a-corpus),
except that it doesn't include metadata. With parameters, the IGTs that are
returned can be filtered.

Parameters:

| Name  | Type   | Description                     |
| ----- | ------ | ------------------------------- |
| id    | string | Comma-separated list of IGT ids |
| match | string | An [XPath][] (or [XigtPath]) expression for matching IGTs |

###### Python Function

```python
>>> sleipnir.dbi.get_igts('TtWe4dSUSwe4KIMzUvBtLA')
[<Igt object (id: igt1323-2) with 3 Tiers at 139781971298888>, <Igt object (id: igt1323-3) with 3 Tiers at 139781978196152>, <Igt object (id: igt3086-16) with 3 Tiers at 139781971317448>, <Igt object (id: igt3086-50) with 3 Tiers at 139781978216152>, <Igt object (id: igt3637-1) with 3 Tiers at 139781970899256>, <Igt object (id: igt3883-5) with 3 Tiers at 139781978148040>, <Igt object (id: igt3883-6) with 3 Tiers at 139781970902616>]
>>> sleipnir.dbi.get_igts('TtWe4dSUSwe4KIMzUvBtLA', ids=['igt1323-2', 'igt1323-3'])
[<Igt object (id: igt1323-2) with 3 Tiers at 140135406564360>, <Igt object (id: igt1323-3) with 3 Tiers at 140135406565800>]
>>> sleipnir.dbi.get_igts('TtWe4dSUSwe4KIMzUvBtLA', matches=['metadata//dc:subject[text()="Kolyma"]'])
[<Igt object (id: igt1323-2) with 3 Tiers at 140135399438920>, <Igt object (id: igt1323-3) with 3 Tiers at 140135399017432>, <Igt object (id: igt3086-16) with 3 Tiers at 140135399043704>, <Igt object (id: igt3086-50) with 3 Tiers at 140135399559720>]
```

###### REST URI

```http
GET /corpora/<c_id>/igts
```

```http
$ curl -i localhost:5000/v1/corpora/572ba99a-8940-4ae5-8937-8043f8595da1/igts
HTTP/1.0 200 OK
Content-Type: application/json
Content-Length: 35758

{
  "igt_count": 7,
  "igts": [
    "...serialized XigtJSON IGTs..."
  ]
}

$ curl -i localhost:5000/v1/corpora/572ba99a-8940-4ae58937-8043f8595da1/igts?id=igt1323-2%2Cigt1323-3
HTTP/1.0 200 OK
Content-Type: application/json
Content-Length: 8365

{
  "igt_count": 2,
  "igts": [
    "...serialized XigtJSON IGTs..."
  ]
}
```

#### Get an IGT

###### Python Function

```python
>>> sleipnir.dbi.get_igt('TtWe4dSUSwe4KIMzUvBtLA', 'igt1323-2')
<Igt object (id: igt1323-2) with 3 Tiers at 140135399045624>
```

###### REST URI

```http
GET /corpora/<c_id>/igts/<i_id>
```

```http
$ curl -i localhost:5000/v1/corpora/572ba99a-8940-4ae5-8937-8043f8595da1/igts/igt1323-2
HTTP/1.0 200 OK
Content-Type: application/json
Content-Length: 3832

{"...serialized XigtJSON IGT..."}
```

#### Add a corpus

###### Python Function

```python
>>> sleipnir.dbi.add_corpus(XigtCorpus(igts=[Igt(id='i1')]), name='Test Corpus')
{'igt_count': 1, 'id': 'BmMAHdaqT1SUOsZ4Xu0mQg'}
```

###### REST URI

```http
POST /corpora
```

```http
$ curl -i -H'Content-Type: application/json' -d'{"igts": [{"id":"i2"}]}' localhost:5000/v1/corpora
HTTP/1.0 200 OK
Content-Type: application/json
Content-Length: 55

{
  "id": "Ptmbl1o_REWJljZP20sGMA",
  "igt_count": 1
}
```

#### Add an IGT to a corpus

###### Python Function

```python
>>> sleipnir.dbi.add_igt('BmMAHdaqT1SUOsZ4Xu0mQg', Igt(id='i2'))
{'id': 'i2', 'tier_count': 0}
```

###### REST URI

```http
POST /corpora/<c_id>/igts
```

```http
$ curl -i -H'Content-Type: application/json' -d'{"id":"i3"}' localhost:5000/v1/corpora/Ptmbl1o_REWJljZP20sGMA/igts
HTTP/1.0 200 OK
Content-Type: application/json
Content-Length: 36

{
  "id": "i3",
  "tier_count": 0
}
```

#### Assign or Replace an IGT

###### Python Function

```python
>>> sleipnir.dbi.set_igt('BmMAHdaqT1SUOsZ4Xu0mQg', 'i1', Igt(id='i1'))
{'id': 'i1', 'created': True}
>>> sleipnir.dbi.set_igt('BmMAHdaqT1SUOsZ4Xu0mQg', 'i1', Igt(id='i1'))
{'id': 'i1', 'created': False}
```

###### REST URI

```http
PUT /corpora/<c_id>/igts/<i_id>
```

```http
$ curl -i -H'Content-Type: application/json' -d'{"id":"i3", "tiers": [{"id": "p"}]}' -X PUT localhost:5000/v1/corpora/Ptmbl1o_REWJljZP20sGMA/igts/i3
HTTP/1.0 204 NO CONTENT
Content-Type: text/html; charset=utf-8
Content-Length: 0
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
>>> sleipnir.dbi.del_corpus('BmMAHdaqT1SUOsZ4Xu0mQg')
```

###### REST URI

```http
DELETE /corpora/<c_id>
```

```http
$ curl -i -X DELETE localhost:5000/v1/corpora/Ptmbl1o_REWJljZP20sGMA
HTTP/1.0 204 NO CONTENT
Content-Type: text/html; charset=utf-8
Content-Length: 0
```

#### Delete an IGT

###### Python Function

```python
>>> sleipnir.dbi.del_igt('BmMAHdaqT1SUOsZ4Xu0mQg', 'i1')
```

###### REST URI

```http
DELETE /corpora/<c_id>/igts/<i_id>
```

```http
$ curl -i -X DELETE localhost:5000/v1/corpora/Ptmbl1o_REWJljZP20sGMA/igts/i3
HTTP/1.0 204 NO CONTENT
Content-Type: text/html; charset=utf-8
Content-Length: 0
```

[XigtCorpus]: https://github.com/goodmami/xigt/wiki/Data%20Model#xigt-corpus
[XigtXML]: https://github.com/goodmami/xigt/wiki/Codecs#xigtxml
[XigtJSON]: https://github.com/goodmami/xigt/wiki/Codecs#xigtjson
[XPath]: http://www.w3.org/TR/xpath/
[XigtPath]: https://github.com/goodmami/xigt/wiki/XigtPath
