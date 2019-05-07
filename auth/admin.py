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
import json

from .models import db, authz, Group, User, Email, UserPermission
from .models import Log, GroupPermission, Thread, Post, Warning, Board
from .forms import AdminUserForm, AdminUserListForm, AdminCreateUserForm 
from .forms import UserGroupForm, UserPermForm, GroupListForm, GroupEditForm
from .forms import GroupCreateForm, InfoForm
from .utils import mail, parse_token, sign_token
from .log import create_log
from sqlalchemy import func
from .services import YamlCompiler, ScssCompiler
from .tasks import send_async_email, delete_user, recount_all_boards_posts
from .tasks import recount_all_users_posts, reset_user_terms, reset_user_privacy

admin_view = Blueprint('admin', __name__)

@admin_view.route('/admin/info', methods=('GET', 'POST'))
@authz.requires(rights.permission(Group, 'admin:view'), methods=('GET', 'POST'))
def info():
	form = InfoForm()
	users = db.session.query(func.count(User.id)).scalar()
	posts = db.session.query(func.count(Post.id)).scalar() 
	threads = db.session.query(func.count(Thread.id)).scalar()
	warnings = db.session.query(func.count(Warning.id)).scalar()
	logs = db.session.query(func.count(Log.id)).scalar()
	newest = User.query.order_by(User.id.desc()).first()
	
	if form.validate_on_submit():
		if form.recountboard.data:
			recount_all_boards_posts.delay()
			flash('Board Topics and posts are scheduled for recount.', 'success')
		if form.recountuser.data:
			recount_all_users_posts.delay()
			flash('Topics and posts are scheduled for recount.', 'success')
		if form.resetterms.data:
			reset_user_terms.delay()
			flash('User Term agreements scheduled for reset.', 'success')
		if form.resetprivacy.data:
			reset_user_privacy.delay()
			flash('User Privacy agreements scheduled for reset.', 'success')
	
	return render_template('admin/info.htm', form=form, users=users, posts=posts,
		threads=threads, warnings=warnings, logs=logs, newest=newest)

@admin_view.route('/admin/theme', methods=('GET', 'POST', 'PUT'))
@authz.requires(rights.permission(Group, 'admin:view'), methods=('GET' 'POST'))
@authz.requires(rights.permission(Group, 'forum:edit'), methods=('GET', 'POST', 'PUT'))
def admin_theme():
	if request.method == 'PUT':
		theme_path = 'auth/theme/theme.yaml'
		data = json.loads(request.data.decode('utf-8'))
		YamlCompiler.write_file(theme_path, 'w', data)
		compiler = ScssCompiler(theme_path)
		sass = compiler.compile('auth/static/uikit/scss/index.scss')
		compiler.write_file(sass, 'auth/static/css/uikit.css')
		return "success"
	else:
		sass_variables = YamlCompiler.read_file('auth/theme/theme.yaml')
		return render_template('admin/theme.html', sass_variables=sass_variables)

@admin_view.route('/admin/user_edit/<int:user_id>', methods=('GET', 'POST'))
@authz.requires(rights.all_of(
		rights.permission(Group, 'admin:userview'),
		rights.permission(Group, 'user:edit'),
), methods=('GET', 'POST'))
def user_edit(user_id):
	user = User.query.get(user_id) or abort(404)
	form = AdminUserForm(obj=user)

	if user.username == current_app.config['OWNER']:
		if current_user.username != current_app.config['OWNER']:
			abort(404) ##Prevent Owner from being edited by others.

	if request.method == 'POST':
		if form.validate_on_submit():
		
			if current_user.password != form.password.data:
				flash('The user credentials specified are invalid.', 'error')
				return render_template('admin/user_edit.htm',
					form=form, user=user)

			if user.username != form.username.data:
				if User.query.filter(User.username==form.username. \
					data.lower()).first() is None:
					user.username = form.username.data
			
			user.display = form.display.data
			user.first_name = form.first_name.data
			user.last_name = form.last_name.data
			user.title = form.title.data
			user.signature = form.signature.data
			user.timezone = form.timezone.data
			
			if user.email != form.email.data:
				if User.query.join(User.emails). \
			filter(Email.email==form.email.data.lower()).first() is None:
					user.email = form.email.data

			user.banned = form.banned.data
			user.activated = form.activated.data
			
			if form.new_password.data:
				user.password = form.new_password.data

			db.session.commit()
			create_log('User: {} Edited'.format(user_id), 1)
			flash('Your Changes have been made successfully.', 'success')
		else:
			flash("""Your Changes have not been made. You will need to fill out
				everything that is required to submit the changes""", 'error')

	return render_template('admin/user_edit.htm', form=form, user=user)

@admin_view.route('/admin/users', methods=('GET', 'POST'), defaults={'page': 1})
@admin_view.route('/admin/users/page/<int:page>', methods=('GET', 'POST'))
@authz.requires(rights.all_of(
		rights.permission(Group, 'admin:userview'),
		rights.permission(Group, 'user:edit'),
), methods=('GET', 'POST'))
@authz.requires(rights.permission(Group, 'user:delete'), methods=('POST'))
def admin_view_users(page):
	users_page = User.query.paginate(page,
		current_app.config['USERS_PER_PAGE'], False)
	
	form = AdminUserListForm()
	form.selected.choices = [(user.id, '') for user in users_page.items]

	if not users_page.items and page != 1:
		abort(404)
	
	if form.validate_on_submit():
		if current_user.password == form.password.data:
			users = User.query.filter(User.id.in_(form.selected.data)).all()
			
			for user in users:
				delete_user.delay(user.id)

			create_log('Users Deleted', 1)
			return redirect(url_for('admin.admin_view_users'))
		else:
			flash('Password Incorrect', 'error')

	users = zip(form.selected, users_page.items) if users_page.items else None

	return render_template('admin/users.htm', form=form, users=users,
		pages=users_page)

@admin_view.route('/admin/create_user', methods=('GET', 'POST'))
@authz.requires(rights.any_of(
		rights.permission(Group, 'user:create'),
		rights.permission(Group, 'admin:userview')
), methods=('GET', 'POST'))
def create_user():
	form = AdminCreateUserForm()

	if form.validate_on_submit():
		user = User(
				username=form.username.data.lower(),
				display=form.display.data,
				first_name=form.first_name.data,
				last_name=form.last_name.data,
				password=form.new_password.data,
				title=form.title.data,
				activated = True,
			)

		if User.query.filter_by(username=user.username.lower()).first():
			flash('Username can not be used, please choose Another', 'error')
			return render_template('admin/user_create.htm', form=form)

		if User.query.filter_by(display=user.display.lower()).first():
			flash('Display can not be used, please choose Another', 'error')
			return render_template('admin/user_create.htm', form=form)
			
		if Email.query.filter_by(email=form.email.data.lower()).first():
			flash('Email can not be used, please choose Another', 'error')
			return render_template('admin/user_create.htm', form=form)

		db.session.add(user)
		name = 'users'
		groups = Group.query.filter_by(name=name.lower()).first()

		if groups is None:
			print("group called Users not found")
			abort(404)

		user.groups.append(groups)
		user.email = Email(email=form.email.data)
		db.session.add(user.email)
		user.emails.append(user.email)
		flash('User Created Successfully', 'success')
		db.session.commit()
		create_log('User {} Create'.format(user.id), 1)
		return redirect(url_for('admin.user_edit', user_id=user.id))

	return render_template('admin/user_create.htm', form=form)
	
@admin_view.route('/admin/user_groups/<int:user_id>', methods=('GET', 'POST'))
@authz.requires(rights.any_of(
		rights.permission(Group, 'user:permissions'),
		rights.permission(Group, 'admin:userview')
), methods=('GET', 'POST'))
def admin_user_group(user_id):
	user = User.query.get(user_id) or abort(404)
	form = UserGroupForm()
	
	groups = Group.query.all()
	form.selected.choices = [(group.name, group.name) for group in groups]

	if form.validate_on_submit():
		if form.password.data != current_user.password:
			flash('Password incorrect', 'error')
			return redirect(url_for('admin.admin_user_group', user_id=user.id))

		group = Group.query.filter_by(name=form.selected.data.lower()).first()
		
		if group is None:
			flash('Group does not exist', 'error')
			return redirect(url_for('admin.admin_user_group', user_id=user.id))

		if form.add.data:
			user.groups.append(group)
			flash('User Group Added Successfully', 'success')
			create_log('User: {} was given group: {}'.format(user.id, group.name), 1)
		elif form.remove.data:
			user.groups.remove(group)
			flash('User Group Removed Successfully', 'success')

		db.session.commit()

		return redirect(url_for('admin.admin_user_group', user_id=user.id))

	return render_template('admin/users_groups.htm', form=form, user=user)
	
@admin_view.route('/admin/user_perms/<int:user_id>', methods=('GET', 'POST'))
@authz.requires(rights.any_of(
		rights.permission(Group, 'user:permissions'),
		rights.permission(Group, 'admin:userview')
), methods=('GET', 'POST'))
def admin_user_perms(user_id):
	user_rights = []
	group_rights = []
	user = User.query.get(user_id) or abort(404)
	form = UserPermForm()
	
	for group in user.groups:
		for right in group.permissions:
			group_rights.append('{0} [inherited from {1}]'.format(right.token,
				group.name))

	for right in user.permissions:
		user_rights.append(right.token)

	if form.validate_on_submit():
		if form.password.data != current_user.password:
			flash('Password incorrect', 'error')
			return redirect(url_for('admin.admin_user_perms', user_id=user.id))

		rights = form.perms.data.strip().split(',')
		
		if form.add.data:
			for right in rights:
				if user.permissions.filter_by(token=right.lower()).first() is None:
					right = UserPermission(token=right.lower())
					db.session.add(right)
					user.permissions.append(right)
			flash('User Rights Added Successfully', 'success')
		elif form.remove.data:
			for right in rights:
				user.permissions.filter_by(token=right.lower()).delete()
			flash('User rights Removed Successfully', 'success')

		db.session.commit()
		create_log('User {} got given permissions'.format(user.id), 1)
		return redirect(url_for('admin.admin_user_perms', user_id=user.id))

	return render_template('admin/user_permissions.htm', form=form, user=user,
		group_rights=group_rights, rights=user_rights)

@admin_view.route('/admin/group_edit/<int:group_id>', methods=('GET', 'POST'))
@authz.requires(rights.all_of(
		rights.permission(Group, 'group:view'),
		rights.permission(Group, 'group:edit'),
), methods=('GET', 'POST'))
def group_edit(group_id):
	group_rights = []
	group = Group.query.get(group_id) or abort(404)
	form = GroupEditForm(obj=group)

	for right in group.permissions:
		group_rights.append(right.token)

	if request.method == 'POST':
		if form.validate_on_submit():
		
			if current_user.password != form.password.data:
				flash('Password is invalid.', 'error')
				return render_template('admin/group_edit.htm',
					form=form, group=group)

			if group.name != form.name.data:
				if Group.query.filter(Group.name==form.name. \
					data.lower()).first() is None:
					group.name = form.name.data
			
			if group.display != form.display.data:
				if Group.query.filter(Group.display==form.display. \
					data.lower()).first() is None:
					group.display = form.display.data
					
			rights = form.perms.data.strip().split(',')
		
			if form.add.data:
				for right in rights:
					if group.permissions.filter_by(token=right.lower()). \
						first() == None:
						right = GroupPermission(token=right.lower())
						db.session.add(right)
						group.permissions.append(right)
			elif form.remove.data:
				for right in rights:
					group.permissions.filter_by(token=right.lower()).delete()

			db.session.commit()
			create_log('Group: {} given or removed permissions'.format(group.id), 1)
			flash('Your Changes have been made successfully.', 'success')
		else:
			flash("""Your Changes have not been made. You will need to fill out
				everything that is required to submit the changes""", 'error')

	return render_template('admin/group_edit.htm', form=form, group=group,
		rights=group_rights)

@admin_view.route('/admin/groups', methods=('GET', 'POST'), defaults={'page': 1})
@admin_view.route('/admin/groups/page/<int:page>', methods=('GET', 'POST'))
@authz.requires(rights.permission(Group, 'group:view'), methods=('GET', 'POST'))
@authz.requires(rights.permission(Group, 'group:delete'), methods=('POST'))
def admin_view_groups(page):
	groups_page = Group.query.paginate(page,
		current_app.config['GROUPS_PER_PAGE'], False)
	form = GroupListForm()
	form.selected.choices = [(group.id, '') for group in groups_page.items]

	if not groups_page.items and page != 1:
		abort(404)

	if form.validate_on_submit():
		if current_user.password == form.password.data:
			stmt = GroupPermission.__table__.delete(). \
				where(GroupPermission.group_id.in_(form.selected.data))
			db.engine.execute(stmt)
			stmt = Group.__table__.delete().where(Group.id.in_(form.selected.data))
			db.engine.execute(stmt)
			create_log('Groups Deleted', 1)
			return redirect(url_for('admin.admin_view_groups'))
		else:
			flash('Password Incorrect', 'error')

	groups = zip(form.selected, groups_page.items) if groups_page.items else None

	return render_template('admin/groups.htm', form=form, groups=groups,
		pages=groups_page)

@admin_view.route('/admin/create_group', methods=('GET', 'POST'))
@authz.requires(rights.any_of(
		rights.permission(Group, 'group:create'),
		rights.permission(Group, 'group:view')
), methods=('GET', 'POST'))
def create_group():
	form = GroupCreateForm()
	groups = Group.query.all()
	form.selected.choices = [(group.name, group.name) for group in groups]

	if form.validate_on_submit():
		group = Group(
			name=form.name.data.lower(),
			display=form.display.data.lower(),
			)

		db.session.add(group)
		
		oldgroup = Group.query.filter_by(name=form.selected.data.lower()).first()
		
		if oldgroup:
			for per in oldgroup.permissions:
				right = GroupPermission(token=per.token)
				db.session.add(right)
				group.permissions.append(right)
			
		flash('Group Created Successfully', 'success')
		db.session.commit()
		create_log('Group: {} Created'.format(group.id), 1)
		return redirect(url_for('admin.group_edit', group_id=group.id))

	return render_template('admin/group_create.htm', form=form)	