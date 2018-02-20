# -*- coding: utf-8 -*-
"""
    Lex Bot Tester
    Copyright (C) 2017-2018  Diego Torres Milano

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
import unittest

from lex_bot_tester.aws.lex.lexruntimeclient import LexRuntimeClient, DialogState

BOT_NAME = 'OrderFlowers'
BOT_ALIAS = 'OrderFlowersLatest'
USER_ID = 'ClientId'

CANCEL = "Cancel"
ORDER_SOME_FLOWERS = "I would like to order some flowers"


class LexRuntimeClientTests(unittest.TestCase):

    def setUp(self):
        super(LexRuntimeClientTests, self).setUp()
        self.lrc = LexRuntimeClient(BOT_NAME, BOT_ALIAS, USER_ID)

    def tearDown(self):
        super(LexRuntimeClientTests, self).tearDown()

    def test_post_text(self):
        self.assertEqual(self.lrc.post_text(CANCEL)['intentName'], CANCEL)

    def test_get_slots(self):
        self.assertIsNotNone(self.lrc.post_text(CANCEL))
        self.assertEqual(self.lrc.get_slots(), {})

    def test_get_dialog_state(self):
        self.assertIsNotNone(self.lrc.post_text(CANCEL))
        self.assertEqual(self.lrc.get_dialog_state(), DialogState.READY_FOR_FULFILLMENT)

    def test_get_slot(self):
        self.assertIsNotNone(self.lrc.post_text(ORDER_SOME_FLOWERS))
        self.assertEqual(self.lrc.get_intent_name(), 'OrderFlowers')
        self.assertEqual(self.lrc.get_slot('FlowerType'), None)

    def test_get_intent_name(self):
        self.assertIsNotNone(self.lrc.post_text(CANCEL))
        self.assertEqual(self.lrc.get_intent_name(), CANCEL)

    def test_get_message(self):
        self.assertIsNotNone(self.lrc.post_text(ORDER_SOME_FLOWERS))
        self.assertEqual(self.lrc.get_message(), 'What type of flowers would you like to order?')

    def test_get_slot_to_elicit(self):
        self.assertIsNotNone(self.lrc.post_text(ORDER_SOME_FLOWERS))
        self.assertEqual(self.lrc.get_intent_name(), 'OrderFlowers')
        self.assertEqual(self.lrc.get_slot_to_elicit(), 'FlowerType')

    def test_get_response(self):
        self.assertIsNotNone(self.lrc.post_text(ORDER_SOME_FLOWERS))
        r = self.lrc.get_response()
        self.assertIsNotNone(r)
        self.assertIsNotNone(r['ResponseMetadata'])

    def test_get_session_attributes(self):
        self.assertIsNotNone(self.lrc.post_text(ORDER_SOME_FLOWERS, session_attributes={'sa': 'SA'}))
        self.assertEqual(self.lrc.get_session_attributes()['sa'], 'SA')


if __name__ == '__main__':
    unittest.main()
