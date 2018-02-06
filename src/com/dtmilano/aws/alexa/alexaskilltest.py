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
from __future__ import print_function

from time import sleep
from unittest import TestCase

from com.dtmilano.aws.alexa.alexaskillmanagementclient import AlexaSkillManagementClient, SimulationResult

VERBOSE = False
DEBUG = False


class AlexaSkillTest(TestCase):
    """
    Base class for Alexa Skill Tests.
    """
    def setUp(self):
        super(AlexaSkillTest, self).setUp()

    def tearDown(self):
        super(AlexaSkillTest, self).tearDown()

    def conversation_text(self, skill_name, intent_name, conversation, verbose=VERBOSE, use_tts=False):
        # type: (AlexaSkillTest, str, str, list, bool, bool) -> SimulationResult
        """
        Helper method for tests using text conversations.

        :param intent_name: the intent name
        :param use_tts: whether to use TTS
        :param skill_name: the bot name
        :param conversation: the conversation
        :param verbose: produce verbose output

        Iterates over the list of :py:attr:conversations and each py:class::ConversationItem, sends the corresponding
        text and analyzes the response.

        For this response, it asserts that:

        * the intent name is correct
        * the response is not None
        * the dialog state is as defined in the item
        * the slots contain the specified values, as declared in the item

        """
        self.asmc = AlexaSkillManagementClient(skill_name)
        self.asmc.conversation_start(intent_name, conversation, verbose)
        simulation_result = None
        fulfilled = False
        for c in conversation:
            simulation_result = self.asmc.conversation_step(c, verbose, debug=False)
            fulfilled = fulfilled or (simulation_result.is_fulfilled() if simulation_result else False)
            sleep(1)
        self.asmc.conversation_end()
        self.assertTrue(fulfilled,
                        'Some slots have no values:\n{}\n'.format(
                            simulation_result.get_slots() if simulation_result else 'no slots available')
                        )
        return simulation_result
