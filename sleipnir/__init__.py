
from flask import Blueprint

v1 = Blueprint('sleipnir', __name__)

from sleipnir import config
# blueprint.config['DATABASE'] = config.DATABASE
# blueprint.config['DATABASE_PATH'] = config.DATABASE_PATH

dbi = None
if config.DATABASE == 'filesystem':
    from sleipnir.interfaces import FileSystemDbi
    dbi = FileSystemDbi(config.DATABASE_PATH)
else:
    raise ValueError('Invalid database type: {}'.format(config.DATABASE))


# the following imports are circular; do them at the end!

import sleipnir.views
