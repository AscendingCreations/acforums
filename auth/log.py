#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Author(s):
#  - Andrew Wheeler <lordsatin@hotmail.com>
#
from itsdangerous import SignatureExpired
from datetime import datetime, timedelta
from flask import abort, Blueprint, flash, redirect, render_template, request
from flask import current_app, url_for
from flask_login import current_user
from flask_authz import rights

from .models import db, authz, Group, User, Log
from .utils import mail, parse_token, sign_token
from .forms import LogForm

log_view = Blueprint('logs', __name__)

def create_log(event='unknown event', type=2):
	log = Log (
				type = type,
				event = event,
				date = datetime.utcnow(),
			)
	db.session.add(log)
	current_user.users_logs.append(log)
	db.session.commit()

@log_view.route('/admin/logs', methods=('GET', 'POST'), defaults={'page': 1})
@log_view.route('/admin/logs/<int:page>', methods=('GET', 'POST'))
@authz.requires(rights.permission(Group, 'log:view'), methods=('GET', 'POST'))
@authz.requires(rights.permission(Group, 'log:delete'), methods=('POST'))
def view_logs(page):
	log_page = Log.query.paginate(page, current_app.config['LOGS_PER_PAGE'], False)
	form = LogForm()

	if not log_page.items and page != 1:
		abort(404)

	form.selected.choices = [(log.id, '') for log in log_page.items]

	if form.validate_on_submit():
		if current_user.password == form.password.data:
			logs = Log.query.filter(Log.id.in_(form.selected.data)).all()
			
			for log in logs:
				db.session.delete(log) 

			db.session.commit()
			create_log('Logs were deleted', 1)
			flash('Logs were deleted successfully.', 'success')
			return redirect(url_for('logs.view_logs', page=1))
		else:
			flash('The user credentials specified are invalid.', 'error')

	logs = zip(form.selected, log_page.items) if log_page.items else None
	return render_template('admin/logs.htm', form=form, logs=logs, pages=log_page)