#!/usr/bin/env python

from flask import Flask
import sleipnir

app = Flask(__name__)
app.register_blueprint(sleipnir.blueprint)
app.run(debug=True)
