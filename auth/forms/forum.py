#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Author(s):
#  - Andrew Wheeler <lordsatin@hotmail.com>
from flask import current_app
from flask_wtf import FlaskForm
from flask_ckeditor import CKEditorField
from wtforms import BooleanField, TextField, PasswordField
from wtforms import validators, SelectField, SubmitField
from .utils import MultiCheckboxField

class BoardViewForm(FlaskForm):
	delete = SubmitField('Delete')
	move = SubmitField('Move')
	sticky = SubmitField('Sticky')
	unsticky = SubmitField('UnSticky')
	selected = MultiCheckboxField('Selected', choices=[], coerce=int)
	password = PasswordField('Password')

class BoardMoveForm(FlaskForm):
	boards = SelectField('Boards', choices=[], coerce=int)
	password = PasswordField('Password')
	
class BoardDeleteForm(FlaskForm):
	password = PasswordField('Password')
	
class ThreadCreateForm(FlaskForm):
	title = TextField('Title',
		validators=[validators.Required(),
		validators.Length(min=4, max=64)])
	text = CKEditorField('Text',
		validators=[validators.Required(),
		validators.Length(min=15, max=8192)])
	sticky = BooleanField('Sticky')
	password = PasswordField('Password')

class PostForm(FlaskForm):
	text = CKEditorField('Text',
		validators=[validators.Required(),
		validators.Length(min=15, max=8192)])
	password = PasswordField('Password')

class PostsForm(FlaskForm):
	password = PasswordField('Password', validators=[validators.Required()])
	selected = MultiCheckboxField('Selected', choices=[], coerce=int)