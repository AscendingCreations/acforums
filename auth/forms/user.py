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
from wtforms import BooleanField, TextField, PasswordField, DateTimeField
from wtforms import validators, SelectField, IntegerField, SubmitField
from .utils import MultiCheckboxField
from datetime import datetime
import pendulum

class SignUpForm(FlaskForm):
	username = TextField('Username *',
		validators=[validators.Required()],
		description="""
		Choose an appropriate user name as a handle to identify yourself with when logging in. As it
		will only be used to log in to your account, it will never be shown publicly anywhere. Do
		keep in mind that, once chosen, your user name cannot be changed later on.
		""")
	display = TextField('Display name *',
		validators=[validators.Required()],
		description="""
		Choose an appropriate name to display to other users.
		""")
	email = TextField('E-mail address *',
		validators=[validators.Email()],
		description="""
		The e-mail address that will be used for further correspondence.
		""")
	password = PasswordField('Password *',
		validators=[validators.Required()],
		description="""
		Choose a strong password for your account. A strong password should be easy to remember,
		but hard to guess.
		""")
	confirm_password = PasswordField('Confirm password *',
		validators=[validators.Required(), validators.EqualTo('password')],
		description="""
		Confirm your password by repeating it again. This is to make sure that you have entered
		your password correctly.
		""")
	issixteen = BooleanField('Confirm that you are 16 years old or Older one last time',
		validators=[validators.Required()],description="""
		Please Confirm you are 16 Years or older. As you must be at least 16 years of age to register 
		and give permission to store your data.
		""")
	loginconfirm = BooleanField('Confirm we can store your Email and User name',validators=[validators.Required()],
		description="""
		Please give us permission to long term store your email and user name for the duration of the account.
		You must give this permission in order to register an account as this information is used to login to your account,
		making it vital for the forums operation. This information is only visible by Administrators 
		who have account management authority. If you do Spam the forums, this information will be used to 
		identify you through stopforumspam.com.
		""")
	displayconfirm = BooleanField('Confirm we can store your Display name.',validators=[validators.Required()],
		description="""
		Please give us permission to long term store your Display Name for the duration of the account.
		You must give this permission in order to register an account as this information is used to display 
		whom created a post to the public. The display name will be public accessible and is require for the forum software
		to function correctly.
		""")

class SignInForm(FlaskForm):
	id = TextField('Username or e-mail Address')
	password = PasswordField('Password')
	remember_me = BooleanField('Remember me')

class InvitationForm(FlaskForm):
	email = TextField('E-mail address', validators=[validators.Email()],
		description = """
		The e-mail address to send the invitation to.
		""")

class ProfileForm(FlaskForm):
	username = TextField('Username',
		description="""
		used to identify yourself when logging in. It is only be used to log in
		to your account and it will not be shown publicly. 
		your user name cannot be changed.
		""")
	display = TextField('Display name',
		description="""
		Choose an appropriate name to display to other users.
		""",validators=[validators.Length(min=4,
		max=256)])
	first_name = TextField('First name',
		description="""
		Your first name (e.g. John).
		""",validators=[validators.Length(max=64)])
	last_name = TextField('Last name',
		description="""
		Your last name (e.g. Smith).
		""",validators=[validators.Length(max=64)])
	email = TextField('E-mail address',
		description="""
		Your currently set e-mail address.
		If you need this changed please contact an Administrator. 
		""")
	old_password = PasswordField('Password',
		validators=[validators.Required()],
		description="""
		Confirm your changes by entering your password.
		""")
	new_password = PasswordField('New password',
		description="""
		Choose a strong password for your account. A strong password should be easy to remember,
		but hard to guess.
		""")
	confirm_password = PasswordField('Confirm password',
		validators=[validators.EqualTo('new_password')],
		description="""
		Confirm your password by repeating it again. This is to make sure that you have entered
		your password correctly.
		""")
	signature = CKEditorField('Signature',
		description="""
		Your signature, Please follow the forum rules when creating a signature.
		""",validators=[validators.Length(max=512)])
	title = TextField('Title',
		description="""
		Custom Titles. Please follow the forum rues when creating a Title.
		""",validators=[validators.Length(max=64)])
	timezone = SelectField(label='TimeZone', 
		choices=[(tz, tz) for tz in pendulum.timezones], description="""
		Your current Timezone.
		""")
	loginconfirm = BooleanField('Confirm we can store your Email and User name',
	description="""
		Please give us permission to long term store your email and user name for the duration of the account.
		You must give this permission in order to register an account as this information is used to login to your account,
		making it vital for the forums operation. This information is only visible by Administrators 
		who have account management authority. If you do Spam the forums, this information will be used to 
		identify you through stopforumspam.com. If you disallow us to store this data then your account will be removed.
		""")
	displayconfirm = BooleanField('Confirm we can store your Display name.', description="""
		Please give us permission to long term store your Display Name for the duration of the account.
		You must give this permission in order to register an account as this information is used to display 
		whom created a post to the public. The display name will be public accessible and is require for the forum software
		to function correctly. If you disallow us to store this data then your account will be removed.
		""")
	avatarconfirm =BooleanField('Confirm we can display your Gravatar.', description="""
		Please give us permission to Display your Gravatar within the forums. 
		If you do not give us permission we will use a default avatar in its place.
		Your Gravatar will be publicly viewable.
		""")
	nameconfirm = BooleanField('Confirm we can store your First and Last name.', description="""
		Please give us permission to store your First and Last name. Your first and last name will only be 
		viewable by members within your profile. If you do not allow storing your name then First and Last name will
		be blank even if you attempt to place data within it.
		""")
	titleconfirm =BooleanField('Confirm we can store your Title.', description="""
		Please give us permission to store your custom title. The title will be publicly viewable. If you do not allow
		us to store your own custom then it will be reverted to the forum default title.
		""")
	sigconfirm = BooleanField('Confirm we can store your signature.', description="""
		Please give us permission to store your signature. Your signature will be publicly viewable. If you do not allow 
		us to store your signature then it will be blank.
		""")
	hideprofile = BooleanField('Hide Your Profile.', description="""
		You can enable this option to Hide your profile and prevent others from private messaging you. 
		If enabled Only Administrators and Moderators can view your profile.
		""")

class CreateWarningForm(FlaskForm):
	text = CKEditorField('Text',
		validators=[validators.Required(),
		validators.Length(min=8, max=512)])
	points = IntegerField('Points', validators=[validators.Required(),
		validators.NumberRange(min=1, max=5)])
	password = PasswordField('Password', validators=[validators.Required()])

class CreatePMForm(FlaskForm):
	text = CKEditorField('Text',
		validators=[validators.Required(),
		validators.Length(min=8, max=8192)])
	display = TextField('Display name',validators=[validators.Length(min=4,
		max=256)])
	title = TextField('Title',validators=[validators.Length(min=4,
		max=256)])
	password = PasswordField('Password', validators=[validators.Required()])

class PMsForm(FlaskForm):
	selected = MultiCheckboxField('Selected', choices=[], coerce=int)
	password = PasswordField('Password', validators=[validators.Required()])

class ViewPMForm(FlaskForm):
	delete = SubmitField('Delete')
	reply = SubmitField('Reply')
	password = PasswordField('Password')
	
class AgreementForm(FlaskForm):
	issixteen = BooleanField('Confirm that you are 16 years old or Older',
		validators=[validators.Required()],description="""
		Please Confirm you are 16 Years or older. As you must be at least 16 years of age to register 
		and give permission to store your data.
		""")
	agree = BooleanField('Agree',  validators=[validators.Required()])
	accept = SubmitField('Accept')

class ViewProfileForm(FlaskForm):
	pm = SubmitField('Private Message')

class ProfileDeleteForm(FlaskForm):
	password = PasswordField('Password')