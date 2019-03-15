#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Author(s):
#  - S.J.R. van Schaik <stephan@synkhronix.com>
#
from functools import wraps

import authz
from authz import PermissionDenied, SecurityContext, UserMixin
from flask import current_app, request

try:
	from flask import _app_ctx_stack as stack
except ImportError:
	from flask import _request_ctx_stack as stack

class Authz(authz.Authz):
	def __init__(self, app=None):
		self.app = app
		self.error_handler = None

		if app is not None:
			self.init_app(app)

	def init_app(self, app):
		pass

	def requires(self, right, methods=('GET'), handler=None):
		def decorator(f):
			@wraps(f)
			def decorated_function(*args, **kwargs):
				if request.method not in methods:
					return f(*args, **kwargs)

				if self.check(right, **kwargs):
					return f(*args, **kwargs)

				if handler is not None:
					return handler(*args, **kwargs)

				if self.error_handler is not None:
					return self.error_handler(*args, **kwargs)

				raise PermissionDenied()

			return decorated_function

		return decorator
