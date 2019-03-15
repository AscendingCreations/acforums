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
from flask import current_app, url_for
from flask_login import current_user, login_user, logout_user
from flask_authz import rights
import pendulum

from .models import db, authz, Group, User, Warning, PM
from .forms import WarningForm, EditWarningForm, CreateWarningForm
from .log import create_log

warnings = Blueprint('warn', __name__)

@warnings.route('/admin/warn', methods=('GET', 'POST'), defaults={'page': 1})
@warnings.route('/admin/warn/<int:page>', methods=('GET', 'POST'))
@authz.requires(rights.all_of(rights.permission(Group, 'user:warn'),
	rights.permission(Group, 'admin:view')), methods=('GET', 'POST'))
@authz.requires(rights.permission(Group, 'admin:warn'), methods=('POST'))
def admin_view_warnings(page):
	form = WarningForm()
	warn_page = Warning.query.paginate(page,
		current_app.config['WARNINGS_PER_PAGE'], False)

	if not warn_page.items and page != 1:
		abort(404)

	form.selected.choices = [(warning.id, '') for warning in warn_page.items]

	if form.validate_on_submit():
		if current_user.password != form.password.data:
			flash('Password incorrect', 'error')
			return redirect(url_for('warn.admin_view_warnings', page=page))

		warnings = Warning.query.filter(Warning.id.in_(form.selected.data)).all()
		
		for warning in warnings:
			warning.user.warning_points -= warning.points
			print(warning.id)
			if warning.user.banned:
				if warning.user.warning_points < \
					current_app.config['MAX_WARNINGS']:
					warning.user.banned = False
			db.session.delete(warning)

		db.session.commit()
		create_log('Warnings were deleted', 1)
		flash('Warnings were deleted', 'success')
		return redirect(url_for('warn.admin_view_warnings'))

	warnings = zip(form.selected, warn_page.items) if warn_page.items else None

	return render_template('admin/warnings.htm', form=form, warnings=warnings,
		pages=warn_page)

@warnings.route('/admin/warning/<int:id>', methods=('GET', 'POST'))
@authz.requires(rights.all_of(rights.permission(Group, 'user:warn'),
	rights.permission(Group, 'admin:view')), methods=('GET', 'POST'))
@authz.requires(rights.permission(Group, 'admin:warn'), methods=('POST'))
def admin_edit_warning(id):
	form = EditWarningForm()
	warning = Warning.query.get(id) or abort(404)

	if form.validate_on_submit():
		if current_user.password == form.password.data:
			warning.user.warning_points -= warning.points
			warning.message = form.text.data
			warning.points = form.points.data
			warning.user.warning_points += warning.points

			if warning.user.warning_points >= \
				current_app.config['MAX_WARNINGS']:
				if warning.user.username != current_app.config['OWNER']:
					warning.user.banned = True

			db.session.commit()
			flash('Warning was Updated', 'success')
			create_log('Warning {} was updated.'.format(id), 1)
			return redirect(url_for('warn.admin_view_warnings'))
		else:
			flash('Password incorrect', 'error')

	form.text.data = warning.message
	form.points.data = warning.points

	return render_template('admin/edit_warning.htm', form=form, warning=warning)

@warnings.route('/user/warning/<int:user_id>', methods=('GET', 'POST'))
@authz.requires(rights.permission(Group, 'user:warn'), methods=('GET', 'POST'))
def mod_give_warning(user_id):
	form = CreateWarningForm()
	user = User.query.get(user_id) or abort(404)

	if not user:
		abort(404)

	if form.validate_on_submit():
		if current_user.password == form.password.data:
		
			warning = Warning (
				message = form.text.data,
				points = form.points.data,
				date = datetime.utcnow(),
				)

			db.session.add(warning)
			user.user_warnings.append(warning)
			current_user.warnings_issued.append(warning)
			user.warning_points += warning.points

			if user.warning_points >= \
				current_app.config['MAX_WARNINGS']:
				if user.username != current_app.config['OWNER']:
					user.banned = True

			pm  = PM (
				title = 'Warning Points Recieved',
				message = warning.message,
				date = datetime.utcnow(),
			)
			
			db.session.add(pm)
			user.user_pms.append(pm)
			current_user.sent_pms.append(pm)
			user.unreadpms += 1

			db.session.commit()
			create_log('Warning Given to user: {}'.format(user.username), 1)
			flash('Warning was Created', 'success')
			return redirect(url_for('forum.view_forum'))
		else:
			flash('Password incorrect', 'error')

	return render_template('user/warn.htm', form=form, user=user)