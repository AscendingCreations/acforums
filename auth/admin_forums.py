#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Author(s):
#  - Andrew Wheeler <lordsatin@hotmail.com>
#
from datetime import datetime, timedelta
from flask import abort, Blueprint, flash, redirect, render_template, request
from flask import current_app, url_for
from flask_login import current_user
from flask_authz import rights
import pendulum

from .models import db, authz, Group, User, GroupPermission
from .models import Category, Board, Thread, Post, Log
from .forms import CategoryCreateForm, BoardCreateForm, BoardEditForm
from .forms import CategoryEditForm, DeleteForumForm
from .log import create_log

admin_forum_view = Blueprint('admin_forum', __name__)

def groups_set_perm(new_right, data):
	for id in data:
		group = Group.query.filter_by(id=id).first()

		if group:
			new_right = new_right.lower()
			if group.permissions.filter_by(token=new_right).first() is None:
				right = GroupPermission(token=new_right)
				db.session.add(right)
				group.permissions.append(right)
			
@admin_forum_view.route('/admin/forums', methods=('GET', 'POST'))
@authz.requires(rights.permission(Group, 'admin:view'), methods=('GET', 'POST'))
def admin_view_forum():
	cats = Category.query.order_by(Category.order.asc()).all()
	return render_template('admin/forum.htm', cats=cats)

@admin_forum_view.route('/admin/category_del/<int:id>', methods=('GET', 'POST'))
@authz.requires(rights.permission(Group, 'admin:view'), methods=('GET', 'POST'))
@authz.requires(rights.permission(Group, 'forum:delete'), methods=('POST'))
def admin_del_category(id):
	form = DeleteForumForm()
	category = Category.query.filter_by(id=id).first()

	if not category:
		abort(404)

	if form.validate_on_submit():
		if current_user.password == form.password.data:
			db.session.delete(category)
			db.session.commit()
			create_log('Category: {} Deleted'.format(id), 1)
			flash('Category Deleted Successfully', 'success')
			return redirect(url_for('admin_forum.admin_view_forum'))
		else:
			flash('Password Incorrect', 'error')

	return render_template('admin/forum_delete.htm', form=form, title=category.title)

@admin_forum_view.route('/admin/board_del/<int:id>', methods=('GET', 'POST'))
@authz.requires(rights.permission(Group, 'admin:view'), methods=('GET', 'POST'))
@authz.requires(rights.permission(Group, 'forum:delete'), methods=('POST'))
def admin_del_board(id):
	form = DeleteForumForm()
	board = Board.query.filter_by(id=id).first()

	if not board:
		abort(404)

	if form.validate_on_submit():
		if current_user.password == form.password.data:
			Board.query.filter_by(id=id).delete()
			db.session.commit()
			create_log('Board: {} Deleted'.format(id), 1)
			flash('Board Deleted Successfully', 'success')
			return redirect(url_for('admin_forum.admin_view_forum'))
		else:
			flash('Password Incorrect', 'error')

	return render_template('admin/forum_delete.htm', form=form, title=board.title)

@admin_forum_view.route('/admin/category_create', methods=('GET', 'POST'))
@authz.requires(rights.permission(Group, 'admin:view'), methods=('GET', 'POST'))
@authz.requires(rights.permission(Group, 'forum:create'), methods=('POST'))
def admin_create_category():
	form = CategoryCreateForm()
	groups = Group.query.all()
	form.view.choices = [(group.id, '') for group in groups]
	
	if form.validate_on_submit():
		if current_user.password == form.password.data:
			category = Category (
							title = form.title.data,
							order = form.order.data,
						)

			if Category.query.filter_by(title=category.title.lower()).first() is not None:
				flash('Title can not be used, please choose Another', 'error')
				return redirect(url_for('admin_forum.admin_create_category'))
			
			db.session.add(category)

			for choice in form.view.data:
				group = Group.query.filter_by(id=choice).first()
				permission = GroupPermission(token='category:view:{}'.format(category.id))
				db.session.add(permission)
				group.permissions.append(permission)

			db.session.commit()
			create_log('Category {} Created'.format(category.title), 1)
			flash('Category Added Successfully', 'success')
			return redirect(url_for('admin_forum.admin_view_forum'))
		else:
			flash('Password Incorrect', 'error')

	groups = zip(form.view, groups) if groups else None

	return render_template('admin/category_create.htm', form=form, groups=groups)

@admin_forum_view.route('/admin/category_edit/<int:id>', methods=('GET', 'POST'))
@authz.requires(rights.permission(Group, 'admin:view'), methods=('GET', 'POST'))
@authz.requires(rights.permission(Group, 'forum:edit'), methods=('POST'))
def admin_edit_category(id):
	category = Category.query.filter_by(id=id).first()
	
	if not category:
		abort(404)

	form = CategoryEditForm()
	groups = Group.query.all()

	if form.validate_on_submit():
		if current_user.password == form.password.data:
			category.title = form.title.data
			category.order = form.order.data

			if Category.query.filter_by(title=category.title.lower()).first():
				flash('Title can not be used, please choose Another', 'error')
				return redirect(url_for('admin_forum.admin_edit_category', id=id))
				
			db.session.commit()
			create_log('Category {} Edited'.format(id), 1)
			flash('Category Updated Successfully', 'success')
			return redirect(url_for('admin_forum.admin_view_forum'))
		else:
			flash('Password Incorrect', 'error')

	form.title.data = category.title
	form.order.data = category.order

	return render_template('admin/category_edit.htm', form=form, category=category)
	
@admin_forum_view.route('/admin/board_create', methods=('GET', 'POST'))
@authz.requires(rights.permission(Group, 'admin:view'), methods=('GET', 'POST'))
@authz.requires(rights.permission(Group, 'forum:create'), methods=('POST'))
def admin_create_board():
	form = BoardCreateForm()
	groups = Group.query.all()
	boards = Board.query.all()
	cats = Category.query.all()
	mustselect = False

	form.category.choices.clear()
	form.parent.choices.clear()

	form.view.choices = [(group.id, '') for group in groups]
	form.post.choices = [(group.id, '') for group in groups]
	form.reply.choices = [(group.id, '') for group in groups]
	form.poll.choices = [(group.id, '') for group in groups]
	
	form.category.choices.append((0, 'None'))
	form.parent.choices.append((0, 'None'))

	for category in cats:
		form.category.choices.append((category.id, category.title))

	for board in boards:
		if not board.parent:
			form.parent.choices.append((board.id, board.title))

	if form.validate_on_submit():
		if current_user.password == form.password.data:
			board = Board (
				title = form.title.data,
				order = form.order.data,
				link = form.link.data
			)

			if Board.query.filter_by(title=board.title.lower()).first() is None:
				db.session.add(board)

				if form.parent.data != 0:
					parent_board = Board.query.\
						filter_by(id=form.parent.data).first()
					parent_category = Category.query.\
						filter_by(id=parent_board.category_id).first()
					parent_board.board_boards.append(board)
					parent_category.category_boards.append(board)
				elif form.category.data != 0:
					category = Category.query.\
						filter_by(id=form.category.data).first()
					category.category_boards.append(board)

				groups_set_perm('forum:view:{}'.format(board.id),
					form.view.data)
				groups_set_perm('forum:post:{}'.format(board.id),
					form.post.data)
				groups_set_perm('forum:reply:{}'.format(board.id),
					form.reply.data)
				groups_set_perm('forum:poll:{}'.format(board.id),
					form.poll.data)

				db.session.commit()
				create_log('Created Board {}'.format(board.title), 1)
				flash('Board Added Successfully', 'success')
				return redirect(url_for('admin_forum.admin_view_forum'))

				flash('You must select a category or a Parent', 'error')
			else:
				flash('Title can not be used, please choose Another', 'error')
		else:
			flash('Password Incorrect', 'error')

	groups = zip(form.view, form.post, form.reply, form.poll,
		groups) if groups else None

	return render_template('admin/board_create.htm', form=form, groups=groups)

	
@admin_forum_view.route('/admin/board_edit/<int:id>', methods=('GET', 'POST'))
@authz.requires(rights.permission(Group, 'admin:view'), methods=('GET', 'POST'))
@authz.requires(rights.permission(Group, 'forum:edit'), methods=('POST'))
def admin_edit_board(id):
	cur_board = Board.query.filter_by(id=id).first()
	
	if not cur_board:
		abort(404)

	form = BoardEditForm()
	boards = Board.query.all()
	cats = Category.query.all()

	if form.validate_on_submit():
		if current_user.password == form.password.data:
			if cur_board.title != form.title.data.lower():
				if Board.query.filter_by(title=form.title.data.lower()).first():
					flash('Title can not be used, please choose Another', 'error')
					return redirect(url_for('admin_forum.admin_edit_board', id=id))

			cur_board.title = form.title.data
			cur_board.order = form.order.data
			cur_board.link = form.link.data

			if form.parent.data != 0:
				if cur_board.board_boards:
					if len(cur_board.board_boards):
						flash('You must remove all sub boards to make this a sub board', 'error')
						return redirect(url_for('admin_forum.admin_edit_board', id=id))
				
				if cur_board.parent is not None:
					old_parent = Board.query.filter_by(id=cur_board.parent_id).first()
					old_category = Category.query.filter_by(id=cur_board.category_id).first()
					old_parent.board_boards.remove(cur_board)
					old_category.category_boards.remove(cur_board)
					print("removed old parent and category")

				new_parent = Board.query.filter_by(id=form.parent.data).first()
				new_category = Category.query.filter_by(id=new_parent.category_id).first()
				new_parent.board_boards.append(cur_board)
				new_category.category_boards.append(cur_board)

			elif form.category.data != 0:
				if cur_board.parent:
					parent = cur_board.parent
					parent.board_boards.remove(cur_board)
					cur_board.parent_id = None

				category = Category.query.filter_by(id=form.category.data).first()
				old_category = Category.query.filter_by(id=cur_board.category_id).first()
				old_category.category_boards.remove(cur_board)
				category.category_boards.append(cur_board)
			else:
				flash('You must select a category or a Parent to create a board', 'error')
				return redirect(url_for('admin_forum.admin_edit_board', id=id))

			db.session.commit()
			create_log('board: {} Updated'.format(id), 1)
			flash('Board Updated Successfully', 'success')
			return redirect(url_for('admin_forum.admin_view_forum'))
		else:
			flash('Password Incorrect', 'error')

	form.category.choices.clear()
	form.parent.choices.clear()
	form.category.choices.append((0, 'None'))
	form.parent.choices.append((0, 'None'))
	
	for category in cats:
		form.category.choices.append((category.id, category.title))

	for board in boards:
		if not board.parent:
			form.parent.choices.append((board.id, board.title))

	form.parent.data = cur_board.parent_id
	form.category.data = cur_board.category_id
	form.title.data = cur_board.title
	form.order.data = cur_board.order
	form.link.data = cur_board.link

	return render_template('admin/board_edit.htm', form=form)
	