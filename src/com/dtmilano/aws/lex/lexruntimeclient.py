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

import boto3
from six import string_types

from com.dtmilano.aws.polly.pollyclient import PollyClient


class DialogState:
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
        self.__polly = PollyClient()
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

    def post_text_to_speech(self, text, request_attributes=None, session_attributes=None):
        """

        :param text:
        :param request_attributes:
        :param session_attributes:
        :return:
        """
        speech = self.__polly.synthesize_speech(text)['AudioStream'].read()
        self.__response = self.post_content('audio/l16; rate=16000; channels=1', speech, 'text/plain; charset=utf-8',
                                            request_attributes,
                                            session_attributes)
        return self.__response

    def post_content(self, content_type, input_stream, accept, request_attributes=None,
                     session_attributes=None):
        """

        :param content_type:
        :param input_stream:
        :param accept:
        :param request_attributes:
        :param session_attributes:
        :return:
        """
        if request_attributes is None:
            request_attributes = {}
        if session_attributes is None:
            session_attributes = {}
        self.__response = self.__client.post_content(
            botName=self.bot_name,
            botAlias=self.bot_alias,
            userId=self.user_id,
            sessionAttributes=session_attributes,
            requestAttributes=request_attributes,
            contentType=content_type,
            inputStream=input_stream,
            accept=accept
        )
        return self.__response

    def get_slots(self):
        if self.__response is None:
            return None
        slots = self.__response['slots']
        for k in slots:
            v = slots[k]
            if isinstance(v, string_types):
                slots[k] = v.lower()
        return slots

    def get_slot(self, name):
        if name is not None:
            return self.get_slots()[name]
        return None

    def get_intent_name(self):
        return self.__response['intentName']

    def get_dialog_state(self):
        if self.__response is None:
            return None
        try:
            return self.__response['dialogState']
        except KeyError:
            return None

    def get_message(self):
        if self.__response is None:
            return None
        try:
            return self.__response['message']
        except KeyError:
            return None

    def get_slot_to_elicit(self):
        """
        Gets the slot name to elicit.
        If there's none, return None

        :return: the slot name or None
        """
        if self.__response is None:
            return None
        try:
            return self.__response['slotToElicit']
        except KeyError:
            return None

    def get_response(self):
        return self.__response

    def get_session_attributes(self):
        return self.__response['sessionAttributes']
