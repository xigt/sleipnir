
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

from xigt.codecs import xigtxml, xigtjson

from flask import json

def corpora(app):
    idx = load_index(app)
    return json.jsonify(
        num_corpora=len(idx['files']),
        corpora=[{"id": f_id, "name": get_name(entry)}
                 for f_id, entry in idx['files'].items()]
    )

def corpus(app, corpus_id):
    idx = load_index(app)
    entry = idx['files'].get(corpus_id)
    xc = load_corpus(app, entry)
    return json.jsonify(
            name=get_name(entry),
            num_igts=len(xc),
            igt_ids=[igt.id for igt in xc]
    )

def igt(app, corpus_id, igt_id):
    idx = load_index(app)
    entry = idx['files'].get(corpus_id)
    xc = load_corpus(app, entry)
    if xc:
        igt = xc.get(igt_id)
        if igt:
            return json.jsonify(
                igt=xigtjson.encode_igt(igt)
            )
    return None

def load_index(app):
    return json.load(
        open(os.path.join(app.config['DATABASE_PATH'], 'index.json'))
    )

def load_corpus(app, entry):
    if entry and 'path' in entry:
        path = os.path.join(app.config['DATABASE_PATH'], entry['path'])
        return xigtxml.load(path)
    else:
        return None

def get_name(entry):
    return entry.get('name', '(untitled)')
