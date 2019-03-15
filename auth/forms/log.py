#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Author(s):
#  - Andrew Wheeler <lordsatin@hotmail.com>
from flask import current_app
from flask_wtf import FlaskForm
from wtforms import validators, SelectField, PasswordField
from .utils import MultiCheckboxField

class LogForm(FlaskForm):
	selected = MultiCheckboxField('Selected', choices=[], coerce=int)
	password = PasswordField('Password', validators=[validators.Required()])
