#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Author(s):
#  - S.J.R. van Schaik <stephan@synkhronix.com>
#

from functools import wraps

class PermissionDenied(Exception):
	pass

class UserMixin(object):
	def is_authenticated(self):
		raise NotImplemented

	def in_group(self, name):
		raise NotImplemented

class Authz(object):
	def __init__(self):
		self.error_handler = None
		self.get_user = None

	def permission_denied(self, f):
		self.error_handler = f
		return f

	def user_loader(self, f):
		self.get_user = f
		return f

	def check(self, right, **kwargs):
		return right(self, **kwargs)

	def requires(self, right, handler=None):
		def decorator(f):
			@wraps(f)
			def decorated_function(*args, **kwargs):
				if self.check(**kwargs):
					return f(*args, **kwargs)

				if handler is not None:
					return handler(*args, **kwargs)

				if self.error_handler is not None:
					return self.error_handler(*args, **kwargs)

				raise PermissionDenied()

			return decorated_function

		return decorator
