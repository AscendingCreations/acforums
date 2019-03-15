#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Author(s):
#  - Andrew Wheeler <lordsatin@hotmail.com>
#
from flask import Blueprint, url_for
from flask_authz import rights
from flask_login import current_user
from .models import authz, Group

menu = Blueprint('menu', __name__)

@menu.app_template_global()
def get_menu():
	nav = []

	if current_user.anonymous:
		nav.append(('Login', url_for('user.sign_in')))
		nav.append(('Register', url_for('user.user_agreement')))
	
	if authz.check(rights.authenticated()):
		nav.append(('Your profile', url_for('user.profile',user_id=current_user.id)))
		if authz.check(rights.permission(Group, 'pm:view')):
			title = 'PMs:({})'.format(current_user.unreadpms)
			nav.append((title, url_for('user.view_pms')))
		nav.append(('Sign out', url_for('user.sign_out')))

	if authz.check(rights.permission(Group, 'user:view')):
		nav.append(('User List', url_for('user.view_users')))

	if authz.check(rights.permission(Group, 'admin:view')):
		nav.append(('Admin Panel', url_for('admin.info')))
		
	return nav

