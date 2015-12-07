
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
from uuid import uuid4
from base64 import urlsafe_b64encode

from xigt import XigtCorpus, xigtpath as xp
from xigt.errors import XigtError
from xigt.codecs import xigtxml, xigtjson

from flask import json

from sleipnir.errors import (
    SleipnirDbError,
    SleipnirDbBadRequestError,
    SleipnirDbNotFoundError,
    SleipnirDbConflictError,
)

DATABASE_PATH = None

raw_formats = {'application/xml'}

def corpora():
    idx = _load_index()
    corpora = []
    for f_id, entry in idx['files'].items():
        corpora.append({
            'id': f_id,
            'name': _get_name(entry),
            'igt_count': entry.get('igt_count', -1)
        })
    return json.jsonify(corpora_count=len(idx['files']), corpora=corpora)

def corpus_summary(corpus_id):
    entry = _get_entry(corpus_id)
    xc = _load_corpus(entry)
    return json.jsonify(
            name=_get_name(entry),
            igt_count=len(xc),
            igt_ids=[igt.id for igt in xc]
    )

def fetch_raw(corpus_id, mimetype):
    entry = _get_entry(corpus_id)
    if mimetype == 'application/xml':
        return open(_corpus_filename(entry)).read()
    return None

def get_corpus(corpus_id, mimetype=None):
    entry = _get_entry(corpus_id)
    return _serialize_corpus(_load_corpus(entry), mimetype)

def add_corpora(fs, corpus_id=None, name=None):
    for f in fs:
        print(fs, fs.content_type)

def get_igts(corpus_id, igt_ids=None, matches=None, mimetype=None):
    entry = _get_entry(corpus_id)
    xc_ = _load_corpus(entry)
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
    return _serialize_corpus(xc, mimetype)

def add_igts(corpus_id, data, mimetype):
    entry = _get_entry(corpus_id)
    new_xc = _decode_corpus(data, mimetype)
    xc = _load_corpus(entry)
    # adding IGTs doesn't allow for changing corpus metadata
    # try:
    #     for md in new_xc.metadata:
    #         if md not in xc.metadata:
    #             xc.metadata.append(md)
    # except XigtError:
    #     raise SleipnirDbBadRequestError(
    #         'Metadata ID conflict in corpus {}.'.format(corpus_id)
    #     )
    try:
        for igt in new_xc:
            xc.append(igt)
    except XigtError:
        raise SleipnirDbBadRequestError(
            'Igt ID "{}" already exists in corpus {}.'
            .format(igt.id, corpus_id)
        )
    _save_corpus(entry, xc)
    _update_index(corpus_id, xc)
    return json.jsonify({'success': True, 'igt_count': len(xc)})

def set_igt(corpus_id, igt_id, data, mimetype):
    entry = _get_entry(corpus_id)
    xc = _load_corpus(entry)
    cur_igt = xc.get(igt_id)
    new_igt = _decode_igt(data, mimetype)
    if new_igt is not None:
        # ensure new igt's ID maps the target
        if new_igt.id is None:
            try:
                new_igt.id = igt_id
            except ValueError:
                raise SleipnirDbBadRequestError(
                    'Invalid ID: {}'.format(igt_id)
                )
        elif new_igt.id != igt_id:
            raise SleipnirDbBadRequestError(
                'Igt ID must match requested ID: {} != {}'
                .format(str(new_igt.id), igt_id)
            )
        if cur_igt is None:
            # target doesn't exist; append
            xc.append(new_igt)
        else:
            # target exists; replace
            idx = xc.index(cur_igt)
            xc[idx] = new_igt
    elif cur_igt:
        # empty payload, non-empty target; delete the target IGT
        xc.remove(cur_igt)
    _save_corpus(entry, xc)
    _update_index(corpus_id, xc)
    return json.jsonify({'success': True, 'igt_count': len(xc)})

def _load_index():
    try:
        return json.load(
            open(os.path.join(DATABASE_PATH, 'index.json'))
        )
    except OSError:
        raise SleipnirDbError('Database index not found.')

def _update_index(corpus_id, xc, name=None, path=None):
    index = _load_index()
    entry = index['files'].get(corpus_id)
    entry['igt_count'] = len(xc)
    if name is not None: entry['name'] = name
    if path is not None: entry['path'] = path
    index['files'][corpus_id] = entry
    json.dump(
        index,
        open(os.path.join(DATABASE_PATH, 'index.json'), 'w')
    )

def _get_entry(corpus_id, index=None):
    if index is None:
        index = _load_index()
    entry = index['files'].get(corpus_id)
    if not entry:
        raise SleipnirDbNotFoundError(
            'Corpus {} not found.'.format(corpus_id)
        )
    return entry

def _corpus_filename(entry):
    if entry and 'path' in entry:
        return os.path.join(DATABASE_PATH, entry['path'])
    else:
        return None

def _load_corpus(entry):
    return xigtxml.load(_corpus_filename(entry))

def _save_corpus(entry, xc):
    return xigtxml.dump(_corpus_filename(entry), xc)

def _decode_corpus(data, mimetype):
    xc = None
    if mimetype == 'application/json':
        xc = xigtjson.decode(json.loads(data))
    elif mimetype == 'application/xml':
        xc = xigtxml.loads(data)
    else:
        raise SleipnirDbError('Unsupported filetype')
    _validate_corpus(xc)
    return xc

def _decode_igt(data, mimetype):
    igt = None
    if data:
        if mimetype == 'application/json':
            data = json.loads(data)
            if data:
                igt = xigtjson.decode_igt(data)
        #elif mimetype == 'application/xml':
        else:
            raise SleipnirDbError('Unsupported filetype')
    return igt

def _validate_corpus(xc):
    for igt in xc:
        if igt.id is None:
            raise SleipnirDbBadRequestError('Each IGT must have an ID.')

def _get_name(entry):
    return entry.get('name', '(untitled)')

def _serialize_corpus(xc, mimetype='application/json'):
    if mimetype == 'application/xml':
        return xigtxml.dumps(xc, indent=None)
    elif mimetype == 'application/json':
        return xigtjson.dumps(xc, indent=None)
    elif mimetype is None:
        return xc
    # else: raise exception
    return None
