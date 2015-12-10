
'''
These are the exposed API URIs for Sleipnir

    (! means "not implemented")

    GET requests
     /corpora
     /corpora/<corpus_id>
     /corpora/<corpus_id>/summary
     /corpora/<corpus_id>/igts
     /corpora/<corpus_id>/igts/<igt_id>

    POST requests
     !/corpora
     /corpora/<corpus_id>/igts

    PUT requests
     !/corpora/<corpus_id>
     /corpora/<corpus_id>/igts/<igt_id>

    DELETE requests
     !/corpora/<corpus_id>
     !/corpora/<corpus_id>/igts/<igt_id>

    PATCH requests
     !/corpora/<corpus_id>
     !/corpora/<corpus_id>/igts/<igt_id>
'''

import tempfile
import subprocess

from flask import request, Response, abort, json

from xigt.codecs import xigtxml, xigtjson

from sleipnir import v1, dbi
from sleipnir.errors import SleipnirError

accept_mimetypes = ['application/xml', 'application/json']


#
# GET REQUESTS
#

@v1.route('/corpora')
def list_corpora():
    corpora = dbi.list_corpora()
    return json.jsonify(
        corpus_count=len(corpora),
        corpora=corpora
    )

@v1.route('/corpora/<corpus_id>')
def get_corpus(corpus_id):
    mimetype = _json_or_xml()
    if mimetype in getattr(dbi, 'raw_formats', []):
        corpus = dbi.fetch_raw_corpus(corpus_id, mimetype)
    else:
        xc = dbi.get_corpus(corpus_id)
        corpus = _serialize_corpus(xc, mimetype)
    return Response(corpus, mimetype=mimetype)

@v1.route('/corpora/<corpus_id>/summary')
def corpus_summary(corpus_id):
    return json.jsonify(dbi.corpus_summary(corpus_id))

@v1.route('/corpora/<corpus_id>/igts')
def get_igts(corpus_id):
    igt_ids = _get_arg_list('id', delim=',')
    matches = _get_arg_list('match')
    igts = list(map(xigtjson.encode_igt,
                    dbi.get_igts(corpus_id, ids=igt_ids, matches=matches)))
    return json.jsonify(igts=igts, igt_count=len(igts))

@v1.route('/corpora/<corpus_id>/igts/<igt_id>')
def get_igt(corpus_id, igt_id):
    igt = dbi.get_igt(corpus_id, igt_id)
    return json.jsonify(xigtjson.encode_igt(igt))

#
# POST REQUESTS
#

@v1.route('/corpora', methods=['POST'])
def post_corpora():
    corpora = _get_request_corpora()
    result = dbi.add_corpora(corpora)
    return json.jsonify(**result)

@v1.route('/corpora/<corpus_id>/igts', methods=['POST'])
def post_igts(corpus_id):
    igts = []
    data = request.get_json()
    if data:
        igts = [xigtjson.decode_igt(x) for x in data.get('igts', [])]
    result = dbi.add_igts(corpus_id, igts)
    return json.jsonify(**result)

#
# PUT REQUESTS
#

@v1.route('/corpora/<corpus_id>', methods=['PUT'])
def put_corpus():
    xcs = _get_request_corpora()
    if len(xcs) != 1:
        raise SleipnirError(
            'Only one corpus may be assigned to an ID', status_code=400
        )
    result = dbi.set_corpus(corpus_id, xcs[0])
    return json.jsonify(**result)

@v1.route('/corpora/<corpus_id>/igts/<igt_id>', methods=['PUT'])
def put_igt(corpus_id, igt_id):
    igt = None
    data = request.get_json()
    if data:
        igt = xigtjson.decode_igt(data)
    if not igt:  # igt is None or empty {}
        raise SleipnirError(
            'Only one IGT may be assigned to an ID', status_code=400
        )
    result = dbi.set_igt(corpus_id, igt_id, igt)
    return json.jsonify(**result)

#
# DELETE REQUESTS
#

@v1.route('/corpora/<corpus_id>', methods=['DELETE'])
def delete_corpus(corpus_id):
    result = dbi.del_corpus(corpus_id)
    return json.jsonify(**result)

@v1.route('/corpora/<corpus_id>/igts/<igt_id>', methods=['DELETE'])
def delete_igt(corpus_id, igt_id):
    result = dbi.del_igt(corpus_igt, igt_id)
    return json.jsonify(**result)

#
# PATCH REQUESTS
#

@v1.route('/corpora/<corpus_id>', methods=['PATCH'])
def patch_corpus():
    abort(501)

@v1.route('/corpora/<corpus_id>/igts/<igt_id>', methods=['PATCH'])
def patch_igt():
    abort(501)

#
# ERRORS
#

@v1.errorhandler(SleipnirError)
def handle_sleipnirerror(error):
    response = json.jsonify(error.to_dict())
    response.status_code = error.status_code
    return response

#
# HELPERS
#

# thanks: http://flask.pocoo.org/snippets/45/
def _json_or_xml():
    mimetype = 'application/json'
    best = request.accept_mimetypes.best_match(accept_mimetypes)
    if (best == 'application/xml' and
            request.accept_mimetypes[best] >
            request.accept_mimetypes['application/json']):
        mimetype = 'application/xml'
    return mimetype

def _get_arg_list(param, delim=None):
    xlist = None
    if param in request.args:
        xlist = list(request.args.getlist(param))
        if delim is not None:
            xlist = [x for xstring in xlist for x in xstring.split(delim)]
    return xlist

def _get_request_corpus():
    xc = None
    if request.mimetype == 'application/json':
        data = request.get_json()
        if data and data.get('corpus'):
            xc = xigtjson.decode(data['corpus'])
    return xc

def _get_request_corpora():
    xcs = []
    for f in request.files['files']:
        xcs.append(_decode_corpus(f.read(), f.mimetype))
    if request.mimetype == 'application/json':
        data = request.get_json()
        if data:
            for c in data.get('corpora', []):
                xcs.append(xigtjson.decode(c))
    return xcs

def _decode_corpus(data, mimetype):
    xc = None
    if mimetype == 'application/json':
        xc = xigtjson.decode(json.loads(data))
    elif mimetype == 'application/xml':
        xc = xigtxml.loads(data)
    else:
        raise SleipnirError(
            'Unsupported filetype: %s' % mimetype, status_code=400
        )
    _validate_corpus(xc)
    return xc

def _validate_corpus(xc):
    for igt in xc:
        if igt.id is None:
            raise SleipnirError('Each IGT must have an ID.', status_code=400)

# def _file_mimetype(f):
#     mimetype = None
#     with tempfile.TemporaryDirectory() as tmpdir:
#         fn = os.path.join(tmpdir, 'tmpfile')
#         f.save(fn)
#         mimetype = subprocess.Popen(
#             ['file', fn, '--mime-type', '-b'],
#             stdout=subprocess.PIPE
#         ).stdout.read().strip()
#     # tempdir and tempfile should be destroyed now
#     return mimetype

def _serialize_corpus(xc, mimetype='application/json'):
    if mimetype == 'application/xml':
        return xigtxml.dumps(xc, indent=None)
    elif mimetype == 'application/json':
        return xigtjson.dumps(xc, indent=None)
    elif mimetype is None:
        return xc
    # else: raise exception
    return None
