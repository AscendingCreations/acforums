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
from flask import current_app, url_for, session
from flask_login import current_user, login_user, logout_user
from flask_authz import rights
from flask_mail import Message

import pendulum

from .models import db, authz, Group, User, Email, PM, Board, Thread, Post
from .forms import SignUpForm, SignInForm, InvitationForm, ProfileForm, SelectForm
from .forms import CreatePMForm, PMsForm, ViewPMForm
from .forms import AgreementForm, ViewProfileForm, ProfileDeleteForm
from .utils import mail, parse_token, sign_token
from .forum import check_right
from .log import create_log
from .tasks import send_async_email, delete_user

user_view = Blueprint('user', __name__)

@user_view.route('/test', methods=('GET', 'POST'))
def send_test():
	form = SignUpForm()
	msg = Message('Hello from Flask',
							recipients=["test"])
	msg.body = 'This is a test email sent from a background Celery task.'
	
	send_async_email.delay()
	flash("""Email was sent MUWAHAHAH""", 'success')

	return render_template('user/sign_up.htm', form=form)

@user_view.route('/auth')
@authz.requires(rights.authenticated(), handler=lambda: abort(401))
def auth():
	return ''

@user_view.app_template_global()
def get_current_user():
	return current_user

@user_view.app_template_global()
def conv_to_user_date(time):
	p = pendulum.instance(time)
	p = pendulum.timezone(current_user.timezone).convert(p)
	return p.format('DD MMMM YYYY', locale='EN')

@user_view.app_template_global()
def conv_to_user_time(time):
	p = pendulum.instance(time)
	p = pendulum.timezone(current_user.timezone).convert(p)
	return p.format('DD MMMM YYYY hh:mm:ss A', locale='EN')

@user_view.route('/agreement', methods=('GET', 'POST'))
@authz.requires(rights.any_of(
		rights.permission(Group, 'user:create'),
		rights.argument('invitation'),
		rights.authenticated()
), methods=('GET', 'POST'))
def user_agreement():
	form = AgreementForm()
	
	if form.validate_on_submit():
		if form.accept.data:
			if current_user.is_authenticated():
				current_user.termsagree = 1
				db.session.commit()
				flash('You have accepted the new Terms and Conditions successfully.', 'success')
				return redirect(url_for('forum.view_forum'))
			else:
				session['accepted'] = 1
				return redirect(url_for('user.user_privacy'))
		else:
			abort(404)

	return render_template('user/agreement.htm', form=form)

@user_view.route('/privacy_policy', methods=('GET', 'POST'))
@authz.requires(rights.any_of(
		rights.permission(Group, 'user:create'),
		rights.argument('invitation'),
		rights.authenticated()
), methods=('POST'))
def user_privacy():
	form = AgreementForm()
	
	if form.validate_on_submit():
		if form.accept.data:
			if current_user.is_authenticated():
				current_user.privacyagree = 1
				db.session.commit()
				flash('You have accepted the new Privacy Policy successfully.', 'success')
				return redirect(url_for('forum.view_forum'))
			else:
				session['agreed'] = 1
				return redirect(url_for('user.sign_up'))
		else:
			abort(404)
	
	return render_template('user/privacy.htm', form=form, user=current_user)
	
@user_view.route('/sign-up', methods=('GET', 'POST'))
@authz.requires(rights.any_of(
		rights.permission(Group, 'user:create'),
		rights.argument('invitation')
), methods=('GET', 'POST'))
def sign_up():
	invitation = request.args.get('invitation')
	form = SignUpForm()
	accepted = session.get('accepted', 0)
	agreed = session.get('agreed', 0)
	
	if accepted != 1:
		flash('You must accept the terms of agreement before you can register.', 'error')
		return redirect(url_for('user.user_agreement'))
	
	if agreed != 1:
		flash('You must agree with the privacy policy before you can register.', 'error')
		return redirect(url_for('user.user_privacy'))
		
	if invitation:
		try:
			invitation = parse_token(invitation, tag='user:invite')
		except SignatureExpired:
			abort(410)
		except:
			abort(403)

		del form.email

	if form.validate_on_submit():
		user = User(
				username=form.username.data.lower(),
				display=form.display.data,
				password=form.password.data,
				issixteen=form.issixteen.data,
				loginconfirm=form.loginconfirm.data,
				displayconfirm=form.displayconfirm.data,
				regdate = datetime.utcnow(),
				lastactive = datetime.utcnow(),
				termsagree = True,
				privacyagree = True,
				activated = True,
			)
			
		if User.query.filter_by(username=user.username.lower()).first():
			flash('Username can not be used, please choose Another', 'error')
			return render_template('user/sign_up.htm', form=form)

		if User.query.filter_by(display=user.display.lower()).first():
			flash('Display can not be used, please choose Another', 'error')
			return render_template('user/sign_up.htm', form=form)
			
		if Email.query.filter_by(email=form.email.data.lower()).first():
			flash('Email can not be used, please choose Another', 'error')
			return render_template('user/sign_up.htm', form=form)

		db.session.add(user)
		name = 'users'
		groups = Group.query.filter_by(name=name.lower()).first()

		if groups is None:
			print('error: group not found.')
			return

		user.groups.append(groups)

		if invitation:
			user.email = Email(email=invitation)
			db.session.add(user.email)
			user.emails.append(user.email)
			user.activated = True
			flash('You have been signed up successfully.', 'success')
			session['accepted'] = 0
		else:
			user.email = Email(email=form.email.data)
			db.session.add(user.email)
			user.emails.append(user.email)
			activation=sign_token(form.email.data, tag='user:activate')
			#mail.send_message(
				#recipients=[form.email.data],
				#subject='Your activation for a ascendingcreations.com account',
				#body=render_template('mail/activate.htm',
					#user=user,
					#activation=activation))
			session['accepted'] = 0
			session['agreed'] = 0
		flash("""You have been signed up successfully. An e-mail has been sent 
			to the e-mail address specified to confirm that it is yours. Please be sure to also check your Spam box.""",
			'success')
		print(url_for('user.activate', activation=activation, _external=True))
		db.session.commit()

		return redirect(url_for('user.sign_in'))

	return render_template('user/sign_up.htm', form=form)

@user_view.route('/sign-in', methods=('GET', 'POST'))
def sign_in():
	form = SignInForm()
	
	if form.validate_on_submit():
		user = User.query.join(User.emails). \
			filter(Email.email==form.id.data.lower()).first() or \
			User.query.filter(User.username==form.id.data.lower()).first()

		if user is None:
			flash('The user credentials specified are invalid.', 'error')
			return render_template('user/sign_in.htm', form=form)

		if user.loginattempts >= 5:
			if user.loginlasttry < datetime.utcnow():
				user.loginattempts = 0
				db.session.commit()
			else:
				flash("""You failed to login to many times,
					Please try again later""", 'error')
				return render_template('user/sign_in.htm', form=form)

		if user.password != form.password.data:
			user.loginattempts += 1
			print(user.loginattempts)

			if user.loginattempts >= 5:
				flash("""You failed to login to many times,
				Please try again later""", 'error')
				user.loginlasttry = datetime.utcnow() + timedelta(minutes = 5)
			else:
				flash('The user credentials specified are invalid.', 'error')

			db.session.commit()
			return render_template('user/sign_in.htm', form=form)

		if not user.is_active():
			flash('Your account has not been activated yet.', 'error')
			return render_template('user/sign_in.htm', form=form)

		if user.banned and user.username != 'genusis':
			flash('Your account has been banned.', 'error')
			return render_template('user/sign_in.htm', form=form)

		user.loginattempts = 0
		user.lastactive = datetime.utcnow()
		db.session.commit()
		
		login_user(user, remember=form.remember_me.data)
		flash('You have signed in successfully.', 'success')

		return redirect(request.args.get('redirect', url_for('forum.view_forum')))

	return render_template('user/sign_in.htm', form=form)

@user_view.route('/sign-out')
def sign_out():
	logout_user()

	return redirect(url_for('user.sign_in'))

@user_view.route('/profile/<int:user_id>', methods=('GET', 'POST'))
@authz.requires(rights.any_of(
	rights.permission(Group, 'user:view'),
	rights.permission(Group, 'user:view:{user_id}')
), methods=('GET', 'POST'))
@authz.requires(rights.permission(Group, 'pm:send'),
	methods=('POST'))
def profile(user_id):
	form = ViewProfileForm()
	user = User.query.get(user_id) or abort(404)
	hidden = 0

	if user.hideprofile == True and user.id != current_user.id:
		if not check_right('admin:userview'):
			hidden = 1

	if request.method == 'POST':
		if form.validate_on_submit():
			if form.pm.data:
				session['pmmessage'] = "Hello"
				session['pmtitle'] = ""
				session['pmdisplay'] = user.display
				return redirect(url_for('user.send_pm'))

	return render_template('user/profile.htm', user=user, 
		form=form, hidden=hidden)

@user_view.route('/profile_edit', methods=('GET', 'POST'))
@authz.requires(rights.authenticated(), methods=('GET', 'POST'))
def profile_edit():
	form = ProfileForm(obj=current_user)

	if request.method == 'POST':
		if form.validate_on_submit():
			if form.old_password.data != current_user.password:
				flash('The password is incorrect.', 'error')
				return render_template('user/profile.htm', form=form)

			current_user.display = form.display.data

			if form.nameconfirm.data:
				current_user.first_name = form.first_name.data
				current_user.last_name = form.last_name.data
			else:
				current_user.first_name = ''
				current_user.last_name = ''

			if form.titleconfirm.data:
				current_user.title = form.title.data
			else:
				current_user.title = ''

			if form.sigconfirm.data:
				current_user.signature = form.signature.data
			else:
				current_user.signature = ''
			
			current_user.timezone = form.timezone.data
			current_user.loginconfirm = form.loginconfirm.data
			current_user.displayconfirm = form.displayconfirm.data
			current_user.avatarconfirm = form.avatarconfirm.data
			current_user.nameconfirm = form.nameconfirm.data
			current_user.titleconfirm = form.titleconfirm.data
			current_user.sigconfirm = form.sigconfirm.data
			current_user.hideprofile = form.hideprofile.data

			if form.new_password.data:
				current_user.password = form.new_password.data

			db.session.commit()
			create_log('User Modofied Own Profile', 2)
			flash('Your Changes have been made successfully.', 'success')
		else:
			flash("""Your Changes have not been made. You will need to fill out
				everything that is required to submit the changes""", 'error')
	return render_template('user/profile_edit.htm', form=form)

@user_view.route('/invite', methods=('GET', 'POST'))
@authz.requires(rights.permission(Group, 'user:invite'), methods=('GET', 'POST'))
def invite():
	form = InvitationForm()

	if form.validate_on_submit():
		mail.send_message(
				recipients=[form.email.data],
				subject='Your invitation to sign up for an account',
				body=render_template('mail/invite.htm',
					user=current_user,
					invitation=sign_token(form.email.data, tag='user:invite')))

		create_log('User Sent Inventations', 2)
		flash('The invitation has been sent to {}.'.format(form.email.data),
			'success')

	return render_template('user/invite.htm',
		form=form)

@user_view.route('/activate', methods=('GET', 'POST'))
@authz.requires(rights.any_of(
		rights.argument('activation')
), methods=('GET', 'POST'))
def activate():
	activation = request.args.get('activation')
	form = SignUpForm()

	if activation:
		try:
			activation = parse_token(activation, tag='user:activate')
		except SignatureExpired:
			abort(410)
		except:
			abort(403)

		email = Email(email=activation)
		user = User.query.join(User.emails). \
			filter(Email.email==activation.lower()).first()
			
		if user is None:
			abort(403)
	
		user.activated = True
		db.session.commit()
		flash('Your Account has been activated! You can now login.', 'success')
		return redirect(url_for('user.sign_in'))
	else:
		abort(403)

@user_view.route('/users', methods=('GET', 'POST'), defaults={'page': 1})
@user_view.route('/users/page/<int:page>', methods=('GET', 'POST'))
@authz.requires(rights.permission(Group, 'user:view'), methods=('GET', 'POST'))
def view_users(page):
	users_per_page = User.query.filter_by(hideprofile=False).paginate(page, 
			current_app.config['USERS_PER_PAGE'], False)

	if not users_per_page.items and page != 1:
		abort(404)

	return render_template('user/users.htm', users=users_per_page)
	
@user_view.route('/private_messages', methods=('GET', 'POST'), defaults={'page': 1})
@user_view.route('/private_messages/<int:page>', methods=('GET', 'POST'))
@authz.requires(rights.permission(Group, 'pm:view'), methods=('GET', 'POST'))
def view_pms(page):
	pm_page = PM.query.filter_by(user_id=current_user.id).paginate(page,
		current_app.config['PMS_PER_PAGE'], False)

	if not pm_page.items and page != 1:
		abort(404)

	form = PMsForm()
	form.selected.choices = [(pm.id, '') for pm in pm_page.items]

	if form.validate_on_submit():
		if current_user.password == form.password.data:
			pms = PM.query.filter(PM.id.in_(form.selected.data)).all()

			for pm in pms:
				if not pm.read:
					if pm.user.unreadpms > 0:
						pm.user.unreadpms -= 1
				db.session.delete(pm)

			db.session.commit()
			flash('Private Messages were deleted', 'success')
			return redirect(url_for('user.view_pms'))
		else:
			flash('Password incorrect', 'error')

	pms = zip(form.selected, pm_page.items) if pm_page.items else None

	return render_template('user/pms.htm', form=form, pms=pms, pages=pm_page,
		user=current_user, sent=0)

@user_view.route('/private_messages/send', methods=('GET', 'POST'))
@authz.requires(rights.permission(Group, 'pm:send'), methods=('GET', 'POST'))
def send_pm():
	form = CreatePMForm()

	if form.validate_on_submit():
		if current_user.password == form.password.data:
			user = User.query.filter(User.display==form.display.data).first()
			
			if user:
				if not user.hideprofile or  check_right('admin:userview'):
					pm  = PM (
						title = form.title.data,
						message = form.text.data,
						date = datetime.utcnow()
					)
					
					db.session.add(pm)
					user.user_pms.append(pm)
					current_user.sent_pms.append(pm)
					user.unreadpms += 1
					db.session.commit()
					create_log('User Sent PM to: {}'.format(user.display), 2)
					flash('Private Message was sent', 'success')
					return redirect(url_for('user.view_pms'))
				else:
					flash('User is not accepting Private Messages', 'error')
			else:
				flash('User does not exist', 'error')
		else:
			flash('Password incorrect', 'error')

	text = session.get('pmmessage', "")

	if text:
		form.text.data = text
		form.display.data = session.get('pmdisplay', "")
		form.title.data = session.get('pmtitle', "")
		session['pmmessage'] = ''
		session['pmtitle'] = ''
		session['pmdisplay'] = ''
	
	return render_template('user/pm_send.htm', form=form, user=current_user)
	
@user_view.route('/private_messages/view/<int:id>', methods=('GET', 'POST'))
@authz.requires(rights.permission(Group, 'pm:view'), methods=('GET', 'POST'))
def view_pm(id):
	form = ViewPMForm()
	pm = PM.query.get(id) or abort(404)

	if not pm.read:
		pm.read = True

		if current_user.unreadpms > 0:
			current_user.unreadpms -= 1

		db.session.commit()
	
	if form.validate_on_submit():
		if form.delete.data:
			if current_user.password == form.password.data:
				db.session.delete(pm)
				db.session.commit()
				flash('Private Message was Deleted', 'success')
				return redirect(url_for('user.view_pms'))
			else:
				flash('Password incorrect', 'error')

		elif form.reply.data:
			session['pmmessage'] = "Quote by {0}:<div style=\"background:#eeeeee;	border:1px \
				solid #cccccc; padding:5px 10px\">{1}</div>".format(pm.sender.display,
				pm.message)

			if pm.title.find('RE:', 0) >= 0:
				session['pmtitle'] = pm.title
			else:
				session['pmtitle'] = "RE:{}".format(pm.title)
			session['pmdisplay'] = pm.sender.display
			return redirect(url_for('user.send_pm'))

	return render_template('user/view_pm.htm', form=form, pm=pm,
		user=current_user,  sent=0)

@user_view.route('/sent_private_messages', methods=('GET', 'POST'), defaults={'page': 1})
@user_view.route('/sent_private_messages/<int:page>', methods=('GET', 'POST'))
@authz.requires(rights.permission(Group, 'pm:view'), methods=('GET', 'POST'))
def view_sent_pms(page):
	pm_page = PM.query.filter_by(sender_id=current_user.id).paginate(page,
		current_app.config['PMS_PER_PAGE'], False)

	if not pm_page.items and page != 1:
		abort(404)

	form = PMsForm()
	form.selected.choices = [(pm.id, '') for pm in pm_page.items]

	if form.validate_on_submit():
		if current_user.password == form.password.data:
			pms = PM.query.filter(PM.id.in_(form.selected.data)).all()

			for pm in pms:
				if pm.user.unreadpms > 0:
					 pm.user.unreadpms -= 1
				db.session.delete(pm)

			db.session.commit()
			flash('Private Messages were deleted', 'success')
			return redirect(url_for('user.view_sent_pms'))
		else:
			flash('Password incorrect', 'error')

	pms = zip(form.selected, pm_page.items) if pm_page.items else None

	return render_template('user/pms.htm', form=form, pms=pms, pages=pm_page,
		user=current_user, sent=1)

@user_view.route('/private_messages/view/sent/<int:id>', methods=('GET', 'POST'))
@authz.requires(rights.permission(Group, 'pm:view'), methods=('GET', 'POST'))
def view_sent_pm(id):
	form = ViewPMForm()
	pm = PM.query.get(id) or abort(404)

	if form.validate_on_submit():
		if form.delete.data:
			if current_user.password == form.password.data:
				if not pm.read:
					if pm.user.unreadpms > 0:
						pm.user.unreadpms -= 1

				db.session.delete(pm)
				db.session.commit()
				flash('Sent Private Message was deleted', 'success')
				return redirect(url_for('user.view_sent_pms'))
			else:
				flash('Password incorrect', 'error')

	return render_template('user/view_pm.htm', form=form, pm=pm,
		user=current_user, sent=1)

@user_view.route('/profile_delete', methods=('GET', 'POST'))
@authz.requires(rights.authenticated(), methods=('GET', 'POST'))
def profile_delete():
	form = ProfileDeleteForm()
	
	if request.method == 'POST':
		if form.validate_on_submit():
			if form.password.data == current_user.password:
				delete_user.delay(current_user.id)
				create_log('User Deleted Own Profile', 2)
			else:
					flash('The password is incorrect.', 'error')
			
	return render_template('user/user_delete.htm', form=form)
	
