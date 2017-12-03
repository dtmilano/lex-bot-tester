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
from aetypes import Enum

import boto3
from six import string_types


class DialogState(Enum):
    ELICIT_INTENT = 'ElicitIntent'
    CONFIRM_INTENT = 'ConfirmIntent'
    ELICIT_SLOT = 'ElicitSlot'
    FULFILLED = 'Fulfilled'
    READY_FOR_FULFILLMENT = 'ReadyForFulfillment'
    FAILED = 'Failed'


class LexRuntimeClient:
    """
    Lex Runtime Client.
    """

    def __init__(self, bot_name, bot_alias, user_id):
        self.__client = boto3.client('lex-runtime')
        self.bot_name = bot_name
        self.bot_alias = bot_alias
        self.user_id = user_id
        self.__response = None

    def post_text(self, text, request_attributes=None, session_attributes=None):
        """
        Post text.

        :rtype: dict
        :param text: the text to post
        :param request_attributes: the request attributes if any
        :param session_attributes: the session attributes if any
        :return: the response from the server
        """
        if request_attributes is None:
            request_attributes = {}
        if session_attributes is None:
            session_attributes = {}
        self.__response = self.__client.post_text(
            botName=self.bot_name,
            botAlias=self.bot_alias,
            userId=self.user_id,
            sessionAttributes=session_attributes,
            requestAttributes=request_attributes,
            inputText=text
        )
        return self.__response

    def get_slots(self):
        slots = self.__response['slots']
        for k in slots:
            v = slots[k]
            if isinstance(v, string_types):
                slots[k] = v.lower()
        return slots

    def get_slot(self, name):
        return self.get_slots()[name]

    def get_intent_name(self):
        return self.__response['intentName']

    def get_dialog_state(self):
        return self.__response['dialogState']

    def get_message(self):
        return self.__response['message']

    def get_slot_to_elicit(self):
        return self.__response['slotToElicit']

    def get_response(self):
        return self.__response

    def get_session_attributes(self):
        return self.__response['sessionAttributes']
