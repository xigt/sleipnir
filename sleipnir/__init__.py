
from flask import Flask
app = Flask(__name__)

import sleipnir.config
app.config['DATABASE'] = config.DATABASE
app.config['DATABASE_PATH'] = config.DATABASE_PATH

if config.DATABASE == 'filesystem':
    import sleipnir.interfaces.filesystem as dbi
    dbi.app = app
else:
    raise ValueError('Invalid database type: {}'.format(config.DATABASE))

import sleipnir.views  # do this at the end!
