
# Filesystem backend for Sleipnir
#
# config['DATABASE_PATH'] should be a directory and it should contain
# a file `index.json.gz` with the following structure:
# {
#     "corpora": {
#         "ID": {"name": "NAME", "path": "PATH"}
#     }
# }
# where ID is a unique identifier for a corpus, NAME is the name given
# to the corpus, and PATH is the corpus's path relative to
# DATABASE_PATH.
#

import os
import shutil
from tempfile import mkdtemp
from uuid import uuid4
from base64 import urlsafe_b64encode
import gzip
import json
from collections import defaultdict

from xigt import xigtpath as xp, Item, Metadata, Meta
from xigt.codecs import xigtjson

from sleipnir.interfaces import SleipnirDatabaseInterface
from sleipnir.errors import SleipnirDbError, SleipnirError


class FileSystemDbi(SleipnirDatabaseInterface):
    raw_formats = ['application/json']

    def __init__(self, path):
        SleipnirDatabaseInterface.__init__(self, path)
        # if DB doesn't exist; create a bare one
        if not os.path.isdir(path):
            os.mkdir(path)
            _dump_index({'corpora': {}}, path)
            os.mkdir(os.path.join(path, 'data'))
        self.index = _load_index(self.path)  # primary index

    def _update_index_entry(self, corpus_id,
                            name=None, path=None, igt_count=None):
        entry = self.index['corpora'].get(
            corpus_id,
            {'name': None, 'path': None, 'igt_count': None, 'languages': {}}
        )
        if name is not None: entry['name'] = name
        if path is not None: entry['path'] = path
        if igt_count is not None: entry['igt_count'] = igt_count
        self.index['corpora'][corpus_id] = entry
        _dump_index(self.index, self.path)

    def _get_index_entry(self, corpus_id):
        entry = self.index['corpora'].get(corpus_id)
        if entry is None:
            raise SleipnirDbError('Index entry missing: %s' % corpus_id)
        return entry

    def _corpus_path(self, corpus_id):
        entry = self._get_index_entry(corpus_id)
        return os.path.join(self.path, entry['path'])

    def _get_name(self, corpus_id):
        return self._get_index_entry(corpus_id).get('name', '(untitled)')

    def _read_igts(self, corpus_id, ids=None):
        cpath = self._corpus_path(corpus_id)
        cindex = _load_index(cpath)
        igts = cindex['igts']
        if ids is not None:
            igtidx = cindex['igt_index']
            missing = [_id for _id in ids if _id not in igtidx]
            if missing:
                raise SleipnirDbError(
                    'Requested IGTs not found: {}'.format(', '.join(missing)),
                    status_code=404
                )
            idxs = map(igtidx.__getitem__, ids)
            igts = [igts[idx] for idx in idxs]
        return [_jsonload(os.path.join(cpath, igt['path'])) for igt in igts]

    def _build_corpus_dict(self, corpus_id, ids=None):
        cindex = _load_index(self._corpus_path(corpus_id))
        xcd = {}
        if 'namespaces' in cindex: xcd['namespaces'] = cindex['namespaces']
        if 'namespace' in cindex: xcd['namespace'] = cindex['namespace']
        if 'attributes' in cindex: xcd['attributes'] = cindex['attributes']
        if 'metadata' in cindex: xcd['metadata'] = cindex['metadata']
        xcd['igts'] = self._read_igts(corpus_id, ids=ids)
        return xcd

    def list_corpora(self):
        corpora = []
        for corpus_id, entry in self.index['corpora'].items():
            corpus_entry = {
                'id': corpus_id,
                'name': self._get_name(corpus_id),
                'igt_count': entry.get('igt_count', -1)
            }
            corpora.append(corpus_entry)
        return corpora

    def corpus_summary(self, corpus_id):
        cindex = _load_index(self._corpus_path(corpus_id))
        languages = defaultdict(lambda: defaultdict(int))
        for igt in cindex['igts']:
            lgcode = igt.get('language_code','und')
            lgname = igt.get('language_name', '???')
            languages[lgcode][lgname] += 1
        return {
            'id': corpus_id,
            'name': self._get_name(corpus_id),
            'igt_count': len(cindex['igts']),
            'languages': languages,
            'igts': [
                {'id': igt['id'], 'tier_count': igt.get('tier_count', -1)}
                for igt in cindex['igts']
            ]
        }

    def fetch_raw_corpus(self, corpus_id, mimetype):
        if mimetype == 'application/json':
            return json.dumps(self._build_corpus_dict(corpus_id), indent=2)
        else:
            raise SleipnirDbError(
                'Unsupported mimetype for raw corpus: %s' % mimetype
            )

    def get_corpus(self, corpus_id, ids=None):
        xc = xigtjson.decode(self._build_corpus_dict(corpus_id, ids=ids))
        return xc

    def get_igts(self, corpus_id, ids=None, paths=None):
        igts = list(
            map(xigtjson.decode_igt, self._read_igts(corpus_id, ids=ids))
        )
        if paths is not None:
            # queries are a conjunction (all have to match)
            matched_igts = []
            for igt in igts:
                matched = True
                for p in paths:
                    objs = xp.findall(igt, p)
                    if objs:
                        md = Metadata(
                            type='QueryResult',
                            attributes={'queryType': 'path', 'query': p}
                        )
                        for obj in objs:
                            if isinstance(obj, Item):
                                md.append(Meta(attributes={
                                    'tier': obj.tier.id,
                                    'item': obj.id
                                }))
                        igt.metadata.append(md)
                    else:
                        matched = False
                if matched:
                    matched_igts.append(igt)
            igts = matched_igts
        return igts

    # get_igt() just uses the default from SleipnirDatabaseInterface

    def add_corpus(self, xc, name=None):
        _validate_corpus(xc)
        tmp_cdir, igt_count = _make_corpus_directory(xc)

        # update main index
        while True:
            corpus_id = _make_new_id(6)
            if corpus_id not in self.index['corpora']:
                break
        cdir = os.path.join('data', corpus_id)
        shutil.move(tmp_cdir, os.path.join(self.path, cdir))
        if name is None:
            name = corpus_id
        self._update_index_entry(corpus_id, name, cdir, igt_count)

        return {'id': corpus_id, 'igt_count': igt_count}

    def add_igt(self, corpus_id, igt):
        if igt.id is None:
            raise SleipnirDbError(
                'IGTs must have an ID', status_code=400
            )
        cindex = _add_igt(igt, self._corpus_path(corpus_id))
        self._update_index_entry(corpus_id, igt_count=len(cindex['igts']))

        return {'id': igt.id, 'tier_count': len(igt)}

    # disable this one
    # def set_corpus(self, corpus_id, xc):
    #     raise NotImplementedError()

    def set_igt(self, corpus_id, igt_id, igt):
        if igt is None:
            raise SleipnirDbError(
                'Cannot assign empty IGT; delete the IGT instead.'
            )
        # ensure new igt's ID maps the target
        if igt.id is None:
            try:
                igt.id = igt_id
            except ValueError:
                raise SleipnirDbError(
                    'Invalid ID: {}'.format(igt_id),
                    status_code=400
                )
        elif igt.id != igt_id:
            raise SleipnirDbError(
                'Igt ID must match requested ID: {} != {}'
                .format(str(igt.id), igt_id),
                status_code=400
            )
        cdir = self._corpus_path(corpus_id)
        cindex = _load_index(cdir)
        igt_entry_idx = cindex['igt_index'].get(igt.id)
        if igt_entry_idx is None:  # target doesn't exist; just add
            _add_igt(igt, cdir, cindex=cindex)
            created = True
        else:  # target exists; replace
            igt_entry = cindex['igts'][igt_entry_idx]
            igt_path = os.path.join(cdir, igt_entry['path'])
            _jsondump(xigtjson.encode_igt(igt), igt_path)
            igt_entry['tier_count'] = len(igt)
            created = False
        _dump_index(cindex, cdir)
        self._update_index_entry(corpus_id, igt_count=len(cindex['igts']))

        return {'id': igt_id, 'created': created}

    def del_corpus(self, corpus_id):
        path = self._corpus_path(corpus_id)
        try:
            shutil.rmtree(path)
        except OSError:
            raise SleipnirDbError('Could not delete corpus: %s' % corpus_id)
        del self.index['corpora'][corpus_id]
        _dump_index(self.index, self.path)

    def del_igt(self, corpus_id, igt_id):
        cdir = self._corpus_path(corpus_id)
        cindex = _load_index(cdir)
        try:
            igt_entry_idx = cindex['igt_index'][igt_id]
            igt_entry = cindex['igts'][igt_entry_idx]
            path = os.path.join(cdir, igt_entry['path'])
            os.remove(path)
            del cindex['igts'][igt_entry_idx]
            del cindex['igt_index'][igt_id]
        except (KeyError, IndexError, OSError):
            raise SleipnirDbError(
                'Error removing IGT "{}" in corpus "{}"'
                .format(igt_id, corpus_id)
            )
        _refresh_igt_index(cindex)
        _dump_index(cindex, cdir)
        self._update_index_entry(corpus_id, igt_count=len(cindex['igts']))

def _validate_corpus(xc):
    for igt in xc:
        if igt.id is None:
            raise SleipnirError('Each IGT must have an ID.', status_code=400)

def _jsonload(path, **kwargs):
    try:
        return json.load(gzip.open(path, 'rt'), **kwargs)
    except OSError:
        raise SleipnirDbError('JSON file not found.')
    except json.JSONDecodeError:
        raise SleipnirDbError('File is not valid JSON data.')

def _jsondump(obj, path, **kwargs):
    if 'indent' not in kwargs: kwargs['indent'] = 2
    try:
        return json.dump(obj, gzip.open(path, 'wt'), **kwargs)
    except OSError:
        raise SleipnirDbError('Could not write JSON file.')

def _load_index(d): return _jsonload(os.path.join(d, 'index.json.gz'))
def _dump_index(i, d): return _jsondump(i, os.path.join(d, 'index.json.gz'))

def _make_new_id(size):
    return urlsafe_b64encode(uuid4().bytes)[:size].decode('ascii')

def _make_corpus_directory(xc):
    cdir = mkdtemp()
    # add IGT files
    igts = list(xc)
    # corpus index is corpus info w/ mapping to IGT files instead of IGTs
    xc.clear()
    cindex = xigtjson.encode(xc)
    cindex['igt_index'] = {}
    cindex['igts'] = []
    for igt in igts:
        _add_igt(igt, cdir, cindex, False)
    # refresh igt ID to path mapping once at the end
    _refresh_igt_index(cindex)
    _dump_index(cindex, cdir)
    return cdir, len(igts)

def _add_igt(igt, cdir, cindex=None, refresh=True):
    if cindex is None:
        cindex = _load_index(cdir)

    if igt.id in cindex['igt_index']:
        raise SleipnirDbError(
            'Igt ID "{}" already exists in corpus.'.format(igt.id),
        )

    while True:
        fn = '%s.json.gz' % _make_new_id(4)
        igtpath = os.path.join(cdir, fn)
        if not os.path.exists(igtpath):
            break
    _jsondump(xigtjson.encode_igt(igt), igtpath)
    lgcode, lgname = _igt_lang_info(igt)
    cindex['igts'].append({
        'id': igt.id,
        'tier_count': len(igt),
        'language_code': lgcode,
        'language_name': lgname,
        'path': fn
    })
    if refresh:
        _refresh_igt_index(cindex)
        _dump_index(cindex, cdir)
    # return the updated cindex so the caller can see the effect (in case
    # it didn't pass in a cindex)
    return cindex

def _igt_lang_info(igt):
    code = xp.find(igt, 'metadata//dc:subject/@olac:code').replace(':', '-')
    name = xp.find(igt, 'metadata//dc:subject/text()')
    return (code.lower(), name or '')

def _refresh_igt_index(cindex):
    igt_index = {}
    for i, igt in enumerate(cindex['igts']):
        igt_index[igt['id']] = i
    cindex['igt_index'] = igt_index
