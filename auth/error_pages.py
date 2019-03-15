#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Author(s):
#  - S.J.R. van Schaik <stephan@synkhronix.com>
from flask import Blueprint, render_template
from flask_login import login_required

error_pages = Blueprint('error_pages', __name__)

@error_pages.app_errorhandler(410)
def expired(*args, **kwargs):
	return render_template('error/410.htm')

@error_pages.app_errorhandler(403)
def forbidden(*args, **kwargs):
	return render_template('error/403.htm')

@error_pages.app_errorhandler(404)
def page_not_found(*args, **kwargs):
	return render_template('error/404.htm')
