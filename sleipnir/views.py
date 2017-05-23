
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
     /corpora
     /corpora/<corpus_id>/igts

    PUT requests
     !/corpora/<corpus_id>
     /corpora/<corpus_id>/igts/<igt_id>

    DELETE requests
     /corpora/<corpus_id>
     /corpora/<corpus_id>/igts/<igt_id>

    PATCH requests
     !/corpora/<corpus_id>
     !/corpora/<corpus_id>/igts/<igt_id>
'''

from functools import wraps

from flask import request, Response, abort, json, url_for

from xigt.codecs import xigtxml, xigtjson

from sleipnir import v1, dbi
from sleipnir.errors import SleipnirError

accept_mimetypes = ['application/xml', 'application/json']

#
# GET REQUESTS
#

# thanks: http://flask.pocoo.org/snippets/79/
def jsonp(func):
    """Wraps JSONified output for JSONP requests."""
    @wraps(func)
    def decorated_function(*args, **kwargs):
        callback = request.args.get('callback', False)
        if callback:
            if _json_or_xml() != 'application/json':
                raise SleipnirError('Cannot use JSONP with non-JSON data.')
            response = func(*args, **kwargs)
            response.set_data('{}({})'.format(
                str(callback),
                response.get_data(as_text=True)
            ))
            response.mimetype = 'application/javascript'
            return response
        else:
            return func(*args, **kwargs)
    return decorated_function

@v1.route('/corpora')
@jsonp
def list_corpora():
    corpora = dbi.list_corpora()
    for entry in corpora:
        entry['url'] = url_for('.get_corpus', corpus_id=entry['id'], _external=True)
        entry['summary_url'] = url_for('.corpus_summary', corpus_id=entry['id'], _external=True)
    return json.jsonify(
        corpus_count=len(corpora),
        corpora=corpora
    )

@v1.route('/corpora/<corpus_id>')
@jsonp
def get_corpus(corpus_id):
    mimetype = _json_or_xml()
    igt_ids = _get_arg_list('id', delim=',')
    if mimetype in getattr(dbi, 'raw_formats', []) and not igt_ids:
        corpus = dbi.fetch_raw_corpus(corpus_id, mimetype)
    else:
        xc = dbi.get_corpus(corpus_id, ids=igt_ids)
        corpus = _serialize_corpus(xc, mimetype)
    return Response(corpus, mimetype=mimetype)

@v1.route('/corpora/<corpus_id>/summary')
@jsonp
def corpus_summary(corpus_id):
    summary = dbi.corpus_summary(corpus_id)
    for igt in summary['igts']:
        igt['url'] = url_for(
            '.get_igt',
            corpus_id=corpus_id,
            igt_id=igt['id'],
            _external=True
        )
    return json.jsonify(summary)

@v1.route('/corpora/<corpus_id>/igts')
@jsonp
def get_igts(corpus_id):
    igt_ids = _get_arg_list('id', delim=',')
    paths = _get_arg_list('path')
    igts = list(map(xigtjson.encode_igt,
                    dbi.get_igts(corpus_id, ids=igt_ids, paths=paths)))
    return json.jsonify(igts=igts, igt_count=len(igts))

@v1.route('/corpora/<corpus_id>/igts/<igt_id>')
@jsonp
def get_igt(corpus_id, igt_id):
    igt = dbi.get_igt(corpus_id, igt_id)
    return json.jsonify(xigtjson.encode_igt(igt))

#
# POST REQUESTS
#

@v1.route('/corpora', methods=['POST'])
def post_corpus():
    print(request.data)
    xc = _get_request_corpus()
    name = request.args.get('name')
    result = dbi.add_corpus(xc, name=name)
    return json.jsonify(**result)

@v1.route('/corpora/<corpus_id>/igts', methods=['POST'])
def post_igt(corpus_id):
    igt = _get_request_igt()
    result = dbi.add_igt(corpus_id, igt)
    return json.jsonify(**result)

#
# PUT REQUESTS
#

# Maybe don't allow this one
# @v1.route('/corpora/<corpus_id>', methods=['PUT'])
# def put_corpus():
#     xc = _get_request_corpus()
#     result = dbi.set_corpus(corpus_id, xc)
#     if 'created' in result:
#         created = result['created']
#         del result['created']
#     created = result.get('created', False)

#     return '', 204

@v1.route('/corpora/<corpus_id>/igts/<igt_id>', methods=['PUT'])
def put_igt(corpus_id, igt_id):
    igt = _get_request_igt()
    result = dbi.set_igt(corpus_id, igt_id, igt)
    return '', 204

#
# DELETE REQUESTS
#

@v1.route('/corpora/<corpus_id>', methods=['DELETE'])
def delete_corpus(corpus_id):
    dbi.del_corpus(corpus_id)
    return '', 204

@v1.route('/corpora/<corpus_id>/igts/<igt_id>', methods=['DELETE'])
def delete_igt(corpus_id, igt_id):
    dbi.del_igt(corpus_id, igt_id)
    return '', 204

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

# request can have 1 file attachment, or alternatively the message body
# can be a XigtXML- or XigtJSON-encoded corpus.
def _get_request_corpus():
    xc = None
    files = request.files.getlist('file')
    if len(files) == 1:
        f = files[0]
        data = f.read()
        mimetype = f.mimetype
    elif len(files) > 1:
        raise SleipnirError('Only one file may be uploaded at a time.')
    else:
        data = request.data
        if not isinstance(data, str):
            data = data.decode()
        mimetype = request.mimetype
    if mimetype not in accept_mimetypes:
        raise SleipnirError(
            'Unsupported mimetype: %s' % mimetype, status_code=400
        )
    try:
        if mimetype == 'application/json':
            xc = xigtjson.loads(data)
        elif mimetype == 'application/xml':
            xc = xigtxml.loads(data)
    except:  # when Xigt has a parsing exception, use it here
        raise
        raise SleipnirError('Unparseable Xigt corpus.')
    return xc

def _get_request_igt():
    data = request.get_json()
    try:
        igt = xigtjson.decode_igt(data)
    except:  # when Xigt has a parsing exception, use it here
        raise SleipnirError('Unparseable Xigt IGT instance.')
    return igt

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
        return xigtxml.dumps(xc, indent=2)
    elif mimetype == 'application/json':
        return xigtjson.dumps(xc, indent=2)
    else:
        raise SleipnirError('Unsupported mimetype: %s' % mimetype)
