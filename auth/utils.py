#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Author(s):
#  - S.J.R. van Schaik <stephan@synkhronix.com>
from flask import current_app
from flask_mail import Mail
from itsdangerous import TimedJSONWebSignatureSerializer

def sign_token(payload, tag=None, expires_in=None):
	serializer = TimedJSONWebSignatureSerializer(
		current_app.config.get('SIGNATURE_SECRET_KEY'),
		salt=tag,
		expires_in=expires_in)

	return serializer.dumps(payload)

def parse_token(payload, tag=None):
	serializer = TimedJSONWebSignatureSerializer(
		current_app.config.get('SIGNATURE_SECRET_KEY'),
		salt=tag)

	return serializer.loads(payload)

mail = Mail()
