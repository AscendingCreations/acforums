#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Author(s):
#  - S.J.R. van Schaik <stephan@synkhronix.com>
#
def any_of(*rights):
	def func(authz, *args, **kwargs):
		for right in rights:
			if right(authz, *args, **kwargs):
				return True

		return False

	return func

def all_of(*rights):
	def func(authz, *args, **kwargs):
		for right in rights:
			if not right(authz, *args, **kwargs):
				return False

		return True

	return func

def none_of(*rights):
	def func(authz, *args, **kwargs):
		for right in rights:
			if right(authz, *args, **kwargs):
				return False

		return True

	return func

def permission(ctx, token):
	def func(authz, *args, **kwargs):
		return ctx.has(token.format(**kwargs)) or False

	return func

def authenticated():
	def func(authz, *args, **kwargs):
		return authz.get_user().is_authenticated()

	return func

def group(name):
	def func(authz, *args, **kwargs):
		return authz.get_user().in_group(name)

	return func
