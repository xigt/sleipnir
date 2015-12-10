
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
        if not index or 'files' not in index:
            raise SleipnirDbError('Database index is malformed.')
        self.index = index

    def _update_index_entry(self, corpus_id, xc, name=None, path=None):
        entry = self._get_index_entry(corpus_id)
        entry['igt_count'] = len(xc)
        if name is not None: entry['name'] = name
        if path is not None: entry['path'] = path
        self.index['files'][corpus_id] = entry
        try:
            json.dump(self.index, open(self._index_path, 'w'))
        except OSError:
            raise SleipnirDbError('Could not write database index.')

    def _get_index_entry(self, corpus_id):
        entry = self.index['files'].get(corpus_id)
        if entry is None:
            raise SleipnirDbError('Corpus entry missing: %s' % corpus_id)
        return entry

    def _load_corpus(self, entry):
        return xigtxml.load(self._corpus_filename(entry))

    def _save_corpus(self, xc, entry):
        xigtxml.dump(self._corpus_filename(entry), xc)

    def _corpus_filename(self, entry):
        return os.path.join(self.path, entry['path'])

    def list_corpora(self):
        corpora = []
        for f_id, entry in self.index['files'].items():
            corpora.append({
                'id': f_id,
                'name': _get_name(entry),
                'igt_count': entry.get('igt_count', -1)
            })
        return corpora

    def corpus_summary(self, corpus_id):
        entry = self._get_index_entry(corpus_id)
        xc = self._load_corpus(entry)
        return {
            'name': _get_name(entry),
            'igt_count': len(xc),
            'igt_ids': [igt.id for igt in xc]
        }

    def fetch_raw_corpus(self, corpus_id, mimetype):
        entry = self._get_index_entry(corpus_id)
        if mimetype == 'application/xml':
            return open(self._corpus_filename(entry)).read()
        else:
            raise SleipnirDbError(
                'Unsupported mimetype for raw corpus: %s' % mimetype
            )

    def get_corpus(self, corpus_id):
        entry = self._get_index_entry(corpus_id)
        corpus = self._load_corpus(entry)
        return corpus

    def get_igts(self, corpus_id, ids=None, matches=None):
        entry = self._get_index_entry(corpus_id)
        xc = self._load_corpus(entry)
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

    def add_corpora(self, xcs):
        for xc in xcs:
            print(xc)

    def add_igts(self, corpus_id, igts):
        entry = self._get_index_entry(corpus_id)
        xc = self._load_corpus(entry)
        try:
            for igt in igts:
                xc.append(igt)
        except XigtError:
            raise SleipnirDbError(
                'Igt ID "{}" already exists in corpus {}.'
                .format(igt.id, corpus_id),
            )
        self._save_corpus(xc, entry)
        self._update_index_entry(corpus_id, xc)
        return {'igt_count': len(xc)}

    def set_corpus(self):
        pass

    def set_igt(self, corpus_id, igt_id, igt):
        entry = self._get_index_entry(corpus_id)
        xc = self._load_corpus(entry)
        cur_igt = xc.get(igt_id)
        if igt is not None:
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
            if cur_igt is None:
                # target doesn't exist; append
                xc.append(igt)
            else:
                # target exists; replace
                idx = xc.index(cur_igt)
                xc[idx] = igt
        elif cur_igt:
            # empty payload, non-empty target; delete the target IGT
            xc.remove(cur_igt)
        self._save_corpus(xc, entry)
        _update_index_entry(corpus_id, xc)
        return json.jsonify({'success': True, 'igt_count': len(xc)})

    def del_corpus(self, corpus_id):
        pass

    def del_igt(self, corpus_id, igt_id):
        pass

def _get_name(entry):
    return entry.get('name', '(untitled)')
