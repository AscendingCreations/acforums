#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Author(s):
#  - Andrew Wheeler <lordsatin@hotmail.com>
#  - S.J.R. van Schaik <stephan@synkhronix.com>
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask import current_app
import redis

db = SQLAlchemy()
migrate = Migrate()
pool = redis.ConnectionPool(host='localhost',  port=6379, max_connections=100, db=0)
rdb = redis.StrictRedis(connection_pool=pool)