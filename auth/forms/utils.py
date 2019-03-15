#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Author(s):
#  - S.J.R. van Schaik <stephan@synkhronix.com>
from flask_wtf import FlaskForm
from wtforms import widgets, SelectMultipleField

class MultiCheckboxField(SelectMultipleField):
	"""
	A multiple-select, except displays a list of checkboxes.

	Iterating the field will produce subfields, allowing custom rendering of
	the enclosed checkbox fields.
	"""
	widget = widgets.ListWidget(prefix_label=False)
	option_widget = widgets.CheckboxInput()

class SelectForm(FlaskForm):
	selected = MultiCheckboxField('Selected', choices=[], coerce=int)
