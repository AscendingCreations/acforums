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
from wtforms.validators import ValidationError, InputRequired
from wtforms import BooleanField, TextField, PasswordField, DateTimeField
from wtforms import validators, SelectField, SubmitField, TextAreaField
from wtforms import IntegerField
from datetime import datetime
from .utils import MultiCheckboxField
import pendulum

def checkforselection(form, field):
		if form.parent.data == 0 and form.category.data == 0:
			raise ValidationError('One of these fields need to be set.')
			
class AdminUserForm(FlaskForm):
	username = TextField('Username', description='Users username.',
		validators=[validators.Length(min=4,
		max=256)])
	display = TextField('Display name', description='Users Display name.',
		validators=[validators.Length(min=4,
		max=256)])
	first_name = TextField('First name',
		description='Users first name (e.g. John).',
		validators=[validators.Length(max=64)])
	last_name = TextField('Last name', 
		description='Users last name (e.g. Smith).',
		validators=[validators.Length(max=64)])
	email = TextField('E-mail address', description='Users e-mail address.')
	password = PasswordField('Password', validators=[validators.Required()])
	new_password = PasswordField('New password',
		description='Choose a strong password for the Users account.')
	confirm_password = PasswordField('Confirm password',
		validators=[validators.EqualTo('new_password')],
		description="""
		Confirm password by repeating it again. This is to make sure that you have entered
		your password correctly.
		""")
	signature = CKEditorField('Signature', description='Users signature.',
		validators=[validators.Length(max=512)])
	title = TextField('Title', description='Users Custom Title.',
		validators=[validators.Length(max=64)])
	timezone = SelectField(label='TimeZone', 
		choices=[(tz, tz) for tz in pendulum.timezones],
		description='Users current Timezone.')
	banned = BooleanField('Banned', description='Ban or  Un-ban user.')
	activated = BooleanField('Activated', description='Activate or  Deactivate user.')

class AdminUserListForm(FlaskForm):
	password = PasswordField('Password', validators=[validators.Required()])
	selected = MultiCheckboxField('Selected', choices=[], coerce=int)

class AdminCreateUserForm(FlaskForm):
	username = TextField('Username',
		validators=[validators.Length(min=4,
		max=256)],
		description='Their Login name.')
	display = TextField('Display name', 
		validators=[validators.Length(min=4,
		max=256)],
		description='Appropriate name to display to other users.')
	first_name = TextField('First name', description='Their first name (e.g. John).',
		validators=[validators.Length(max=64)])
	last_name = TextField('Last name', description='Their last name (e.g. Smith).',
		validators=[validators.Length(max=64)])
	email = TextField('E-mail address',
		validators=[validators.Required(), validators.Email('Must be an actule email address.')],
		description="""
		Their e-mail address.
		If you need this changed please contact an Administrator. 
		""")
	password = PasswordField('Password',
		validators=[validators.Required()],
		description='Confirm your changes by entering your password.')
	new_password = PasswordField('New password',
		validators=[validators.Required(), validators.Length(min=4)],
		description="""
		Choose a strong password. A strong password should be easy to remember,
		but hard to guess.
		""")
	confirm_password = PasswordField('Confirm password',
		validators=[validators.EqualTo('new_password')],
		description="""
		Confirm the password by repeating it again. This is to make sure that you have entered
		the password correctly.
		""")
	title = TextField('Title',
		description="""
		Custom Titles. Please follow the forum rues when creating a Title.
		""",
		validators=[validators.Length(max=64)])

class UserGroupForm(FlaskForm):
	selected = SelectField('Groups', choices=[])
	password = PasswordField('Password',
		validators=[validators.Required()])
	add = SubmitField()
	remove = SubmitField()

class UserPermForm(FlaskForm):
	perms = TextField('Permissions', validators=[validators.Required()])
	password = PasswordField('Password', validators=[validators.Required()])
	add = SubmitField()
	remove = SubmitField()

class GroupListForm(FlaskForm):
	password = PasswordField('Password', validators=[validators.Required()])
	selected = MultiCheckboxField('Selected', choices=[], coerce=int)

class GroupCreateForm(FlaskForm):
	selected = SelectField('Groups', choices=[])
	name = TextField('Name', validators=[validators.Required(),
		validators.Length(min=4,
		max=256)])
	display = TextField('Display', validators=[validators.Required(),
		validators.Length(min=4,
		max=256)])
	password = PasswordField('Password', validators=[validators.Required()])

class GroupEditForm(FlaskForm):
	perms = TextField('Permissions')
	name = TextField('Name')
	display = TextField('Display')
	password = PasswordField('Password', validators=[validators.Required()])
	add = SubmitField('Add/Save')
	remove = SubmitField()

class BoardCreateForm(FlaskForm):
	title = TextField('Title*', validators=[validators.Required(),
		validators.Length(min=4,
		max=64)])
	description = TextAreaField('Description',validators=[
		validators.Length(max=64)])
	parent = SelectField('Parent', choices=[], coerce=int,
		validators=[checkforselection])
	category = SelectField('Categories', choices=[], coerce=int,
		validators=[checkforselection])
	link = TextField('Link', validators=[
		validators.Length(max=64)])
	order = IntegerField('Order')
	view = MultiCheckboxField('View', choices=[], coerce=int)
	post = MultiCheckboxField('Post', choices=[], coerce=int)
	reply = MultiCheckboxField('Reply', choices=[], coerce=int)
	poll = MultiCheckboxField('Poll', choices=[], coerce=int)
	password = PasswordField('Password', validators=[validators.Required()])

class BoardEditForm(FlaskForm):
	title = TextField('Title*',validators=[validators.Required(),
		validators.Length(min=4,
		max=64)])
	description = TextAreaField('Description',validators=[
		validators.Length(max=64)])
	parent = SelectField('Parent', choices=[], coerce=int)
	category = SelectField('Categories', choices=[], coerce=int)
	link = TextField('Link',validators=[
		validators.Length(max=64)])
	order = IntegerField('Order')
	password = PasswordField('Password', validators=[validators.Required()])
	
class CategoryCreateForm(FlaskForm):
	title = TextField('Title*',validators=[validators.Required(),
		validators.Length(min=4,
		max=64)])
	order = IntegerField('Order')
	view = MultiCheckboxField('View', choices=[], coerce=int)
	password = PasswordField('Password', validators=[validators.Required()])
	
class CategoryEditForm(FlaskForm):
	title = TextField('Title*',validators=[validators.Required(),
		validators.Length(min=4,
		max=64)])
	order = IntegerField('Order')
	password = PasswordField('Password', validators=[validators.Required()])

class DeleteForumForm(FlaskForm):
	password = PasswordField('Password', validators=[validators.Required()])

class WarningForm(FlaskForm):
	selected = MultiCheckboxField('Selected', choices=[], coerce=int)
	password = PasswordField('Password', validators=[validators.Required()])

class EditWarningForm(FlaskForm):
	text = CKEditorField('Text',
		validators=[validators.Required(),
		validators.Length(min=15, max=8192)])
	points = IntegerField('Points')
	password = PasswordField('Password', validators=[validators.Required()])
	
class InfoForm(FlaskForm):
	recountboard = SubmitField('Recount board posts')
	recountuser = SubmitField('Recount user posts')
	resetterms = SubmitField('Reset the Terms Agreements')
	resetprivacy = SubmitField('Reset the Privacy Agreements')