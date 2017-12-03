# lex-bot-tester
*AWS Lex Bot Tester* is a library that simplifies the creation of AWS Lex Bot tests. Using AWS Lex Models Client this utility inspects the properties of the available Bots and creates specific Results classes to be used by the tests. 

# Installation
Run

    pip install lex-bot-tester
    

# Example
Once you have the package installed, you can create tests like this one, which uses the well know *OrderFlowers* bot.

```python
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
import re
import unittest

from com.dtmilano.aws.lex.conversation import Conversation, ConversationItem
from com.dtmilano.aws.lex.lexbottest import LexBotTest
from com.dtmilano.aws.lex.lexmodelsclient import LexModelsClient
from com.dtmilano.aws.lex.lexruntimeclient import DialogState

RE_DATE = re.compile('\d+-\d+-\d+')

BOT_NAME = 'OrderFlowers'
BOT_ALIAS = 'OrderFlowersLatest'
USER_ID = 'ClientId'


class OrderFlowersTests(LexBotTest):
    def test_conversations_text(self):
        lmc = LexModelsClient(BOT_NAME, BOT_ALIAS)
        conversations = []
        for i in lmc.get_intents_for_bot():
            r = lmc.get_result_class_for_intent(i)
            if i == 'OrderFlowers':
                conversations.append(Conversation(
                    ConversationItem('I would like to order some roses',
                                     r(DialogState.ELICIT_SLOT, flower_type='roses')),
                    ConversationItem('white', r(DialogState.ELICIT_SLOT, flower_type='roses', flower_color='white')),
                    ConversationItem('next Sunday',
                                     r(DialogState.ELICIT_SLOT, flower_type='roses', flower_color='white',
                                       pickup_date=RE_DATE)),
                    ConversationItem('noon', r(DialogState.CONFIRM_INTENT, flower_type='roses', flower_color='white',
                                               pickup_date=RE_DATE, pickup_time='12:00')),
                    ConversationItem('yes', r(DialogState.FULFILLED, flower_type='roses', flower_color='white',
                                              pickup_date=RE_DATE, pickup_time='12:00')),
                ))
            elif i == 'Cancel':
                conversations.append(Conversation(
                    ConversationItem('Cancel', r(DialogState.READY_FOR_FULFILLMENT))
                ))
        self.conversations_text(BOT_NAME, BOT_ALIAS, USER_ID, conversations)


if __name__ == '__main__':
    unittest.main()
```
