#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Author(s):
#  - Andrew Wheeler <lordsatin@hotmail.com>
#  - S.J.R. van Schaik <stephan@synkhronix.com>
from getpass import getpass
import sys
import click

from ..models import db, User, UserPermission, Email, Group, GroupPermission
import flask

user = flask.cli.AppGroup('user')

@user.group('emails', help='Manages e-mail addresses of the user')
def user_email():
	pass

@user.group('groups', help='Manages user groups')
def user_group():
	pass

@user.group('rights', help='Manages user rights')
def user_rights():
	pass

@user.command('add', help='Adds a new user')
@click.option('--email', prompt=True, help='The e-mail address of the user')
@click.password_option('--password', help='The password of the user')
@click.option('--display', prompt=True, help='The display name of the user')
def add_user(email, password, display):
	if Email.query.filter_by(email=email).count():
		print('error: the specified e-mail address is already in use.')
		return

	email = Email(
			email=email
		)
	db.session.add(email)

	user = User(
			activated=True,
			display=display,
			password=password,
		)
	user.email = email
	user.emails.append(email)
	db.session.add(user)
	db.session.commit()

@user.command('del', help='Deletes the user')
@click.option('--email', prompt=True,
	help='The e-mail address of the user to delete.')
def del_user(email):
	user = User.query.join(User.email).filter_by(email=email.lower()).first()

	if user is None:
		print('error: user not found.')
		return

	click.confirm('Are you sure you want to delete the user? '
		'This action cannot be undone.', abort=True)

	db.session.delete(user)
	db.session.commit()

@user_email.command('list')
def list_users():
	users = User.query.all()

	if users is None:
		print('error: user not found.')
		return

	for user in users:
		print(user.display)

@user_group.command('list')
@click.option('--email', prompt=True)
def list_groups(email):
	user = User.query.join(User.email).filter_by(email=email.lower()).first()

	if user is None:
		print('error: user not found.')
		return

	for group in user.groups:
		print(group.name)

@user_group.command('add')
@click.option('--email', prompt=True)
@click.option('--group', prompt=True)
def add_group(email, group):
	user = User.query.join(User.email).filter_by(email=email.lower()).first()

	if user is None:
		print('error: user not found.')
		return

	group = Group.query.filter_by(name=group).first()

	if group is None:
		print('error: group not found.')
		return

	user.groups.append(group)
	db.session.commit()

@user_group.command('del')
@click.option('--email', prompt=True)
@click.option('--group', prompt=True)
def del_group(email, group):
	user = User.query.join(User.email).filter_by(email=email.lower()).first()

	if user is None:
		print('error: user not found.')
		return

	group = Group.query.filter_by(name=group).first()

	if group is None:
		print('error: group not found.')
		return

	user.groups.remove(group)
	db.session.commit()

@user_rights.command('list', help='Lists the effective rights of the user')
@click.option('--email', prompt=True)
def list_rights(email):
	rights = {}
	user = User.query.join(User.email).filter_by(email=email.lower()).first()

	if user is None:
		print('error: user not found.')
		return

	for group in user.groups:
		for right in group.permissions:
			rights[right.token] = rights.get(right.token, []) + [group.name]

	for right in user.permissions:
		rights[right.token] = []

	for token, inherited in rights.items():
		if inherited:
			print('{} [inherited from {}]'.format(token, ' '.join(inherited)))
		else:
			print(token)

@user_rights.command('add', help='Adds the user right')
@click.option('--email', prompt=True)
@click.option('--right', prompt=True)
def add_right(email, right):
	user = User.query.join(User.email).filter_by(email=email.lower()).first()

	if user is None:
		print('error: user not found.')
		return

	right = UserPermission(token=right)
	db.session.add(right)
	user.permissions.append(right)

	db.session.commit()

@user_rights.command('add_by_display', help='Adds the user right')
@click.option('--display', prompt=True)
@click.option('--right', prompt=True)
def add_right_by_display(display, right):
	user = User.query.filter(User.display==display).first()

	if user is None:
		print('error: user not found.')
		return

	right = UserPermission(token=right)
	db.session.add(right)
	user.permissions.append(right)

	db.session.commit()
	
@user_rights.command('del', help='Deletes the user right')
@click.option('--email', prompt=True)
@click.option('--right', prompt=True)
def del_right(email, right):
	user = User.query.join(User.email).filter_by(email=email.lower()).first()

	if user is None:
		print('error: user not found.')
		return

	right = user.permissions.filter_by(token=right).delete()
	db.session.commit()
