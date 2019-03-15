#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Author(s):
#  - S.J.R. van Schaik <stephan@synkhronix.com>
#
 
from authz.rights import *
from flask import request

def argument(name):
	def func(authz, *args, **kwargs):
		return True if request.args.get(name) else False

	return func
