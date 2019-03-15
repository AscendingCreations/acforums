#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Author(s):
#  - Andrew Wheeler <lordsatin@hotmail.com>
#  - S.J.R. van Schaik <stephan@synkhronix.com>
from getpass import getpass
from datetime import datetime
import sys

from ..models import db, User, Group, GroupPermission, Email, UserPermission
from ..models import Post, Thread
from .user import user

def readline(prompt):
	sys.stdout.write(prompt)
	sys.stdout.flush()
	return sys.stdin.readline()[:-1]

def setup():
	admin_tokens = [
			'forum:view','forum:create','forum:edit','forum:delete',
			'forum:post','forum:reply','forum:poll','forum:mod',
			'user:view','user:create','user:edit','user:delete',
			'user:invite','user:permissions', 'user:like',
			'user:warn','user:ban','user:invisible','user:online',
			'user:groups','pm:view','pm:send','mail:send',
			'mail:mass','admin:view','admin:warn','admin:change',
			'admin:userview','log:view','log:delete','group:view',
			'group:create','group:edit','group:delete',
			'shoutbox:view','shoutbox:post','shoutbox:edit',
			'shoutbox:remove','thread:view','thread:create',
			'thread:edit','thread:remove','thread:reply',
			'thread:like','thread:attach','thread:sticky',
			'thread:move','thread:annoucements',
			'category:view'		
		]
	user_tokens = [
		'user:view','user:invite', 'user:online', 'pm:view', 
		'pm:send', 'mail:send','shoutbox:view',
		'shoutbox:post', 'thread:view', 'thread:create',
		'thread:reply','thread:like', 'thread:edit',
	]
	guest_tokens = [ 
		'user:create','thread:view'	
	]
	
	db.create_all()

	user = User(
		anonymous=True,
		username='guest',
		display='Guest',
		first_name='Ghosty',
		last_name='guest',
		termsagree = True,
		privacyagree = True,
		)

	db.session.add(user)

	permission = UserPermission(token='user:create')
	db.session.add(permission)
	user.permissions.append(permission)
		
	admin_group = Group(name='administrators', display='Administrators')
	db.session.add(admin_group)

	guest_group = Group(name='guests', display='Guests')
	db.session.add(admin_group)

	user_group = Group(name='users', display='Users')
	db.session.add(user_group)
	
	for token in admin_tokens:
		permission = GroupPermission(token=token)
		db.session.add(permission)
		admin_group.permissions.append(permission)

	for token in guest_tokens:
		permission = GroupPermission(token=token)
		db.session.add(permission)
		guest_group.permissions.append(permission)

	for token in user_tokens:
		permission = GroupPermission(token=token)
		db.session.add(permission)
		user_group.permissions.append(permission)

	user.groups.append(guest_group)
	db.session.commit()
	print("Setup is completed")

def setup_mass_users():
	for i in range(0, 100):
		user = User(
			anonymous=True,
			username='guest {}'.format(i),
			display='Guest{}'.format(i),
			first_name='',
			last_name='',
			)

		db.session.add(user)

		permission = UserPermission(token='user:create')
		db.session.add(permission)
		user.permissions.append(permission)

	db.session.commit()
	print('Done adding users')

def add_user():
	username = readline('Username: ')

	if User.query.filter_by(username=username).count():
		print('error: username already in use.')
		return

	display = readline('Display name: ')
	password = getpass('Password: ')

	if getpass('Confirm password: ') != password:
		print('error: passwords do not match.')
		return

	first_name = readline('First name: ')
	last_name = readline('Last name: ')
	birthday = readline('birthday as m d y: ')
	
	user = User(
			activated = True,
			username = username.lower(),
			display = display,
			password = password,
			first_name = first_name,
			last_name = last_name,
			birthday = datetime.strptime(birthday, '%m %d %Y'),
		)
	db.session.add(user)
	db.session.commit()

def add_user_to_group():
	username = readline('Username: ')
	user = User.query.filter_by(username=username.lower()).first()

	if user is None:
		print('error: user not found.')
		return

	name = readline('Group: ')
	group = Group.query.filter_by(name=name.lower()).first()

	if group is None:
		print('error: group not found.')
		return

	user.groups.append(group)
	db.session.commit()

def delete_post():
	post_id = readline('id: ')
	post = Post.query.filter_by(id=post_id).first()

	if post is None:
		print('error: post not found.')
		return

	
	name = readline('Do you want to delete? Type y for yes or n for no: ')
	

	if name == 'y':
		if post.thread_post:
			Thread.query.filter_by(id=post.thread_id).delete()
		else:
			post.delete()
		db.session.commit()
	
class CommandLine(object):
	def init_app(self, app):
		app.cli.command('setup')(setup)
		app.cli.command('setup_delete_post')(delete_post)
		app.cli.command('setup_mass')(setup_mass_users)
		app.cli.add_command(user, 'user')
		app.cli.command('add-user')(add_user)
		app.cli.command('add-user-to-group')(add_user_to_group)

cli = CommandLine()
