from authz import rights
from flask import abort, Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from .forms import AppForm, SelectForm
from .models import db, authz, App, Group

app_view = Blueprint('settings', __name__)

@app_view.route('/settings', methods=('GET', 'POST'))
@authz.requires(rights.permission(Group, 'settings:view'), methods=('GET', 'POST'))
@authz.requires(rights.permission(Group, 'settings:change'), methods=('POST'))
def view_settings():
	apps = current_user.apps

	form = SelectForm()
	form.selected.choices = [(app.id, '') for app in apps]

	if form.validate_on_submit():
		App.query.filter(db.and_(
				App.id.in_(form.selected.data),
				App.owner_id==current_user.id
			)).delete()
		db.session.commit()

	apps = zip(form.selected, apps) if apps else None

	return render_template('app/view_apps.htm',
		form=form,
		apps=apps)

@app_view.route('/apps/add', methods=('GET', 'POST'))
@authz.requires(rights.permission(Group, 'app:create'), methods=('GET', 'POST'))
def add_app():
	form = AppForm()

	if form.validate_on_submit():
		app = App(
				name=form.name.data.lower(),
				display=form.name.data,
				redirect_url=form.redirect_url.data,
				owner=current_user,
			)
		secret = app.generate_secret()
		db.session.add(app)
		db.session.commit()

		flash('The app has been added successfully.', 'success')

		return render_template('app/view_app.htm',
			app=app,
			secret=secret,
			form=form)

	return render_template('app/add_app.htm',
		form=form)

@app_view.route('/apps/<int:app_id>', methods=('GET', 'POST'))
@authz.requires(rights.permission(App, 'app:view:{app_id}'), methods=('GET', 'POST'))
@authz.requires(rights.permission(App, 'app:edit:{app_id}'), methods=('POST'))
def view_app(app_id):
	app = App.query.get(app_id) or abort(404)
	form = AppForm(obj=app)

	if form.validate_on_submit():
		app.redirect_url = form.redirect_url.data
		db.session.commit()

		flash('Your changes have been saved.', 'success')

		return redirect(url_for('app.view_apps'))

	return render_template('app/view_app.htm',
		app=app,
		form=form)

@app_view.route('/apps/<int:app_id>/reset-secret')
@authz.requires(rights.permission(App, 'app:edit:{app_id}'))
def reset_secret(app_id):
	app = App.query.get(app_id) or abort(404)
	form = AppForm(obj=app)

	secret = app.generate_secret()
	db.session.commit()

	return render_template('app/view_app.htm',
		app=app,
		secret=secret,
		form=form)
