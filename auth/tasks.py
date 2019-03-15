#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Author(s):
#  - Andrew Wheeler <lordsatin@hotmail.com>
#
import flask
from celery import Celery
from celery.signals import worker_process_init
from flask import abort, Blueprint, flash, redirect
from flask import current_app, url_for
from flask import render_template, request
from flask_login import current_user
from flask_authz import rights
from .models import db, authz, Group, User, Email
from .models import Category, Board, Thread, Post
from .models import Warning , rdb, UserOnline, Log
from datetime import datetime, timedelta
from .log import create_log
from configobj import ConfigObj

config = ConfigObj('config.py')
celery = Celery(__name__, broker=config.get('CELERY_BROKER_URL'))

@celery.task
def send_async_email():
	print('send async email')

@celery.task
def delete_user(user_id):
	user = User.query.get(user_id) 
	board_last_reset = False
	thread_last_reset = False

	if not user:
		return

	for pm in user.user_pms:
		db.session.delete(pm)
	
	for pm in user.sent_pms:
		db.session.delete(pm)
	
	for warning in user.user_warnings:
		db.session.delete(warning)
		
	for post in user.user_posts:
		if post.thread_post == True:
			thread = post.thread
			board = thread.board

			for p in thread.thread_posts:
				p.creator.postnum -= 1

			thread.board.post_count -= thread.post_count
			thread.board.threads -= 1
			
			if thread.board.last_post.id == thread.last.id:
				board_last_reset = True
					
			db.session.delete(thread)
			db.session.commit()
			
			if board_last_reset:
				thread = Thread.query.filter_by(board_id=board.id). \
					order_by(Thread.last_post.desc(), Thread.id.desc()).first()
				board.last_post = thread.last
				db.session.commit()
				board_last_reset = False
		else:
			post.thread.post_count -= 1
			post.thread.board.post_count -= 1
			thread = post.thread
			last_id = post.id

			if post.thread.last_id == post.id:
				thread_last_reset = True
				
			db.session.delete(post)
			db.session.commit()

			if thread_last_reset:
				old_post = Post.query.filter_by(thread_id=thread.id). \
					order_by(Post.post_time.desc(), Post.id.desc()).first()
				thread.last_post = old_post.post_time
				thread.last = old_post
				
				if thread.board.last_id == last_id:
					thread.board.last_post = old_post
	
				db.session.commit()
				thread_last_reset = False

	db.session.commit()

	if user.banned == True:
		first_name = ''
		last_name = ''
		title = 'New Member'
		unreadpms = 0
		warningpoints = 0
		invisible = False
		lastactive = datetime.utcnow()
		regdate = datetime.utcnow()
		postnum = 0
		threadnum = 0
		signature = ''
		timezone ='UTC'
		deleted = True
		loginattempts = 0
		loginlasttry = datetime.utcnow()
		warning_points = 0
		issixteen = False
		avatarconfirm = False
		loginconfirm = False
		displayconfirm = False
		nameconfirm = False
		titleconfirm = False
		sigconfirm = False
		hideprofile = True
		termsagree = True
		privacyagree = True
		password = "thisisrandomiguess1"
	else:
		db.session.delete(user)
		db.session.commit()

@celery.task
def recount_all_users_posts():
	users = User.query.all()
			
	for user in users:
		user.postnum = 0
		user.threadnum = 0

		for thread in user.user_threads:
			user.threadnum += 1

		for post in user.user_posts:
			user.postnum += 1

	db.session.commit()

@celery.task
def recount_all_boards_posts():
	boards = Board.query.all()
			
	for board in boards:
		board.post_count = 0
		board.threads = 0
		for thread in board.board_threads:
			thread.post_count = 0
			board.threads += 1
			for post in thread.thread_posts:
				board.post_count += 1
				thread.post_count += 1

	db.session.commit()

@celery.task
def reset_user_terms():
	users = User.query.all()

	for user in users:
		user.termsagree = False

	db.session.commit()

@celery.task
def reset_user_privacy():	
	users = User.query.all()

	for user in users:
		user.privacyagree = False
	
	db.session.commit()

@celery.task
def reset_user_warnings():	
	warnings = Warning.query.all()
	
	for warning in warnings:
		if warning.date + timedelta(days= \
			config.get('WARNING_MAX_LIFE_DAYS')) >= datetime.now():
			warning.user.warning_points -= warning.points
			
			if warning.user.banned:
				if warning.user.warning_points < \
					config.get('MAX_WARNINGS'):
					warning.user.banned = False
					
					if warning.user.deleted == True:
						delete_user.delay(warning.user.id)
			
			db.session.delete(warning)
			db.session.commit()

	now = datetime.now()
	reset_user_warnings.apply_async(eta=now + timedelta(days=7))