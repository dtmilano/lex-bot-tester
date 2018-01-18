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
import json
import pathlib
import random
import re
import sys
import uuid
from datetime import datetime
from json import JSONDecodeError
from pprint import pprint
from time import sleep

import requests

from com.dtmilano.util.conversion import number_to_words


class Request:
    class Method:
        HEAD = 'head'
        GET = 'get'
        POST = 'post'


class Response:
    class Status:
        IN_PROGRESS = 'IN_PROGRESS'
        SUCCESSFUL = 'SUCCESSFUL'
        FAILED = 'FAILED'


class Slot:
    def __init__(self, slot):
        self.__slot = slot

    def get_name(self):
        return self.__slot['name']

    def is_elicitation_required(self):
        return self.__slot['elicitationRequired']

    def get_prompts(self):
        return self.__slot['prompts']

    def get_elicitation(self):
        return self.__slot['prompts']['elicitation']

    def get_type(self):
        return self.__slot['type']

    def is_confirmation_required(self):
        return self.__slot['confirmationRequired']


class Prompt:
    def __init__(self, prompt):
        self.__prompt = prompt

    def get_id(self):
        return self.__prompt['id']

    def get_variations(self):
        return self.__prompt['variations']

    def get_variation(self, __type='PlainText'):
        for v in self.get_variations():
            if v['type'] == __type:
                return v['value']
        return None


class InteractionModel:
    def __init__(self, asmc):
        self.__interaction_model = asmc.obtain_interaction_model()

    def get_slots_for_intent(self, intent):
        for i in self.__interaction_model['interactionModel']['dialog']['intents']:
            if i['name'] == intent:
                slots = []
                for s in i['slots']:
                    slots.append(Slot(s))
                # return i['slots']
                return slots
        return None

    def get_prompts(self):
        prompts = []
        for p in self.__interaction_model['interactionModel']['prompts']:
            prompts.append(Prompt(p))
        return prompts

    def get_prompt_variation_by_elicitation(self, elicitation, __type='PlainText'):
        for p in self.get_prompts():
            if p.get_id() == elicitation:
                v = p.get_variation('PlainText')
                if v:
                    return v
                else:
                    print("No prompt variations of type '{}'".format(__type), file=sys.stderr)
        return None

    def get_prompts_by_intent(self, intent):
        slots = self.get_slots_for_intent(intent)
        prompts = {}
        for s in slots:
            if s.is_elicitation_required():
                e = s.get_elicitation()
                v = self.get_prompt_variation_by_elicitation(e)
                prompts[s.get_name()] = v
        return prompts

    def print_interaction_model(self):
        pprint(self.__interaction_model)
        if self.__interaction_model:
            print('dialog')
            intents = self.__interaction_model['interactionModel']['dialog']['intents']
            for i in intents:
                print(i['name'])
                for s in i['slots']:
                    print('\t{}: {} {}'.format(s['name'], s['type'], s['elicitationRequired']))
                    for p in s['prompts'].keys():
                        v = s['prompts'][p]
                        for p2 in self.__interaction_model['interactionModel']['prompts']:
                            if p2['id'] == v:
                                for v2 in p2['variations']:
                                    if v2['type'] == 'PlainText':
                                        print('\t\t{}'.format(v2['value']))
            print()
            print('languageModel')
            intents = self.__interaction_model['interactionModel']['languageModel']['intents']
            for i in intents:
                print(i['name'])
        else:
            print('ERROR', file=sys.stderr)


class SimulationResult(object):
    def __init__(self, simulation_result):
        self.__simulation_result = simulation_result

    def is_fulfilled(self):
        return self.__simulation_result['fulfilled']

    def get_slot_value(self, slot):
        return self.__simulation_result['slots'][slot]['value']

    def get_slots(self):
        return self.__simulation_result['slots']

    def get_response(self):
        return self.__simulation_result['response']

    def get_reprompt(self):
        return self.__simulation_result['reprompt']


class AlexaSkillManagementClient:
    ROOT = 'https://api.amazonalexa.com/'

    def __init__(self, skill_name, locale='en-US'):
        if not skill_name:
            raise ValueError('skill_name must be provided')
        self.__skill_id = AlexaSkillManagementClient.get_skill_id(skill_name, locale)
        if not self.__skill_id:
            raise ValueError('cannot find skillId for {}'.format(skill_name))
        self.__locale = locale
        cli_config = json.loads(open(str(pathlib.Path.home()) + '/.ask/cli_config').read())
        expires_at = datetime.strptime(cli_config['profiles']['default']['token']['expires_at'],
                                       '%Y-%m-%dT%H:%M:%S.%fZ')
        if expires_at < datetime.utcnow():
            raise RuntimeError('ASK access token is expired.')
        else:
            self.__access_token = cli_config['profiles']['default']['token']['access_token']

    def get_interaction_model(self):
        return InteractionModel(self)

    def get_skill_info(self):
        method = Request.Method.GET
        request = '/v0/skills/{}'.format(self.__skill_id)
        print(self.__request(request, method=method))

    def obtain_interaction_model(self):
        # GET /v0/skills/{skillId}/interactionModel/locales/{locale}
        method = Request.Method.GET
        request = '/v0/skills/{skillId}/interactionModel/locales/{locale}'.format(skillId=self.__skill_id,
                                                                                  locale=self.__locale)
        r = self.__request(request, method=method, debug=False)
        return r

    def get_interaction_model_etag(self):
        # HEAD /v0/skills/{skillId}/interactionModel/locales/{locale}
        method = Request.Method.HEAD
        request = '/v0/skills/{skillId}/interactionModel/locales/{locale}'.format(skillId=self.__skill_id,
                                                                                  locale=self.__locale)
        r = self.__request(request, method=method, debug=False)
        print(r)

    def invocation(self, debug=False):
        method = Request.Method.POST
        request = '/v0/skills/{skillId}/invocations'.format(skillId=self.__skill_id)
        body_str = """{{
            "endpointRegion": "NA",
            "skillRequest": {{
                "body": {{
                    "context": {{
                        "AudioPlayer": {{
                            "playerActivity": "IDLE"
                        }},
                        "System": {{
                            "application": {{
                                "applicationId": "{skillId}"
                            }},
                            "device": {{
                                "supportedInterfaces": {{}}
                            }},
                            "user": {{
                                "userId": "{userId}"
                            }}
                        }}
                    }},
                    "request": {{
                        "intent": {{
                            "name": "BookCar",
                            "slots": {{
                                "CarType": {{
                                    "name": "CarType"
                                }},
                                "DriverAge": {{
                                    "name": "DriverAge"
                                }},
                                "PickUpCity": {{
                                    "name": "PickUpCity"
                                }},
                                "PickUpDate": {{
                                    "name": "PickUpDate"
                                }},
                                "ReturnDate": {{
                                    "name": "ReturnDate"
                                }}
                            }}
                        }},
                        "locale": "en-US",
                        "requestId": "{requestId}",
                        "timestamp": "{timestamp}",
                        "type": "IntentRequest"
                    }},
                    "session": {{
                        "application": {{
                            "applicationId": "{skillId}"
                        }},
                        "attributes": {{}},
                        "new": true,
                        "sessionId": "{sessionId}",
                        "user": {{
                            "userId": "{userId}"
                        }}
                    }},
                    "version": "1.0"
                }}
            }}
        }}""".format(skillId=self.__skill_id, sessionId='SessionId.{}'.format(uuid.uuid4()),
                     requestId='EdwRequestId.{}'.format(uuid.uuid4()), userId="TestUser",
                     timestamp=datetime.now().isoformat())
        # FIXME: original timestamp: "2018-01-08T06:27:33Z" (we have a slightly different format now)
        request_body = json.loads(body_str)
        r = self.__request(request, request_body, method, debug)
        slot_values = {'CarType': 'luxury', 'PickUpCity': 'san francisco', 'PickUpDate': 'tomorrow',
                       'ReturnDate': 'next week', 'DriverAge': 25}
        if r['status'] == 'SUCCESSFUL':
            for s in slot_values:
                request_body['skillRequest']['body']['request']['timestamp'] = datetime.now().isoformat()
                request_body['skillRequest']['body']['request']['intent']['slots'][s]['value'] = slot_values[s]
                request_body['skillRequest']['body']['session']['new'] = False
                r = self.__request(request, request_body, method, debug)
                if r['status'] == Response.Status.SUCCESSFUL:
                    try:
                        print(r['result']['skillExecutionInfo']['invocationResponse'])
                        if r['result']['skillExecutionInfo']['invocationResponse']['body']['response'][
                            'shouldEndSession']:
                            break
                    except KeyError:
                        try:
                            print('r = {}'.format(r))
                            print('ERROR: {}'.format(r['result']['error']['message']), file=sys.stderr)
                        except KeyError:
                            print('no invocation response: r = {}'.format(r), file=sys.stderr)
                else:
                    print('ERROR: {}'.format(r), file=sys.stderr)

    def __get_simulation(self, simulation_id, debug=False):
        """
        Gets the simulation for the specified simulation_id.

        :param simulation_id: the simulation id
        :param debug: enable debug
        :return: the {SimulationResult}
        """
        method = Request.Method.GET
        request = '/v0/skills/{skillId}/simulations/{simulationId}'.format(skillId=self.__skill_id,
                                                                           simulationId=simulation_id)
        sleep(1)
        attempt = 7
        while attempt > 0:
            r = self.__request(request, None, method, debug)
            if r['status'] == Response.Status.SUCCESSFUL:
                break
            if r['status'] == Response.Status.FAILED:
                raise RuntimeError('ERROR: {}'.format(r))
            if r['status'] == Response.Status.IN_PROGRESS:
                attempt -= 1
                sleep(1)

        if attempt == 0:
            raise RuntimeError('Could not get simulation with id={}'.format(simulation_id))
        try:
            directives = r['result']['skillExecutionInfo']['invocationResponse']['body']['response']['directives'][
                0]['type']
        except KeyError:
            directives = None
        except IndexError:
            directives = None
        try:
            should_end_session = r['result']['skillExecutionInfo']['invocationResponse']['body']['response'][
                'shouldEndSession']
        except KeyError:
            should_end_session = None
        try:
            response = r['result']['skillExecutionInfo']['invocationResponse']['body']['response']['outputSpeech'][
                'ssml']
        except KeyError:
            response = None
        try:
            reprompt = \
                r['result']['skillExecutionInfo']['invocationResponse']['body']['response']['reprompt']['outputSpeech'][
                    'ssml']
        except KeyError:
            reprompt = None
        try:
            fulfilled = True
            slots = r['result']['skillExecutionInfo']['invocationRequest']['body']['request']['intent']['slots']
            for s in slots:
                if not ('value' in slots[s] and slots[s]['value']):
                    fulfilled = False
                    break
        except KeyError:
            fulfilled = None
            slots = None

        return SimulationResult({'directives': directives, 'shouldEndSession': should_end_session, 'response': response,
                                 'reprompt': reprompt,
                                 'fulfilled': fulfilled, 'slots': slots})

    def simulation(self, text, debug=False):
        """
        Starts a simulation sending the specified text.

        :param text: the text to send
        :param debug: enable debug
        :return: the {SimulationResult}
        """
        method = Request.Method.POST
        request = '/v0/skills/{skillId}/simulations'.format(skillId=self.__skill_id)
        body = {'input': {'content': text}, 'device': {'locale': self.__locale}}
        print('\x1b[35m>>> saying: {}\x1b[0m'.format(text))
        r = self.__request(request, body, method, debug)
        if r['status'] == Response.Status.IN_PROGRESS:
            simulation_id = r['id']
            return self.__get_simulation(simulation_id, debug)
        else:
            raise RuntimeError('ERROR: {}'.format(r))

    def conversation_step(self, step, debug):
        """
        Moves the conversation one step.

        :param step: the step, a dictionary containing slot, prompt and text
        :param debug: show debug messages
        :return: the {SimulationResult}
        """
        forgive = True
        slot = step['slot']
        prompt = step['prompt']
        text = step['text']
        simulation_result = None

        while forgive and not simulation_result:
            try:
                print('\n')
                if prompt:
                    print(prompt)
                simulation_result = self.simulation(text, debug)
                if simulation_result and slot:
                    print('\x1b[36m{}\x1b[0m'.format(simulation_result.get_slot_value(slot)))
                print()
            except RuntimeError as ex:
                if forgive:
                    forgive = False
                else:
                    raise ex
        return simulation_result

    def __request(self, request, body=None, method=Request.Method.GET, debug=False):
        headers = {'Authorization': self.__access_token,
                   'Content-Type': 'application/json',
                   'Accept': 'application/json'}
        if method == Request.Method.GET:
            r = requests.get(self.ROOT + request, headers=headers)
            if r.status_code != 200:
                print(r, file=sys.stderr)
                print(json.loads(r.text)['message'], file=sys.stderr)
                raise RuntimeError('{}: {}'.format(r, r.json()['message']))
        elif method == Request.Method.POST:
            r = requests.post(self.ROOT + request, headers=headers, data=json.dumps(body))
            if r.status_code != 200:
                print(r, file=sys.stderr)
                try:
                    print(r, file=sys.stderr)
                    print(r.json()['message'], file=sys.stderr)
                except JSONDecodeError as ex:
                    print('ERROR', file=sys.stderr)
                return None
        elif method == Request.Method.HEAD:
            r = requests.head(self.ROOT + request, headers=headers)
            if r.status_code != 200:
                print(r, file=sys.stderr)
                print(json.loads(r.text)['message'], file=sys.stderr)
                raise RuntimeError('{}: {}'.format(r, r.json()['message']))
            else:
                return r.headers
        else:
            raise RuntimeError('Unsupported method {}'.format(method))
        if debug:
            print('DEBUG: {} {} {}'.format(r.status_code, r.headers, r.text))
            print('DEBUG: ' + json.dumps(r.json(), indent=4, sort_keys=True))
        return r.json()

    @staticmethod
    def get_skill_id(skill_name, locale='en-US', debug=False):
        alexa_skills = json.loads(open(str(pathlib.Path.home()) + '/.alexa_skills').read())['skills']
        for s in alexa_skills:
            if debug:
                print('DEBUG: s={}'.format(s))
            if s['nameByLocale'][locale] == skill_name:
                return s['skillId']
        return None


def high_low_game(alexa_skill_management_client, debug=False):
    # if not isinstance(conversation, list):
    #     raise ValueError('conversation should be a list of strings')
    conversation = ['start high low game', 'yes', 'twenty four', '$random',
                    '$guess', '$guess', '$guess', '$guess', '$guess', '$guess', '$guess',
                    '$guess', '$guess', '$guess', '$guess']
    simulation_result = None
    lowest = 1
    highest = 100
    for text in conversation:
        if text == '$random':
            text = number_to_words(random.randint(1, 100))
        elif text == '$guess':
            if simulation_result:
                print('searching "{}" for number and condition'.format(simulation_result.get_response()))
                m = re.search('.*?(\d+) is correct.*', simulation_result.get_response())
                if m:
                    print('***** {} is correct !!! *****'.format(m.group(1)))
                    break
                m = re.search('.*?(\d+) is too (\w+).*', simulation_result.get_response())
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
                    raise RuntimeError('simulation_result = {}'.format(simulation_result))
            else:
                text = number_to_words(random.randint(1, 100))
        simulation_result = alexa_skill_management_client.simulation(text, debug)
        print(re.sub('<.*?speak>', '', simulation_result.get_response()))
        print(re.sub('<.*?speak>', '', simulation_result.get_reprompt()))


def reserve_a_car(alexa_skill_management_client, debug=False):
    intent = 'BookCar'
    interaction_model = alexa_skill_management_client.get_interaction_model()
    prompts = interaction_model.get_prompts_by_intent(intent)
    conversation = [
        {'slot': None, 'prompt': None, 'text': 'ask book my trip to reserve a car'},
        {'slot': 'CarType', 'prompt': prompts['CarType'], 'text': 'midsize'},
        {'slot': 'PickUpCity', 'prompt': prompts['PickUpCity'], 'text': 'buenos aires'},
        {'slot': 'PickUpDate', 'prompt': prompts['PickUpDate'], 'text': 'tomorrow'},
        {'slot': 'ReturnDate', 'prompt': prompts['ReturnDate'], 'text': 'five days from now'},
        {'slot': 'DriverAge', 'prompt': prompts['DriverAge'], 'text': 'twenty five'},
        {'slot': None, 'prompt': 'Confirmation', 'text': 'yes'}
    ]

    simulation_result = None
    fulfilled = False
    for c in conversation:
        simulation_result = alexa_skill_management_client.conversation_step(c, debug)
        fulfilled = fulfilled or (simulation_result.is_fulfilled() if simulation_result else False)
        sleep(1)
    if not fulfilled:
        print('ERROR: some slots have no values:\n{}\n'.format(
            simulation_result.get_slots() if simulation_result else 'no slots available'), file=sys.stderr)


def main():
    bmts = AlexaSkillManagementClient('BookMyTripSkill')
    if not bmts:
        raise RuntimeError('Cannot find skill_name {} definition in ~/.alexa_skills'.format('BookMyTripSkill'))

    hlg = AlexaSkillManagementClient('High Low Game')
    if not hlg:
        raise RuntimeError('Cannot find skill_name {} definition in ~/.alexa_skills'.format('High Low Game'))

    # simulation_result = None
    # print('\nskill_name inf')
    # bmts.get_skill_info()
    # print('\netag')
    # bmts.get_interaction_model_etag()
    # print('\nmodel')
    # bmts.print_interation_model(bmts.obtain_interaction_model())
    # print('\ninvocation')
    # bmts.invocation()
    # print('\nsimulation')
    # bmts.simulation(conversation[skill_name][0], debug=False)
    print('\nconversation')
    high_low_game(hlg, debug=False)
    print('\nconversation')
    reserve_a_car(bmts, debug=False)
    # bmts.simulation('start book my trip', debug=True)
    # # bmts.simulation('verdura', debug=True)


if __name__ == '__main__':
    main()
