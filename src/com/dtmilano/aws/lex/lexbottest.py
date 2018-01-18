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

from com.dtmilano.aws.lex.conversation import Conversation, ConversationItem
from com.dtmilano.aws.lex.lexmodelsclient import LexModelsClient
from com.dtmilano.aws.lex.lexruntimeclient import LexRuntimeClient, DialogState
from com.dtmilano.util.color import Color
from com.dtmilano.util.conversion import to_camel_case, to_snake_case

VERBOSE = False
DEBUG = False


class LexBotTest(TestCase):
    def setUp(self):
        super(LexBotTest, self).setUp()

    def tearDown(self):
        super(LexBotTest, self).tearDown()

    def conversations_text(self, bot_name, bot_alias, user_id, conversations, verbose=VERBOSE, use_tts=False):
        # type: (str, str, str, list, bool, bool) -> None
        """
        Helper method for tests using text conversations.

        :param use_tts:
        :param bot_name: the bot name
        :param bot_alias: the bot alias
        :param user_id: the user id
        :param conversations: the list of conversations
        :param verbose: produce verbose output

        Iterates over the list of :py:attr:conversations and each py:class:: ConversationItem, sends the corresponding
        text and analyzes the response.

        For this response, it asserts that:

        * the intent name is correct
        * the response is not None
        * the dialog state is as defined in the item
        * the slots contain the specified values, as declared in the item

        """
        self.csc = LexRuntimeClient(bot_name, bot_alias, user_id)
        for c in conversations:
            if verbose:
                print("Start conversation")
                print("------------------")
            for ci in c:
                before_message = self.csc.get_message()
                before_dialog_state = self.csc.get_dialog_state()
                before_slots = self.csc.get_slots()
                slot_to_elicit = self.csc.get_slot_to_elicit()
                if verbose:
                    if before_message:
                        print(Color.colorize(' Bot: {}'.format(before_message), Color.WHITE, Color.BRIGHT_BLUE))
                    print(Color.colorize('User: {}'.format(ci.send),
                                         Color.BRIGHT_YELLOW if use_tts else Color.BRIGHT_WHITE, Color.BRIGHT_BLACK))
                expected_result = ci.receive
                if DEBUG:
                    print('** expected_result={}'.format(expected_result))
                if before_slots:
                    # if we haven't specified slots that had a value already, we are assuming that their value didn't
                    #  change and we complete the expected_result with the previous values
                    for s in before_slots.keys():
                        if to_snake_case(s) not in expected_result and before_slots[s]:
                            if DEBUG:
                                print('** adding key={} to expected_result with value "{}"'.format(to_snake_case(s),
                                                                                                   before_slots[s]))
                            expected_result[to_snake_case(s)] = before_slots[s]
                if DEBUG:
                    print('Sending: {}'.format(ci.send))
                if use_tts:
                    response = self.csc.post_text_to_speech(ci.send)
                else:
                    response = self.csc.post_text(ci.send)
                self.assertEqual(expected_result.intent_name, self.csc.get_intent_name())
                self.assertIsNotNone(response)
                slots = self.csc.get_slots()
                if DEBUG:
                    print('\tslots={}'.format(slots))
                self.assertEqual(expected_result.dialog_state, self.csc.get_dialog_state(),
                                 msg='Invalid dialog state, response={}'.format(response))
                if DEBUG:
                    print(expected_result)
                    print(response)
                if len(expected_result) > 0:
                    for rk in expected_result.keys():
                        try:
                            e = expected_result[rk]
                            a = slots[to_camel_case(rk)]
                            self.assertIsNotNone(a,
                                                 msg='{} slot is None: rk={} e={} a={} send="{}" elicit={} slots={}'.format(
                                                     to_camel_case(rk),
                                                     rk,
                                                     e,
                                                     a,
                                                     ci.send,
                                                     slot_to_elicit,
                                                     slots))
                            if isinstance(e, re._pattern_type):
                                try:
                                    # noinspection PyCompatibility
                                    self.assertRegex(a, e)
                                except AttributeError as ex:
                                    # python 2.7.x
                                    self.assertRegexpMatches(a, e)
                            else:
                                self.assertEqual(e, a)
                        except KeyError as ex:
                            print('ERROR: rk={} msg={}'.format(rk, str(ex)), file=sys.stderr)
                            if before_dialog_state == DialogState.ELICIT_SLOT and slot_to_elicit is not None:
                                self.assertEqual(ci.send.lower(), self.csc.get_slot(slot_to_elicit).lower())
                            # If it's None we let the slot to be not present
                            self.assertIsNone(expected_result[rk])
                else:
                    # need to know the previous dialog state to know if it was ELICIT_SLOT, however, because
                    # the only possibility of having an empty results is in the first step of the conversation
                    # which has no previous dialog state, we may try...
                    if before_dialog_state == DialogState.ELICIT_SLOT and slot_to_elicit is not None:
                        self.assertEqual(ci.send.lower(), self.csc.get_slot(slot_to_elicit).lower())
            if verbose:
                print('\n')

    def conversations_text_helper(self, bot_alias, bot_name, user_id, conversation_definition, verbose=VERBOSE,
                                  use_tts=False):
        # type: (str, str, str, dict, bool, bool) -> None
        """
        Helper method for tests using text conversations.

        :param bot_name: the bot name
        :param bot_alias: the bot alias
        :param user_id: the user id
        :param conversation_definition: the conversation definition list
        :param verbose: produce verbose output
        :param use_tts:

        Iterates over the :py:attr:conversation_definition list and if there are matching Intents the conversation
        definition items are extracted and the values are used as arguments to the creation of ConversationItems.

        Finally, conversation_text() is invoked.
        """
        lmc = LexModelsClient(bot_name, bot_alias)
        conversations = []
        for i in lmc.get_intents_for_bot():
            r = lmc.get_result_class_for_intent(i)
            if i in conversation_definition:
                c = Conversation()
                for cdi in conversation_definition[i]:
                    if len(cdi) != 3:
                        raise AttributeError('Expected item with len=3 (actual len={})'.format(len(cdi)))
                    kwargs = {}
                    for k in cdi[2]:
                        # in case the slot name has been specified in CamelCase we convert to snake_case here
                        kwargs[to_snake_case(k)] = cdi[2][k]
                    rr = r(cdi[1], **kwargs)
                    ci = ConversationItem(cdi[0], rr)
                    c.append(ci)
                conversations.append(c)
            self.conversations_text(bot_name, bot_alias, user_id, conversations, verbose, use_tts)
