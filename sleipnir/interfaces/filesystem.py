
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
import json

from xigt import XigtCorpus, xigtpath as xp
from xigt.errors import XigtError
from xigt.codecs import xigtxml

from sleipnir.interfaces import SleipnirDatabaseInterface
from sleipnir.errors import SleipnirDbError

class FileSystemDbi(SleipnirDatabaseInterface):
    raw_formats = ['application/xml']

    def __init__(self, path):
        SleipnirDatabaseInterface.__init__(self, path)
        self._index_path = os.path.join(self.path, 'index.json')
        self.index = {'files': []}
        self._load_index()

    def _load_index(self):
        index = None
        try:
            index = json.load(open(self._index_path))
        except OSError:
            raise SleipnirDbError('Database index not found.')
        except json.JSONDecodeError:
            raise SleipnirDbError('Database index is not a valid JSON file.')
        if not index or 'files' not in index:
            raise SleipnirDbError('Database index is malformed.')
        self.index = index

    def _save_index(self):
        try:
            json.dump(self.index, open(self._index_path, 'w'))
        except OSError:
            raise SleipnirDbError('Could not write database index.')

    def _update_index_entry(self, corpus_id, xc, name=None, path=None):
        entry = self._get_index_entry(corpus_id)
        entry['igt_count'] = len(xc)
        if name is not None: entry['name'] = name
        if path is not None: entry['path'] = path
        self.index['files'][corpus_id] = entry
        self._save_index()

    def _get_index_entry(self, corpus_id):
        entry = self.index['files'].get(corpus_id)
        if entry is None:
            raise SleipnirDbError('Corpus entry missing: %s' % corpus_id)
        return entry

    def _make_new_index_entry(self, name=None):
        while True:
            corpus_id = urlsafe_b64encode(uuid4().bytes)[:-2].decode('ascii')
            if corpus_id not in self.index['files']:
                break
        entry = {'path': 'data/%s' % corpus_id}
        if name is not None:
            entry['name'] = name
        self.index['files'][corpus_id] = entry
        return corpus_id

    def _get_name(self, corpus_id):
        return self._get_index_entry(corpus_id).get('name', '(untitled)')

    def _load_corpus(self, corpus_id):
        return xigtxml.load(self._corpus_filename(corpus_id))

    def _save_corpus(self, corpus_id, xc):
        path = self._corpus_filename(corpus_id)
        xigtxml.dump(path, xc)
        self._update_index_entry(corpus_id, xc)

    def _corpus_filename(self, corpus_id):
        entry = self._get_index_entry(corpus_id)
        return os.path.join(self.path, entry['path'])

    def list_corpora(self):
        corpora = []
        for corpus_id, entry in self.index['files'].items():
            corpus_entry = {
                'id': corpus_id,
                'name': self._get_name(corpus_id),
                'igt_count': entry.get('igt_count', -1)
            }
            corpora.append(corpus_entry)
        return corpora

    def corpus_summary(self, corpus_id):
        xc = self._load_corpus(corpus_id)
        return self._generate_corpus_summary(corpus_id, xc)

    def _generate_corpus_summary(self, corpus_id, xc):
        return {
            'id': corpus_id,
            'name': self._get_name(corpus_id),
            'igt_count': len(xc),
            'igts': [{'id': igt.id} for igt in xc]
        }

    def fetch_raw_corpus(self, corpus_id, mimetype):
        if mimetype == 'application/xml':
            return open(self._corpus_filename(corpus_id)).read()
        else:
            raise SleipnirDbError(
                'Unsupported mimetype for raw corpus: %s' % mimetype
            )

    def get_corpus(self, corpus_id):
        corpus = self._load_corpus(corpus_id)
        return corpus

    def get_igts(self, corpus_id, ids=None, matches=None):
        xc = self._load_corpus(corpus_id)
        if ids is None:
            igts = list(xc.igts)
        else:
            igts = []
            for igt_id in ids:
                igt = xc.get(igt_id)
                if igt is not None:
                    igts.append(igt)
        if matches is not None:
            # matches are a disjunction (only one has to match)
            matcher = lambda i: any(xp.find(i, m) is not None for m in matches)
            igts = list(filter(matcher, igts))
        return igts

    # get_igt() just uses the default from SleipnirDatabaseInterface

    def add_corpus(self, xc, name=None):
        _validate_corpus(xc)
        corpus_id = self._make_new_index_entry(name=name)
        self._save_corpus(corpus_id, xc)
        return {'id': corpus_id, 'igt_count': len(xc)}

    def add_igt(self, corpus_id, igt):
        if igt.id is None:
            raise SleipnirDbError(
                'IGTs must have an ID', status_code=400
            )
        xc = self._load_corpus(corpus_id)
        try:
            xc.append(igt)
        except XigtError:
            raise SleipnirDbError(
                'Igt ID "{}" already exists in corpus {}.'
                .format(igt.id, corpus_id),
            )
        self._save_corpus(corpus_id, xc)
        return {'id': igt.id, 'tier_count': len(igt)}

    # disable this one
    # def set_corpus(self, corpus_id, xc):
    #     _validate_corpus(xc)
    #     created = corpus_id not in self.index['files']
    #     self._save_corpus(corpus_id, xc)
    #     return {'id': corpus_id, 'created': created}


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
        xc = self._load_corpus(corpus_id)
        cur_igt = xc.get(igt_id)
        if cur_igt is None:  # target doesn't exist; append
            created = True
            xc.append(igt)
        else:  # target exists; replace
            created = False
            idx = xc.index(cur_igt)
            xc[idx] = igt
        self._save_corpus(corpus_id, xc)
        return {'id': igt_id, 'created': created}

    def del_corpus(self, corpus_id):
        path = self._corpus_filename(corpus_id)
        try:
            os.remove(path)
        except OSError:
            raise SleipnirDbError('Could not delete corpus: %s' % corpus_id)
        del self.index['files'][corpus_id]
        self._save_index()

    def del_igt(self, corpus_id, igt_id):
        xc = self._load_corpus(corpus_id)
        try:
            del xc[igt_id]
        except KeyError:
            raise SleipnirDbError(
                'IGT "{}" not in corpus "{}"'.format(igt_id, corpus_id)
            )
        else:
            self._save_corpus(corpus_id, xc)

def _validate_corpus(xc):
    for igt in xc:
        if igt.id is None:
            raise SleipnirError('Each IGT must have an ID.', status_code=400)
