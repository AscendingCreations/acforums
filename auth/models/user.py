#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Author(s):
#  - Andrew Wheeler <lordsatin@hotmail.com>
#  - S.J.R. van Schaik <stephan@synkhronix.com>
from sqlalchemy_utils import EmailType, PasswordType
from flask import abort, current_app
from flask_login import current_user, LoginManager, UserMixin
from flask_authz import Authz, SecurityContext

from datetime import datetime

from .model import db

login_manager = LoginManager()
authz = Authz()

user_groups = db.Table('user_groups',
	db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
	db.Column('group_id', db.Integer, db.ForeignKey('groups.id'))
)

class User(db.Model, UserMixin, SecurityContext):
	__tablename__ = 'users'

	id = db.Column(db.Integer, primary_key=True)
	email_id = db.Column(db.Integer, db.ForeignKey('emails.id'))
	anonymous = db.Column(db.Boolean(), default=False)
	activated = db.Column(db.Boolean(), default=False)
	username = db.Column(db.String(256), unique=True)
	display = db.Column(db.String(256), unique=True)
	password = db.Column(PasswordType(onload=lambda **kwargs: dict(
			schemes=current_app.config.get('PASSWORD_SCHEMES', ['bcrypt']),
			**kwargs
		)))
	first_name = db.Column(db.String(64))
	last_name = db.Column(db.String(64))
	title = db.Column(db.String(64), default='New Member')
	unreadpms = db.Column(db.Integer(), default=0)
	warningpoints = db.Column(db.Integer(), default=0)
	invisible = db.Column(db.Boolean(), default=False)
	lastactive = db.Column(db.DateTime, default=datetime.utcnow())
	regdate = db.Column(db.DateTime, default=datetime.utcnow())
	postnum = db.Column(db.Integer(), default=0)
	threadnum = db.Column(db.Integer(), default=0)
	signature = db.Column(db.String(512), default='')
	timezone =  db.Column(db.String(64) , default='UTC')
	banned = db.Column(db.Boolean(), default=False)
	deleted = db.Column(db.Boolean(), default=False)
	loginattempts = db.Column(db.Integer(), default=0)
	loginlasttry = db.Column(db.DateTime, default=datetime.utcnow())
	warning_points = db.Column(db.Integer(), default=0)
	issixteen = db.Column(db.Boolean(), default=False)
	avatarconfirm = db.Column(db.Boolean(), default=False)
	loginconfirm = db.Column(db.Boolean(), default=False)
	displayconfirm = db.Column(db.Boolean(), default=False)
	nameconfirm = db.Column(db.Boolean(), default=False)
	titleconfirm = db.Column(db.Boolean(), default=False)
	sigconfirm = db.Column(db.Boolean(), default=False)
	hideprofile = db.Column(db.Boolean(), default=False)
	termsagree = db.Column(db.Boolean(), default=False)
	privacyagree = db.Column(db.Boolean(), default=False)

	email = db.relationship('Email', foreign_keys='User.email_id', post_update=True)
	groups = db.relationship('Group', secondary=user_groups, back_populates='users')

	@staticmethod
	def has(token):
		if db.session.query(db.exists().where(db.and_(
			UserPermission.token==token,
			UserPermission.user_id==current_user.id))).scalar():
			return True

	def __repr__(self):
		return str(self.display)

	def get_id(self):
		return str(self.id)

	def is_authenticated(self):
		return not self.anonymous

	def is_active(self):
		return not self.anonymous and self.activated

	def is_anonymous(self):
		return self.anonymous

	def in_group(self, name):
		return db.session.query(db.exists().where(db.and_(
			Group.name==name.lower(),
			Group.id==user_groups.c.group_id,
			user_groups.c.user_id==current_user.id))).scalar()

class UserPermission(db.Model):
	__tablename__ = 'user_permissions'

	id = db.Column(db.Integer, primary_key=True)
	user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
	token = db.Column(db.String)

	user = db.relationship('User',
		backref=db.backref('permissions', cascade='all, delete', lazy='dynamic'))

class Email(db.Model):
	__tablename__ = 'emails'

	id = db.Column(db.Integer, primary_key=True)
	user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
	email = db.Column(EmailType, unique=True)

	user = db.relationship('User',
		backref=db.backref('emails', cascade='all, delete',
			lazy='dynamic'), foreign_keys='Email.user_id')

	def __repr__(self):
		return str(self.email)

class Group(db.Model, SecurityContext):
	__tablename__ = 'groups'

	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String, unique=True)
	display = db.Column(db.String, unique=True)

	users = db.relationship('User', secondary=user_groups, back_populates='groups')

	@staticmethod
	def has(token):
		if db.session.query(db.exists().where(db.and_(
				GroupPermission.token==token,
				GroupPermission.group_id==Group.id,
				Group.id==user_groups.c.group_id,
				user_groups.c.user_id==current_user.id))).scalar():
			return True
		
		return User.has(token)

class GroupPermission(db.Model):
	__tablename__ = 'group_permissions'

	id = db.Column(db.Integer, primary_key=True)
	group_id = db.Column(db.Integer, db.ForeignKey('groups.id'))
	token = db.Column(db.String)

	group = db.relationship('Group',
		backref=db.backref('permissions', cascade='all, delete', lazy='dynamic'))

class Warning(db.Model):
	__tablename__ = 'warnings'

	id = db.Column(db.Integer, primary_key=True)
	user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
	date = db.Column(db.DateTime, default=datetime.utcnow())
	message = db.Column(db.String(256), default='')
	points = db.Column(db.Integer, default=1)
	issuer_id = db.Column(db.Integer, db.ForeignKey('users.id'))

	user = db.relationship('User',
		backref=db.backref('user_warnings', cascade='all, delete', lazy='dynamic'),
		foreign_keys='Warning.user_id')
	issuer = db.relationship('User',
		backref=db.backref('warnings_issued', cascade='all, delete', lazy='dynamic'),
			foreign_keys='Warning.issuer_id')

class PM(db.Model):
	__tablename__ = 'private_messages'

	id = db.Column(db.Integer, primary_key=True)
	user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
	sender_id = db.Column(db.Integer, db.ForeignKey('users.id'))
	date = db.Column(db.DateTime, default=datetime.utcnow())
	title = db.Column(db.String(256))
	message = db.Column(db.Text, default='')
	read = db.Column(db.Boolean(), default=False)

	user = db.relationship('User',
		backref=db.backref('user_pms', cascade='all, delete', lazy='dynamic'),
		foreign_keys='PM.user_id')
	sender = db.relationship('User',
		backref=db.backref('sent_pms', cascade='all, delete', lazy='dynamic'),
			foreign_keys='PM.sender_id')

class UserOnline(object):
	id = 0
	display = ''
	
	def __init__(self, id, display):
		self.id = id
		self.display = display

@login_manager.user_loader
def load_user(user_id):
	return User.query.get(user_id)

@authz.permission_denied
def on_permission_denied(*args, **kwargs):
	abort(403)

@authz.user_loader
def user_loader():
	return current_user

login_manager.anonymous_user = lambda: User.query.filter_by(anonymous=True).first()
login_manager.session_protection = "strong"
login_manager.login_view = 'user.sign_in'
login_manager.login_message_category = 'info'

