#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Author(s):
#  - Andrew Wheeler <lordsatin@hotmail.com>

from datetime import datetime

from .model import db
from .user import User

class Log(db.Model):
	__tablename__ = 'logs'

	id = db.Column(db.Integer, primary_key=True)
	event = db.Column(db.String(128), default='')
	type =  db.Column(db.Integer(), default=0)
	date = db.Column(db.DateTime, default=datetime.utcnow())
	user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

	user = db.relationship('User',
		backref=db.backref('users_logs', cascade='all, delete',
			lazy='dynamic'), foreign_keys='Log.user_id')

# rows = session.query(Congress).count()
# from sqlalchemy import func
# rows = session.query(func.count(Congress.id)).scalar()