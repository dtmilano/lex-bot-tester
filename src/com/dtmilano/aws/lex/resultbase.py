# -*- coding: utf-8 -*-
"""
    Lex Bot Tester
    Copyright (C) 2017  Diego Torres Milano

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
from six import string_types


class ResultBase(dict):
    """
    A base class for all the dynamically created Result classes.
    """

    def __init__(self, class_type, intent_name, dialog_state, **kwargs):
        """

        :type intent_name: ResultBase
        """
        super(ResultBase, self).__init__()
        self._type = class_type
        self.intent_name = intent_name
        self.dialog_state = dialog_state
        for key in kwargs:
            v = kwargs[key]
            if isinstance(v, string_types):
                v = v.lower()
            self[key] = v
