#! /usr/bin/env python
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

import random
import re
import sys
import unittest

from com.dtmilano.aws.alexa.alexaskillmanagementclient import AlexaSkillManagementClient
from com.dtmilano.aws.alexa.alexaskilltest import AlexaSkillTest
from com.dtmilano.util.color import Color
from com.dtmilano.util.conversion import number_to_words

DEBUG = False
verbose = False


class AlexaSkillManagementClientTests(AlexaSkillTest):

    def test_book_my_trip_reserve_a_car(self):
        skill_name = 'BookMyTripSkill'
        intent = 'BookCar'
        conversation = [
            {'slot': None, 'text': 'ask book my trip to reserve a car'},
            {'slot': 'CarType', 'text': 'midsize'},
            {'slot': 'PickUpCity', 'text': 'buenos aires'},
            {'slot': 'PickUpDate', 'text': 'tomorrow'},
            {'slot': 'ReturnDate', 'text': 'five days from now'},
            {'slot': 'DriverAge', 'text': 'twenty five'},
            {'slot': None, 'prompt': 'Confirmation', 'text': 'yes'}
        ]
        self.conversation_text(skill_name, intent, conversation, verbose=verbose)

    def test_high_low_game(self):
        asmc = AlexaSkillManagementClient('High Low Game')
        conversation = ['start high low game', 'yes', 'twenty four', '$random',
                        '$guess', '$guess', '$guess', '$guess', '$guess', '$guess', '$guess',
                        '$guess', '$guess', '$guess', '$guess']
        simulation_result = None
        lowest = 1
        highest = 100
        found = False
        for text in conversation:
            if text == '$random':
                text = number_to_words(random.randint(1, 100))
            elif text == '$guess':
                if simulation_result:
                    if DEBUG:
                        print('searching "{}" for number and condition'.format(simulation_result.get_output_speech()))
                    m = re.search('.*?(\d+) is correct.*', simulation_result.get_output_speech())
                    if m:
                        print(Color.colorize('* {} is correct !!! *'.format(m.group(1)), Color.BRIGHT_GREEN))
                        found = True
                        break
                    m = re.search('.*?(\d+) is too (\w+).*', simulation_result.get_output_speech())
                    if m:
                        n = int(m.group(1))
                        w = m.group(2)
                        if w == 'high':
                            highest = n
                            randint = random.randint(lowest, highest)
                            text = number_to_words(randint)
                            print('{} is top high, will try {} ({}) in [{}..{}]'.format(n, randint, text, lowest,
                                                                                        highest))
                        else:
                            lowest = n
                            randint = random.randint(lowest + 1, highest)
                            text = number_to_words(randint)
                            print(
                                '{} is top low, will try {} ({}) in [{}..{}]'.format(n, randint, text, lowest, highest))
                    else:
                        self.fail('simulation_result = {}'.format(simulation_result))
                else:
                    text = number_to_words(random.randint(1, 100))
            simulation_result = asmc.simulation(text, verbose=True)
            print(re.sub('<.*?speak>', '', simulation_result.get_output_speech()))
            print(re.sub('<.*?speak>', '', simulation_result.get_reprompt()))
        self.assertIs(found, True)

    def test_plan_my_trip(self):
        skill_name = 'PlanMyTripSkill'
        intent = 'PlanMyTrip'
        conversation = [
            {'slot': None, 'text': 'tell plan my trip I\'m going on a trip the day after tomorrow'},
            {'slot': 'toCity', 'text': 'new york'},
            {'slot': 'fromCity', 'text': 'seattle'}
        ]
        self.conversation_text(skill_name, intent, conversation, verbose=verbose)

    def test_crypto_get_price(self):
        skill_name = 'CryptoSkill'
        intent = 'GetPrice'
        coin = 'Bitcoin'
        conversation = [
            {'slot': None, 'text': 'ask Crypto what is the {} price?'.format(coin)},
        ]
        simulation_result = self.conversation_text(skill_name, intent, conversation, verbose=verbose)
        self.assertRegex(
            simulation_result.get_output_speech(),
            re.compile('Current price of {} is \d+(\.?\d+)* euros\.'.format(coin), re.IGNORECASE)
        )

    def test_decision_tree_recommend_a_job(self):
        skill_name = 'DecisionTreeSkill'
        intent = 'RecommendationIntent'
        conversation = [
            {'slot': None, 'text': 'ask Decision Tree to recommend a job'},
            {'slot': 'salaryImportance', 'text': 'don\'t care about money'},
            {'slot': 'personality', 'text': 'misunderstood'},
            {'slot': 'preferredSpecies', 'text': 'animals'},
            {'slot': 'bloodTolerance', 'text': 'no way'}
        ]
        self.conversation_text(skill_name, intent, conversation, verbose=verbose)


if __name__ == '__main__':
    verbose = '-v' in sys.argv or '--verbose' in sys.argv
    unittest.main()
