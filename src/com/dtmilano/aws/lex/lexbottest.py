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
from __future__ import print_function

import re
import sys
from unittest import TestCase

from com.dtmilano.aws.lex.lexruntimeclient import LexRuntimeClient
from com.dtmilano.util.conversion import to_camel_case

VERBOSE = False
DEBUG = False


class LexBotTest(TestCase):
    def setUp(self):
        super(LexBotTest, self).setUp()

    def tearDown(self):
        super(LexBotTest, self).tearDown()

    def conversations_text(self, bot_name, bot_alias, user_id, conversations):
        """
        Helper method for tests using text conversations.

        :param bot_name: the bot name
        :param bot_alias: the bot alias
        :param user_id: the user id
        :param conversations: the list of conversations
        """
        self.csc = LexRuntimeClient(bot_name, bot_alias, user_id)
        for c in conversations:
            for ci in c:
                if VERBOSE:
                    print(ci.send)
                result = ci.receive
                if DEBUG:
                    print('Sending: {}'.format(ci.send))
                response = self.csc.post_text(ci.send)
                self.assertEqual(result.intent_name, self.csc.get_intent_name())
                self.assertIsNotNone(response)
                slots = self.csc.get_slots()
                if DEBUG:
                    print('\tslots={}'.format(slots))
                self.assertEqual(result.dialog_state, self.csc.get_dialog_state(),
                                 msg='Invalid dialog state, response={}'.format(response))
                for rk in result.keys():
                    try:
                        e = result[rk]
                        a = slots[to_camel_case(rk)]
                        if isinstance(e, re._pattern_type):
                            self.assertRegexpMatches(a, e)
                        else:
                            self.assertEqual(e, a)
                    except KeyError as ex:
                        print("ERROR:" + str(ex), file=sys.stderr)
                        # If it's None we let the slot to be not present
                        self.assertIsNone(result[rk])
