
# Filesystem backend for Sleipnir
#
# config['DATABASE_PATH'] should be a directory and it should contain
# a file `index.json` with the following structure:
# {
#     "files": {
#         "ID": {"name": "NAME", "path": "PATH"}
#     }
# }
# where ID is a unique identifier for a corpus, NAME is the name given
# to the corpus, and PATH is the corpus's path relative to
# DATABASE_PATH.
#

import os.path
import json
import uuid

from xigt import XigtCorpus, xigtpath as xp
from xigt.codecs import xigtxml, xigtjson

from flask import json, Response

app=None

raw_formats = {'application/xml'}

def corpora():
    idx = load_index()
    corpora = []
    for f_id, entry in idx['files'].items():
        corpora.append({
            'id': f_id,
            'name': get_name(entry),
            'igt_count': entry.get('igt_count', -1)
        })
    return json.jsonify(corpora_count=len(idx['files']), corpora=corpora)

def corpus_summary(corpus_id):
    entry = get_entry(corpus_id)
    xc = load_corpus(entry)
    return json.jsonify(
            name=get_name(entry),
            num_igts=len(xc),
            igt_ids=[igt.id for igt in xc]
    )

def fetch_raw(corpus_id, mimetype):
    entry = get_entry(corpus_id)
    if mimetype == 'application/xml':
        return open(corpus_filename(entry)).read()
    return None

def get_corpus(corpus_id, mimetype=None):
    entry = get_entry(corpus_id)
    return serialize_corpus(load_corpus(entry), mimetype)

def add_corpus(f, mimetype, corpus_id=None, name=None):
    pass

def get_igts(corpus_id, igt_ids=None, matches=None, mimetype=None):
    entry = get_entry(corpus_id)
    xc_ = load_corpus(entry)
    xc = XigtCorpus(metadata=xc_.metadata, nsmap=xc_.nsmap)
    if igt_ids is None:
        igts = list(xc_.igts)
    else:
        igts = []
        for igt_id in igt_ids:
            igt = xc_.get(igt_id)
            if igt is not None:
                igts.append(igt)
    if matches is not None:
        matcher = lambda i: any(xp.find(i, m) is not None for m in matches)
        igts = list(filter(matcher, igts))
    xc.extend(igts)
    return json.jsonify(matches=matches, ids=[igt.id for igt in xc])
    return serialize_corpus(xc, mimetype)

def load_index():
    return json.load(
        open(os.path.join(app.config['DATABASE_PATH'], 'index.json'))
    )

def get_entry(corpus_id, index=None):
    if index is None:
        index = load_index()
    return index['files'].get(corpus_id)

def corpus_filename(entry):
    if entry and 'path' in entry:
        return os.path.join(app.config['DATABASE_PATH'], entry['path'])
    else:
        return None

def load_corpus(entry):
    return xigtxml.load(corpus_filename(entry))

def get_name(entry):
    return entry.get('name', '(untitled)')

def serialize_corpus(xc, mimetype='application/json'):
    if mimetype == 'application/xml':
        return xigtxml.dumps(xc, indent=None)
    elif mimetype == 'application/json':
        return xigtjson.dumps(xc, indent=None)
    elif mimetype is None:
        return xc
    # else: raise exception
    return None
