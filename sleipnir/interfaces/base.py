
class SleipnirDatabaseInterface(object):
    raw_formats = []
    def __init__(self, path):
        self.path = path
    def list_corpora(self): raise NotImplementedError()
    def corpus_summary(self, cid): raise NotImplementedError()
    def fetch_raw_corpus(self, cid): raise NotImplementedError()
    def get_corpus(self, cid, **kwargs): raise NotImplementedError()
    def get_igts(self, cid, **kwargs): raise NotImplementedError()
    def get_igt(self, cid, iid, **kwargs):
        return self.get_igts(cid, ids=[iid])[0]
    def add_corpora(self, xcs, **kwargs): raise NotImplementedError()
    def add_igts(self, cid, igts, **kwargs): raise NotImplementedError()
    def set_corpus(self, cid, xc, **kwargs): raise NotImplementedError()
    def set_igt(self, cid, iid, igt, **kwargs): raise NotImplementedError()
    def delete_corpus(self, cid): raise NotImplementedError()
    def delete_igt(self, cid, iid): raise NotImplementedError()

