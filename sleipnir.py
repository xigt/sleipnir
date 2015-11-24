
import logging

from flask import Flask, url_for, safe_join, Response
from werkzeug import secure_filename
app = Flask(__name__)

from xigt import XigtCorpus, xigtpath as xp
from xigt.codecs import xigtxml, xigtjson

import interfaces.filesystem as dbi

import config
app.config['DATABASE_PATH'] = config.DATABASE_PATH

@app.route('/corpora')
def corpora():
    return dbi.corpora(app)

@app.route('/corpora/<corpus_id>')
def corpus(corpus_id):
    return dbi.corpus(app, corpus_id)

@app.route('/corpora/<corpus_id>/<igt_id>')
def igt(corpus_id, igt_id):
    return dbi.igt(app, corpus_id, igt_id)

if __name__ == '__main__':
    app.run(debug=True)
