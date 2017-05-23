#!/usr/bin/env python

from flask import Flask
import sleipnir

# maybe constrain this to known origins to avoid excessive requests
cors_origin = '*'

app = Flask(__name__)
app.register_blueprint(sleipnir.v1, url_prefix='/v1')

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', cors_origin)
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Accept,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    return response


app.run(debug=True)
