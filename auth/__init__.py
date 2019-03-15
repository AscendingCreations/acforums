#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Author(s):
#  - Andrew Wheeler <lordsatin@hotmail.com>
#
from wtforms import TextField, PasswordField
from flask import Flask, render_template, session
from flask_sessionstore import Session, SqlAlchemySessionInterface
from flask_login import LoginManager
from flask_gravatar import Gravatar
from flask_ckeditor import CKEditor
from datetime import datetime
import redis

from .models import db, migrate, login_manager, User, Email, rdb, UserOnline
from .utils import mail

from .api import api
from .cli import cli
from .error_pages import error_pages
from .nav import nav
from .menu import menu
from .user import user_view
from .admin import admin_view
from .admin_forums import admin_forum_view
from .forum import forum_view
from .warn import warnings
from .log import log_view

from .tasks import celery, reset_user_warnings

def create_app(info=None):
	app = Flask(__name__)
	app.config.from_object('config')
	Session(app)
	ckeditor = CKEditor(app)
	gravatar = Gravatar(app,size=100,rating='pg',default='identicon',
		force_default=False, force_lower=False, use_ssl=True, base_url=None)

	app.register_blueprint(error_pages)
	app.register_blueprint(nav)
	app.register_blueprint(menu)
	app.register_blueprint(user_view)
	app.register_blueprint(admin_view)
	app.register_blueprint(admin_forum_view)
	app.register_blueprint(forum_view)
	app.register_blueprint(warnings)
	app.register_blueprint(log_view)

	db.init_app(app)
	SqlAlchemySessionInterface(app, db, "sessions", "my_", permanent=False)
	migrate.init_app(app, db)
	login_manager.init_app(app)
	mail.init_app(app)
	cli.init_app(app)
	celery.conf.update(app.config)
	reset_user_warnings.apply_async(countdown=60)

	@app.before_request
	def set_online_status():
		from flask import request
		from flask_login import current_user
		
		if current_user.is_authenticated():
			current_user.lastactive = datetime.utcnow()
			rdb.setex(current_user.id, 600, current_user.display)
			db.session.commit()

	@app.shell_context_processor
	def shell_context():
		return {'app': app, 'db': db}

	return app
