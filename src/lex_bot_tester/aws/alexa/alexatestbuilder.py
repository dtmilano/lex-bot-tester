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
import warnings

from lex_bot_tester.aws.alexa.alexaskillmanagementclient import AlexaSkillManagementClient
from lex_bot_tester.util.color import Color


class AlexaTestBuilder(object):

    def __init__(self, generator='lex_bot_tester', generation_language='python'):
        self.generator = generator
        self.generation_language = generation_language

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
        interaction_model = asmc.get_interaction_model()
        samples = interaction_model.get_samples_by_intent(intent_name)
        invocation_name = interaction_model.get_invocation_name()
        conversation = [
            {'slot': None, 'text': AlexaTestBuilder.__input_text('$launch_text', 'Samples:\n{}\n\nLaunch ({})'.format(
                Color.colorize('\n'.join(samples), Color.BRIGHT_BLACK), invocation_name), simulated_input)}]
        if invocation_name not in conversation[0]['text']:
            warnings.warn('Launch text does not include invocation name \'{}\''.format(invocation_name))
        slots = interaction_model.get_slots_by_intent(intent_name)
        if slots:
            for s in slots:
                conversation.append({'slot': s.get_name(), 'text': None})
        else:
            warnings.warn('slots is empty for intent={}'.format(intent_name))
            interaction_model.print(file=sys.stderr)
        asmc.fill_prompts_in_conversation(conversation, intent_name, interaction_model)
        for c in conversation:
            if c['slot']:
                c['text'] = AlexaTestBuilder.__input_text(c['slot'], c['prompt'], simulated_input)
        try:
            if interaction_model.get_intent(intent_name)['confirmationRequired']:
                conversation.append(
                    {'slot': None, 'prompt': 'Confirmation',
                     'text': AlexaTestBuilder.__input_text('$confirmation_text', 'Confirmation', simulated_input)})
        except KeyError:
            pass
        return conversation

    @staticmethod
    def select_input(prompt, options):
        d = {}
        for i in range(len(options)):
            d[i] = options[i]
        while True:
            print(prompt)
            for i, o in d.items():
                print('{}: {}'.format(Color.colorize(i, Color.CYAN), o))
            s = input(Color.colorize('option> ', Color.CYAN))
            if not s:
                continue
            if s in d:
                return s
            try:
                if int(s) >= 0:
                    try:
                        return options[int(s)]
                    except IndexError:
                        continue
            except ValueError:
                continue

    def create_test(self, test_name=None, skill_name=None, intent_name=None, conversation=None):
        if not test_name:
            test_name = input('Test method name [test_my_skill]: ') or 'test_my_skill'
        if not skill_name:
            skill_names = AlexaSkillManagementClient.get_skill_names()
            if len(skill_names) == 1:
                skill_name = skill_names[0]
                print('Using skill {}'.format(skill_name))
            else:
                skill_name = None
                while skill_name not in skill_names:
                    skill_name = AlexaTestBuilder.select_input('Skill', skill_names)
        asmc = AlexaSkillManagementClient(skill_name)
        if not intent_name:
            intent_names = [i['name'] for i in asmc.get_interaction_model().get_intents()]
            if len(intent_names) == 1:
                intent_name = intent_names[0]
                print('Using intent {}'.format(intent_name))
            else:
                intent_name = None
                while intent_name not in intent_names:
                    intent_name = AlexaTestBuilder.select_input('Intent', intent_names)
        if not conversation:
            conversation = AlexaTestBuilder.learn_conversation(skill_name, intent_name)
        d = {'test_name': test_name, 'skill_name': skill_name, 'intent_name': intent_name, 'conversation': conversation,
             'now': str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")), 'generator': self.generator}
        if self.generation_language == 'python':
            s = self.create_test_python(d)
        else:
            raise RuntimeError('language not yet supported')
        return s

    @staticmethod
    def create_test_python(d):
        s = '''
    def {test_name}(self):
        """
        Test generated by {generator} on {now}
        """
        skill_name = '{skill_name}'
        intent = '{intent_name}'
        conversation = {conversation}
        simulation_result = self.conversation_text(skill_name, intent, conversation, verbose=verbose)
        self.assertSimulationResultIsCorrect(simulation_result, verbose=verbose)
    '''.format(**d)
        return s


def main(args):
    print('Generating test...')
    print(AlexaTestBuilder.create_test(*args))


if __name__ == '__main__':
    main(sys.argv[1:])
