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

class Category(db.Model):
	__tablename__ = 'categories'

	id = db.Column(db.Integer, primary_key=True)
	title = db.Column(db.String(64), unique=True)
	order = db.Column(db.Integer(), default=0)

class Board(db.Model):
	__tablename__ = 'boards'

	id = db.Column(db.Integer, primary_key=True)
	title = db.Column(db.String(64), unique=True)
	threads = db.Column(db.Integer(), default=0)
	order = db.Column(db.Integer(), default=0)
	post_count = db.Column(db.Integer(), default=0)
	desc = db.Column(db.String(256), default='')
	link = db.Column(db.String(256), default='')
	parent_id = db.Column(db.Integer, db.ForeignKey('boards.id'))
	category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
	last_id = db.Column(db.Integer, db.ForeignKey('posts.id'))
	last_post = db.relationship('Post', foreign_keys='Board.last_id',
		post_update=True)

	category = db.relationship('Category', order_by='Board.order',
		backref=db.backref('category_boards', order_by='Board.order',
			cascade='all, delete', lazy='dynamic'), foreign_keys='Board.category_id')
	parent = db.relationship('Board', backref=db.backref('board_boards',
		order_by='Board.order'), remote_side='Board.id')

class Thread(db.Model):
	__tablename__ = 'threads'

	id = db.Column(db.Integer, primary_key=True)
	title = db.Column(db.String(256), unique=True)
	sticky = db.Column(db.Boolean, default=False)
	post_count= db.Column(db.Integer(), default=0)
	creator_id = db.Column(db.Integer, db.ForeignKey('users.id'))
	board_id = db.Column(db.Integer, db.ForeignKey('boards.id'))
	last_post = db.Column(db.DateTime, default=datetime.utcnow())
	last_id = db.Column(db.Integer, db.ForeignKey('posts.id'))
	#the last post in the thread.for last post displayed via boards.
	last = db.relationship('Post', foreign_keys='Thread.last_id',
		post_update=True)

	creator = db.relationship('User',
		backref=db.backref('user_threads', cascade='all, delete',
			lazy='dynamic'), foreign_keys='Thread.creator_id')
	board = db.relationship('Board',
		backref=db.backref('board_threads', order_by='Thread.sticky, Thread.last_post',
			lazy='dynamic'), foreign_keys='Thread.board_id')

class Post(db.Model):
	__tablename__ = 'posts'

	id = db.Column(db.Integer, primary_key=True)
	message = db.Column(db.Text, default='')
	post_time = db.Column(db.DateTime, default=datetime.utcnow())
	edit_time = db.Column(db.DateTime, default=datetime.utcnow())
	creator_id = db.Column(db.Integer, db.ForeignKey('users.id'))
	editor_id = db.Column(db.Integer, db.ForeignKey('users.id'))
	thread_id = db.Column(db.Integer, db.ForeignKey('threads.id'))
	thread_post = db.Column(db.Boolean, default=False)

	creator = db.relationship('User',
		backref=db.backref('user_posts', cascade='all, delete',
			lazy='dynamic'), foreign_keys='Post.creator_id')
	editor = db.relationship('User',
		backref=db.backref('edited_posts', cascade='all, delete',
			lazy='dynamic'), foreign_keys='Post.editor_id')
	thread = db.relationship('Thread',
		backref=db.backref('thread_posts', cascade='all, delete',
			lazy='dynamic'), foreign_keys='Post.thread_id')