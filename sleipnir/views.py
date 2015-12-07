
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

from flask import request, Response, abort
from sleipnir import blueprint, dbi
from sleipnir.errors import (
    SleipnirDbError,
    SleipnirDbBadRequestError,
    SleipnirDbNotFoundError,
    SleipnirDbConflictError,
)

#
# GET REQUESTS
#

@blueprint.route('/corpora')
def list_corpora():
    return dbi.corpora()

@blueprint.route('/corpora/<corpus_id>')
def get_corpus(corpus_id):
    mimetype = _json_or_xml()
    contents = ''
    if mimetype in getattr(dbi, 'raw_formats', []):
        contents = dbi.fetch_raw(corpus_id, mimetype)
    else:
        contents = dbi.get_corpus(corpus_id, mimetype)
    return Response(contents, mimetype=mimetype)

@blueprint.route('/corpora/<corpus_id>/summary')
def corpus_summary(corpus_id):
    return dbi.corpus_summary(corpus_id)

@blueprint.route('/corpora/<corpus_id>/igts')
def get_igts(corpus_id):
    igt_ids = _get_arg_list('id', delim=',')
    matches = _get_arg_list('match')
    return dbi.get_igts(
        corpus_id, igt_ids=igt_ids, matches=matches, mimetype=_json_or_xml()
    )

@blueprint.route('/corpora/<corpus_id>/igts/<igt_id>')
def get_igt(corpus_id, igt_id):
    igt_ids = [igt_id]
    return dbi.get_igts(
        corpus_id, igt_ids=igt_ids, mimetype=_json_or_xml()
    )

#
# POST REQUESTS
#

@blueprint.route('/corpora', methods=['POST'])
def post_corpora():
    fs = request.files['files']
    return dbi.add_corpora(fs)

@blueprint.route('/corpora/<corpus_id>/igts', methods=['POST'])
def post_igts(corpus_id):
    try:
        return dbi.add_igts(
            corpus_id,
            request.data,
            request.content_type
        )
    except (AttributeError, SleipnirDbBadRequestError):
        abort(400)  # no data or bad data
    except SleipnirDbNotFoundError:
        abort(404)
    except SleipnirDbConflictError:
        abort(409)

#
# PUT REQUESTS
#

@blueprint.route('/corpora/<corpus_id>', methods=['PUT'])
def put_corpus():
    abort(501)

@blueprint.route('/corpora/<corpus_id>/igts/<igt_id>', methods=['PUT'])
def put_igt(corpus_id, igt_id):
    try:
        return dbi.set_igt(
            corpus_id,
            igt_id,
            request.data,
            request.content_type
        )
    except (AttributeError, SleipnirDbBadRequestError):
        abort(400)  # no data or bad data
    except SleipnirDbNotFoundError:
        abort(404)
    except SleipnirDbConflictError:
        abort(409)

#
# DELETE REQUESTS
#

@blueprint.route('/corpora/<corpus_id>', methods=['DELETE'])
def delete_corpus():
    abort(501)

@blueprint.route('/corpora/<corpus_id>/igts/<igt_id>', methods=['DELETE'])
def delete_igt():
    abort(501)

#
# PATCH REQUESTS
#

@blueprint.route('/corpora/<corpus_id>', methods=['PATCH'])
def patch_corpus():
    abort(501)

@blueprint.route('/corpora/<corpus_id>/igts/<igt_id>', methods=['PATCH'])
def patch_igt():
    abort(501)


# thanks: http://flask.pocoo.org/snippets/45/
def _json_or_xml():
    mimetype = 'application/json'
    best = request.accept_mimetypes \
        .best_match(['application/xml', 'application/json'])
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
