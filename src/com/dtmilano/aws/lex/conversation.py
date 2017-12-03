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

from com.dtmilano.aws.lex.resultbase import ResultBase


class ConversationItem(object):
    """
    Items of a Conversation.
    """

    def __init__(self, send, receive):
        if not isinstance(send, string_types):
            raise RuntimeError('send should be a string')
        if not isinstance(receive, ResultBase):
            raise RuntimeError('receive should be a result')
        self.send = send
        self.receive = receive


class Conversation(list):
    """
    Conversation is a list of ConversationItem.
    """

    def __init__(self, *args):
        super(Conversation, self).__init__()
        for arg in args:
            self.append(arg)

    def append(self, conversation_item):
        if not isinstance(conversation_item, ConversationItem):
            raise RuntimeError('conversation_item should be a ConversationItem')
        super(Conversation, self).append(conversation_item)
