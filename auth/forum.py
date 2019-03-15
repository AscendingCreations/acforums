#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Author(s):
#  - Andrew Wheeler <lordsatin@hotmail.com>
#
from datetime import datetime, timedelta
from itsdangerous import SignatureExpired
from flask import abort, Blueprint, flash, redirect, render_template, request
from flask import current_app, url_for, session
from flask_login import current_user
from flask_authz import rights
import redis
import pendulum

from .forms import BoardViewForm, BoardMoveForm, ThreadCreateForm, PostsForm
from .forms import PostForm, BoardDeleteForm
from .models import db, authz, Group, User, Email, rdb, UserOnline
from .models import Category, Board, Thread, Post, Log
from .log import create_log

forum_view = Blueprint('forum', __name__)

@forum_view.app_template_global()
def check_right(right):
	for group in current_user.groups:
		if group.permissions.filter_by(token=right).first() is not None:
			return True

	if current_user.permissions.filter_by(token=right).first() is not None:
		return True
	else:
		return False

@forum_view.app_template_global()
def category_viewable(id):
	if check_right('category:view'):
		return True

	return check_right('category:view:{}'.format(id))

@forum_view.app_template_global()
def board_viewable(id):
	if check_right('forum:view'):
		return True

	return check_right('forum:view:{}'.format(id))

@forum_view.app_template_global()
def get_current_user():
	return current_user

@forum_view.route('/', methods=('GET', 'POST'))
@forum_view.route('/forum', methods=('GET', 'POST'))
def view_forum():

	if not current_user.is_anonymous():
		if not current_user.privacyagree:
			flash('You must accept the new Privacy Policy to continue using the Software.', 'error')
			return redirect(url_for('user.user_privacy'))
					
		if  not current_user.termsagree:
			flash('You must accepted the new Terms and Conditions to continue using the Software.', 'error')
			return redirect(url_for('user.user_agreement'))

	categories = Category.query.all()
	can_see_boards = False
	online = []
	cursor_number = 0

	for category in categories:
		if category_viewable(category.id):
			for board in category.category_boards:
				if board_viewable(board.id):
					can_see_boards = True
					break
			if can_see_boards:
				break

	#show only 50 online users as to not burden the page.
	cursor_number, keys = rdb.execute_command('scan', cursor_number, "count", 50)
	
	for key in keys:
		display = rdb.get(key).decode('utf-8')
		user_online = UserOnline (id = key.decode('utf-8'), display=display,)		
		online.append(user_online)
		
	return render_template('forum/forum.htm', categories=categories,
		can_see_boards=can_see_boards, online=online)

@forum_view.route('/forum/board/<int:board_id>', methods=('GET', 'POST'),
	defaults={'page': 1})
@forum_view.route('/forum/board/<int:board_id>/page/<int:page>',
	methods=('GET', 'POST'))
@authz.requires(rights.any_of(
	rights.permission(Group, 'forum:view'),
	rights.permission(Group, 'forum:view:{board_id}')
), methods=('GET', 'POST'))
@authz.requires(rights.any_of(
	rights.permission(Group, 'thread:move'),
	rights.permission(Group, 'thread:remove'),
	rights.permission(Group, 'thread:sticky')
), methods=('POST'))
def view_board(board_id, page):
	board = Board.query.get(board_id) or abort(404)
	viewable = False

	if board.board_threads:
		threads_page = Thread.query.filter_by(board_id=board.id).\
			order_by(Thread.sticky.desc(),Thread.last_post.asc()).paginate(page,
			current_app.config['THREADS_PER_PAGE'], False)
	else:
		thread_page = None

	if not threads_page.items and page != 1:
		abort(404)

	if board.link != '':
		abort(404)

	form = BoardViewForm()
	form.selected.choices = [(thread.id, '') for thread in threads_page.items]

	if form.validate_on_submit():
		if current_user.password != form.password.data:
			flash('Password incorrect', 'error')
			return redirect(url_for('forum.view_board', board_id=board_id, page=page))

		if form.sticky.data:
			threads = Thread.query.filter(Thread.id.in_(form.selected.data)).all()

			for thread in threads:
				thread.sticky = True;

			db.session.commit()
			create_log('Threads Made Sticky', 1)
			flash('Selected Topics marked as sticky', 'success')
			return redirect(url_for('forum.view_board', board_id=board_id, page=page))
		elif form.unsticky.data:
			threads = Thread.query.filter(Thread.id.in_(form.selected.data)).all()

			for thread in threads:
				thread.sticky = False;

			db.session.commit()
			create_log('Threads Made UnSticky', 1)
			flash('Selected Topics no longer sticky', 'success')
			return redirect(url_for('forum.view_board', board_id=board_id, page=page))
		elif form.move.data:
			session['mod_selection'] = form.selected.data
			return redirect(url_for('forum.board_move_threads', board_id=board_id))
		elif form.delete.data:
			session['mod_selection'] = form.selected.data
			return redirect(url_for('forum.board_delete_threads', board_id=board_id))

	for sub_board in board.board_boards:
		if board_viewable(sub_board.id):
			viewable = True
	
	threads = zip(form.selected, threads_page.items) if threads_page.items else None
	return render_template('forum/board.htm', form=form, board=board,
		threads=threads, pages=threads_page, viewable=viewable, user=current_user)

@forum_view.route('/forum/board/<int:board_id>/move',
	methods=('GET', 'POST'))
@authz.requires(rights.any_of(
	rights.permission(Group, 'forum:mod'),
	rights.permission(Group, 'forum:mod:{board_id}')
), methods=('GET', 'POST'))
@authz.requires(rights.all_of(
	rights.permission(Group, 'thread:view'),
	rights.permission(Group, 'thread:move')
), methods=('GET', 'POST'))
@authz.requires(rights.permission(Group, 'thread:move'), methods=('POST'))
def board_move_threads(board_id):
	form = BoardMoveForm()
	boards = Board.query.all()
	cur_board = Board.query.get(board_id) or abort(404)
	board_last_reset = False

	form.boards.choices = [(board.id, board.title) for board in boards]

	selected = session.get('mod_selection', [])

	if not selected:
		flash('nothing was selected', 'error')
		return redirect(url_for('forum.view_board', board_id=form.boards.data))

	if form.validate_on_submit():
		if current_user.password == form.password.data:
			threads = Thread.query.filter(Thread.id.in_(selected)).all()

			for thread in threads:
				new_parent = Board.query.filter_by(id=form.boards.data).first()
				
				if new_parent.link:
					flash('Can not move to a linked board', 'error')
					return redirect(url_for('forum.view_board', board_id=board_id))

				if cur_board.last_post.id == thread.last.id:
					board_last_reset = True

				if new_parent.last_post.post_time < thread.last.post_time:
					new_parent.last_post = thread.last

				cur_board.post_count -= thread.post_count
				cur_board.threads -= 1
				cur_board.board_threads.remove(thread)
				new_parent.board_threads.append(thread)
				new_parent.post_count += thread.post_count
				new_parent.threads += 1

			db.session.commit()
			
			if board_last_reset:
				thread = Thread.query.filter_by(board_id=cur_board.id). \
					order_by(Thread.last_post.asc()).first()
				
				if not thread:
					cur_board.last_post = None
				else:
					cur_board.last_post = thread.last

				db.session.commit()

			create_log('Threads were moved to board {}'.format(new_parent.id), 1)
			return redirect(url_for('forum.view_board', board_id=form.boards.data))
		else:
			flash('Password incorrect', 'error')
	return render_template('forum/move_threads.htm', form=form, board=cur_board)

@forum_view.route('/forum/board/<int:board_id>/delete',
	methods=('GET', 'POST'))
@authz.requires(rights.any_of(
	rights.permission(Group, 'forum:mod'),
	rights.permission(Group, 'forum:mod:{board_id}')
), methods=('GET', 'POST'))
@authz.requires(rights.all_of(
	rights.permission(Group, 'thread:view'),
	rights.permission(Group, 'thread:remove')
), methods=('GET', 'POST'))
@authz.requires(rights.permission(Group, 'thread:remove'), methods=('POST'))
def board_delete_threads(board_id):
	form = BoardDeleteForm()
	board = Board.query.get(board_id) or abort(404)
	board_last_reset = False

	selected = session.get('mod_selection', [])

	if not selected:
		flash('nothing was selected', 'error')
		return redirect(url_for('forum.view_board', board_id=form.boards.data))

	if form.validate_on_submit():
		if current_user.password == form.password.data:
			threads = Thread.query.filter(Thread.id.in_(selected)).all()
			
			for thread in threads:
				if thread.board_id != board.id:
					abort(404)
				
				if board.last_post.id == thread.last.id:
					board_last_reset = True
					board.last_post = None

				board.post_count -= thread.post_count
				board.threads -= 1
				thread.creator.threadnum -=1
				for post in thread.thread_posts:
					post.creator.postnum -=1

				db.session.delete(thread)
			db.session.commit()
			
			if board_last_reset:
				thread = Thread.query.filter_by(board_id=board.id). \
					order_by(Thread.last_post.desc(), Thread.id.desc()).first()
					
				if thread:
					board.last_post = thread.last

				db.session.commit()

			create_log('Threads Deleted', 1)
			return redirect(url_for('forum.view_board', board_id=board_id))
		else:
			flash('Password incorrect', 'error')
	return render_template('forum/delete_threads.htm', form=form, board=board)

#TODO Add a thread edit page to edit thread if editing the main thread post.
@forum_view.route('/forum/board/<int:board_id>/create_thread',
	methods=('GET', 'POST'))
@authz.requires(rights.any_of(
	rights.permission(Group, 'forum:view'),
	rights.permission(Group, 'forum:view:{board_id}')
), methods=('GET', 'POST'))
@authz.requires(rights.all_of(
	rights.any_of(
		rights.permission(Group, 'forum:post'),
		rights.permission(Group, 'forum:post:{board_id}')),
	rights.permission(Group, 'thread:view')
), methods=('GET', 'POST'))
@authz.requires(rights.permission(Group, 'thread:create'), methods=('POST'))
def board_create_threads(board_id):
	form = ThreadCreateForm()
	board = Board.query.get(board_id) or abort(404)

	if form.validate_on_submit():
		if current_user.password == form.password.data:

			thread = Thread (
				title=form.title.data,
				sticky=form.sticky.data,
				post_count=1,
			)

			db.session.add(thread)
			post = Post (
				message = form.text.data.replace('http:', 'https:'),
				thread_post = True,
				post_time = datetime.utcnow(),
			)
			db.session.add(post)
			
			current_user.user_posts.append(post)
			current_user.user_threads.append(thread)
			thread.thread_posts.append(post)
			board.board_threads.append(thread)
			thread.last_post = post.post_time
			thread.last = post
			thread.board.last_post = post
			current_user.postnum += 1
			current_user.threadnum += 1
			board.threads += 1
			board.post_count += 1
			db.session.commit()

			return redirect(url_for('forum.board_view_posts',
				board_id=board_id, thread_id=thread.id))
		else:
			flash('Password incorrect', 'error')

	return render_template('forum/create_thread.htm', form=form, board=board)

	#TODO : finish post view, post reply, post edit and post create
@forum_view.route('/forum/board/<int:board_id>/thread/<int:thread_id>',
	methods=('GET', 'POST'), defaults={'page': 1})
@forum_view.route('/forum/board/<int:board_id>/thread/<int:thread_id>/page/ \
<int:page>', methods=('GET', 'POST'))
@authz.requires(rights.all_of(
	rights.any_of(
		rights.permission(Group, 'forum:view'),
		rights.permission(Group, 'forum:view:{board_id}')),
	rights.permission(Group, 'thread:view')
), methods=('GET', 'POST'))
@authz.requires(rights.all_of(
	rights.any_of(
		rights.permission(Group, 'forum:mod'),
		rights.permission(Group, 'forum:mod:{board_id}')),
	rights.permission(Group, 'thread:remove')
), methods=('POST'))
def board_view_posts(board_id, thread_id, page):
	form = ThreadCreateForm()
	thread = Thread.query.get(thread_id) or abort(404)
	post_page = Post.query.filter_by(thread_id=thread_id). \
		order_by(Post.thread_post.desc(),Post.post_time.asc()).paginate(page,
			current_app.config['POSTS_PER_PAGE'], False)

	if not post_page.items and page != 1:
		abort(404)

	form = PostsForm()
	form.selected.choices = [(post.id, '') for post in post_page.items]

	if form.validate_on_submit():
		if current_user.password != form.password.data:
			flash('Password incorrect', 'error')
			return redirect(url_for('forum.board_view_posts',
				board_id=board_id, thread_id=thread_id, page=page))

		if form.selected.data:
			posts = Post.query.filter(Post.id.in_(form.selected.data)).all()
			change_time = False
			last_id = 0

			for post in posts:
				if post.thread_post:
					flash('You cannot delete the threads main post.', 'error')
					return redirect(url_for('forum.board_view_posts',
						board_id=board_id, thread_id=thread_id, page=page))
				if post.thread_id != thread_id:
					abort(404)

				thread.board.post_count -= 1
				thread.post_count -= 1
				post.creator.postnum -=1

				if thread.last_post == post.post_time:
					change_time = True
					last_id = post.id

				db.session.delete(post)

			if change_time:
				old_post = Post.query.filter_by(thread_id=thread.id). \
					order_by(Post.post_time.desc(), Post.id.desc()).first()
				thread.last_post = old_post.post_time
				thread.last = old_post
				
				if thread.board.last_id == last_id:
					thread.board.last_post = old_post

			db.session.commit()
			create_log('Posts were removed', 1)
			flash('Posts were removed', 'success')
		return redirect(url_for('forum.board_view_posts',
				board_id=board_id, thread_id=thread_id))

	posts = zip(form.selected, post_page.items) if post_page.items else None
	return render_template('forum/thread.htm', form=form, board_id=board_id,
		thread=thread, pages=post_page, posts=posts, user=current_user)

@forum_view.route('/forum/board/<int:board_id>/thread/<int:thread_id>/\
create_post', methods=('GET', 'POST'))
@authz.requires(rights.any_of(
	rights.permission(Group, 'forum:view'),
	rights.permission(Group, 'forum:view:{board_id}')
), methods=('GET', 'POST'))
@authz.requires(rights.all_of(
	rights.any_of(
		rights.permission(Group, 'forum:post'),
		rights.permission(Group, 'forum:post:{board_id}')),
	rights.permission(Group, 'thread:view')
), methods=('GET', 'POST'))
@authz.requires(rights.permission(Group, 'thread:create'), methods=('POST'))
def board_create_post(board_id, thread_id):
	form = PostForm()
	thread = Thread.query.get(thread_id) or abort(404)

	if form.validate_on_submit():
		if current_user.password == form.password.data:

			post = Post (
				message = form.text.data.replace('http:', 'https:'),
				thread_post = False,
				post_time = datetime.utcnow(),
			)

			db.session.add(post)

			current_user.user_posts.append(post)
			thread.thread_posts.append(post)
			current_user.postnum += 1
			thread.post_count += 1
			thread.board.post_count += 1
			thread.last_post = post.post_time
			thread.last = post
			thread.board.last_post = post
			db.session.commit()

			return redirect(url_for('forum.board_view_posts',
							board_id=board_id, thread_id=thread_id))
		else:
			flash('Password incorrect', 'error')

	return render_template('forum/create_post.htm', form=form, thread=thread)

@forum_view.route('/forum/board/<int:board_id>/thread/<int:thread_id>/\
edit_post/<int:post_id>', methods=('GET', 'POST'))
@authz.requires(rights.any_of(
	rights.permission(Group, 'forum:view'),
	rights.permission(Group, 'forum:view:{board_id}')
), methods=('GET', 'POST'))
@authz.requires(rights.all_of(
		rights.permission(Group, 'forum:edit'),
		rights.permission(Group, 'thread:view')
), methods=('GET', 'POST'))
@authz.requires(rights.permission(Group, 'thread:edit'), methods=('POST'))
def board_edit_post(board_id, thread_id, post_id):
	form = PostForm()
	post = Post.query.get(post_id) or abort(404)
	thread = Thread.query.get(thread_id) or abort(404)

	if not check_right('forum:mod') and \
		not check_right('forum:mod:{}'.format(board_id)):
		if post.creator.id != current_user.id:
			abort(404)

	if form.validate_on_submit():
		if current_user.password == form.password.data:

			post.message = form.text.data
			post.edit_time = datetime.utcnow()
			
			if post.editor:
				post.editor.edited_posts.remove(post)

			current_user.edited_posts.append(post)
			db.session.commit()
			create_log('Post:{} was Edited'.format(post_id), 2)
			return redirect(url_for('forum.board_view_posts',
							board_id=board_id, thread_id=thread_id))
		else:
			flash('Password incorrect', 'error')

	if not form.text.data:
		form.text.data = post.message

	return render_template('forum/edit_post.htm', thread=thread, form=form, post=post)
	
@forum_view.route('/forum/board/<int:board_id>/thread/<int:thread_id>/\
reply_post/<int:post_id>', methods=('GET', 'POST'))
@authz.requires(rights.any_of(
	rights.permission(Group, 'forum:view'),
	rights.permission(Group, 'forum:view:{board_id}')
), methods=('GET', 'POST'))
@authz.requires(rights.all_of(
		rights.any_of(
		rights.permission(Group, 'forum:reply'),
		rights.permission(Group, 'forum:reply:{board_id}')),
		rights.permission(Group, 'thread:view')
), methods=('GET', 'POST'))
@authz.requires(rights.permission(Group, 'thread:reply'), methods=('POST'))
def board_reply_post(board_id, thread_id, post_id):
	form = PostForm()
	post = Post.query.get(post_id) or abort(404)
	thread = Thread.query.get(thread_id) or abort(404)

	if form.validate_on_submit():
		if current_user.password == form.password.data:
			post = Post (
				message = form.text.data.replace('http:', 'https:'),
				thread_post = False,
				post_time = datetime.utcnow(),
			)

			db.session.add(post)

			current_user.user_posts.append(post)
			thread.thread_posts.append(post)
			current_user.postnum += 1
			thread.post_count += 1
			thread.board.post_count += 1
			thread.last_post = post.post_time
			thread.last = post
			thread.board.last_post = post
			db.session.commit()

			return redirect(url_for('forum.board_view_posts',
							board_id=board_id, thread_id=thread_id))
		else:
			flash('Password incorrect', 'error')

	form.text.data = "Quote by {0}:<div style=\"background:#eeeeee;	border:1px \
		solid #cccccc; padding:5px 10px\">{1}</div>".format(post.creator.display,
		post.message)
	return render_template('forum/create_post.htm', thread=thread, form=form)