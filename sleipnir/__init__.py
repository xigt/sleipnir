
from flask import Blueprint

blueprint = Blueprint('sleipnir', __name__)

from sleipnir import config
# blueprint.config['DATABASE'] = config.DATABASE
# blueprint.config['DATABASE_PATH'] = config.DATABASE_PATH

if config.DATABASE == 'filesystem':
    import sleipnir.interfaces.filesystem as dbi
    dbi.DATABASE_PATH = config.DATABASE_PATH
else:
    raise ValueError('Invalid database type: {}'.format(config.DATABASE))

import sleipnir.views  # do this at the end!
