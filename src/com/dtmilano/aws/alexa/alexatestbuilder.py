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
import datetime
import sys

from com.dtmilano.aws.alexa.alexaskillmanagementclient import AlexaSkillManagementClient


class AlexaTestBuilder(object):
    @staticmethod
    def __input_text(slot, prompt, simulated_input=None):
        if simulated_input and slot in simulated_input:
            return simulated_input[slot]
        if prompt:
            return input(prompt + ': ')
        else:
            return input(slot + ': ')

    @staticmethod
    def learn_conversation(skill_name, intent_name, simulated_input=None):
        asmc = AlexaSkillManagementClient(skill_name)
        conversation = [
            {'slot': None, 'text': AlexaTestBuilder.__input_text('$launch_text', 'Launch', simulated_input)}]
        interaction_model = asmc.get_interaction_model()
        slots = interaction_model.get_slots_by_intent(intent_name)
        if slots:
            for s in slots:
                conversation.append({'slot': s.get_name(), 'text': None})
        else:
            print('WARNING: slots is empty for intent={}'.format(intent_name), file=sys.stderr)
            interaction_model.print(file=sys.stderr)
        asmc.fill_prompts_in_conversation(conversation, intent_name, interaction_model)
        for c in conversation:
            if c['slot']:
                c['text'] = AlexaTestBuilder.__input_text(c['slot'], c['prompt'], simulated_input)
        conversation.append(
            {'slot': None, 'prompt': 'Confirmation',
             'text': AlexaTestBuilder.__input_text('$confirmation_text', 'Confirmation', simulated_input)})
        return conversation

    @staticmethod
    def create_test(test_name=None, skill_name=None, intent_name=None, conversation=None):
        if not test_name:
            test_name = input('Test method name: ')
        if not skill_name:
            skill_name = input('Skill: ')
        asmc = AlexaSkillManagementClient(skill_name)
        if not intent_name:
            intent_names = [i['name'] for i in asmc.get_interaction_model().get_intents()]
            if len(intent_names) == 1:
                intent_name = intent_names[0]
                print('Using intent {}'.format(intent_name))
            else:
                intent_name = input('Intent [{}]: '.format(intent_names))
        if not conversation:
            conversation = AlexaTestBuilder.learn_conversation(skill_name, intent_name)
        d = {'test_name': test_name, 'skill_name': skill_name, 'intent_name': intent_name, 'conversation': conversation,
             'now': str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))}
        s = '''
    def {test_name}(self):
        """
        Test generated by lex-bot-tester on {now}
        """
        skill_name = '{skill_name}'
        intent = '{intent_name}'
        conversation = {conversation}
        simulation_result = self.conversation_text(skill_name, intent, conversation, verbose=verbose)
        self.assertIsNotNone(simulation_result)
        self.assertTrue(simulation_result.is_fulfilled())
    '''.format(**d)
        return s


def main(args):
    print('Generating test...')
    print(AlexaTestBuilder.create_test(*args))


if __name__ == '__main__':
    main(sys.argv[1:])