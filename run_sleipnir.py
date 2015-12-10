#!/usr/bin/env python

from flask import Flask
import sleipnir

app = Flask(__name__)
app.register_blueprint(sleipnir.v1, url_prefix='/v1')
app.run(debug=True)
