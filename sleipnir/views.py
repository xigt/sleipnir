
from flask import request, Response, abort
from sleipnir import blueprint, dbi

@blueprint.route('/corpora', methods=['GET'])
def list_corpora():
    return dbi.corpora()

@blueprint.route('/corpora', methods=['POST'])
def add_corpus():
    f = request.files['file']
    return dbi.add_corpus(f)

@blueprint.route('/corpora/<corpus_id>/summary')
def corpus_summary(corpus_id):
    return dbi.corpus_summary(corpus_id)

@blueprint.route('/corpora/<corpus_id>')
def get_corpus(corpus_id):
    mimetype = json_or_xml()
    contents = ''
    if mimetype in getattr(dbi, 'raw_formats', []):
        contents = dbi.fetch_raw(corpus_id, mimetype)
    else:
        contents = dbi.get_corpus(corpus_id, mimetype)
    return Response(contents, mimetype=mimetype)

@blueprint.route('/corpora/<corpus_id>', methods=['PATCH'])
def update_corpus(corpus_id):
    abort(501)

@blueprint.route('/corpora/<corpus_id>/igts', methods=['GET'])
def get_igts(corpus_id):
    igt_ids = get_arg_list('id', delim=',')
    matches = get_arg_list('match')
    return dbi.get_igts(
        corpus_id, igt_ids=igt_ids, matches=matches, mimetype=json_or_xml()
    )

@blueprint.route('/corpora/<corpus_id>/igts', methods=['POST'])
def add_igts(corpus_id):
    abort(501)

# thanks: http://flask.pocoo.org/snippets/45/
def json_or_xml():
    mimetype = 'application/json'
    best = request.accept_mimetypes \
        .best_match(['application/xml', 'application/json'])
    if (best == 'application/xml' and
            request.accept_mimetypes[best] >
            request.accept_mimetypes['application/json']):
        mimetype = 'application/xml'
    return mimetype

def get_arg_list(param, delim=None):
    xlist = None
    if param in request.args:
        xlist = list(request.args.getlist(param))
        if delim is not None:
            xlist = [x for xstring in xlist for x in xstring.split(delim)]
    return xlist
