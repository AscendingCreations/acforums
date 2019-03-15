#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Author(s):
#  - Andrew Wheeler <lordsatin@hotmail.com>
#
from flask import Blueprint, render_template, request, redirect, url_for
from flask_authz import rights
from flask_login import current_user
from .models import authz, Group

nav = Blueprint('nav', __name__)

@nav.app_template_global()
def get_nav(user_id):
	nav = []
	subnav = []

	if (user_id == current_user.id):
		if authz.check(rights.authenticated()):
			subnav.append(('Profile', url_for('user.profile',user_id=current_user.id)))
			if authz.check(rights.permission(Group, 'pm:view')):
				title = 'Private Messages:({})'.format(current_user.unreadpms)
			subnav.append((title, url_for('user.view_pms')))
			subnav.append(('Sent Private Messages', url_for('user.view_sent_pms')))
		
		if subnav:
			nav.append(('Dashboard', subnav))
			subnav = []

		if authz.check(rights.permission(Group, 'user:view')):
			subnav.append(('Edit', url_for('user.profile_edit')))
			subnav.append(('Delete Account', url_for('user.profile_delete')))

		if subnav:
			nav.append(('Settings', subnav))
			subnav = []
	
	return nav

@nav.app_template_global()
def get_admin_nav():
	nav = []
	subnav = []

	if authz.check(rights.authenticated()):
		subnav.append(('Info', url_for('admin.info')))
	
	if authz.check(rights.permission(Group, 'forum:view')):
		subnav.append(('Category & Boards', url_for('admin_forum.admin_view_forum')))

	if authz.check(rights.permission(Group, 'admin:userview')):
		subnav.append(('User List', url_for('admin.admin_view_users')))

	if authz.check(rights.permission(Group, 'group:view')):
		subnav.append(('Group List', url_for('admin.admin_view_groups')))

	if authz.check(rights.permission(Group, 'user:warn')):
		subnav.append(('Warning List', url_for('warn.admin_view_warnings')))

	if authz.check(rights.permission(Group, 'log:view')):
		subnav.append(('Logs', url_for('logs.view_logs')))
		
	subnav.append(('Return To Forum', url_for('forum.view_forum')))

	if subnav:
		nav.append(('Dashboard', subnav))
		subnav = []

	return nav

@nav.app_template_global()	
def url_for_other_page(page):
	args = request.view_args.copy()
	args['page'] = page
	return url_for(request.endpoint, **args)