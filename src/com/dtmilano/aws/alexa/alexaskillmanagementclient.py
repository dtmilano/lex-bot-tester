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

import json
import pathlib
import sys
import uuid
from datetime import datetime
from json import JSONDecodeError
from pprint import pprint
from time import sleep

import requests

from com.dtmilano.util.color import Color

DOT_ALEXA_SKILLS = '.alexa_skills'
HOME_DOT_ALEXA_SKILLS = str(pathlib.Path.home()) + '/' + DOT_ALEXA_SKILLS


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
        try:
            return self.__slot['name']
        except KeyError:
            return "<NO NAME>"

    def is_elicitation_required(self):
        return self.__slot['elicitationRequired']

    def get_prompts(self):
        return self.__slot['prompts']

    def get_elicitation(self):
        return self.__slot['prompts']['elicitation']

    def get_type(self):
        try:
            return self.__slot['type']
        except KeyError:
            return "<NO TYPE>"

    def is_confirmation_required(self):
        return self.__slot['confirmationRequired']

    def __str__(self):
        return 'Slot: {{name: {}, type: {}}}'.format(self.get_name(), self.get_type())


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

    def get_slots_by_intent(self, intent: str) -> [Slot]:
        if 'dialog' in self.__interaction_model['interactionModel']:
            for i in self.__interaction_model['interactionModel']['dialog']['intents']:
                if i['name'] == intent:
                    slots = []
                    for s in i['slots']:
                        slots.append(Slot(s))
                    return slots
        return None

    def get_slot_by_intent(self, slot, intent):
        for s in self.get_slots_by_intent(intent):
            if s.get_name() == slot:
                return s
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
        slots = self.get_slots_by_intent(intent)
        prompts = {}
        if slots:
            for s in slots:
                if s.is_elicitation_required():
                    e = s.get_elicitation()
                    v = self.get_prompt_variation_by_elicitation(e)
                    prompts[s.get_name()] = v
        return prompts

    def print(self):
        pprint(self.__interaction_model)
        if self.__interaction_model:
            print('dialog')
            intents = self.__interaction_model['interactionModel']['dialog']['intents']
            for i in intents:
                print(i['name'])
                for s in i['slots']:
                    print('\t{}: {} {}'.format(s['name'], s['type'], s['elicitationRequired']))
                    if 'prompts' in s:
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
    def __init__(self, simulation_result, debug=False):
        self.__simulation_result = simulation_result
        self.debug = debug

    def is_fulfilled(self):
        return self.__simulation_result['fulfilled']

    def get_slot_value(self, slot):
        try:
            return self.__simulation_result['slots'][slot]['value']
        except KeyError:
            raise RuntimeError('Cannot get slot value for {}: {}'.format(slot, self.__simulation_result['slots']))

    def get_slots(self):
        return self.__simulation_result['slots']

    # def get_response(self):
    #     return self.__simulation_result['response']

    def get_reprompt(self):
        return self.__simulation_result['reprompt']

    def get_output_speech(self):
        if self.debug:
            print('DEBUG: get_output_speech: simulation_result = {}'.format(self.__simulation_result))
        try:
            _type = self.__simulation_result['outputSpeechType']
            if _type is None:
                return None
            if _type == 'PlainText':
                return self.__simulation_result['outputSpeechText']
            elif _type == 'SSML':
                return self.__simulation_result['outputSpeechSsml']
            else:
                raise RuntimeError('Unknown type: {} for simulation_result: {}'.format(_type, self.__simulation_result))
        except KeyError:
            return None

    def __str__(self):
        return 'SimulationResult {{ {} }}'.format(self.__simulation_result)


class AlexaSkillManagementClient:
    ROOT = 'https://api.amazonalexa.com'

    def __init__(self, skill_name, locale='en-US'):
        self.__interaction_model_slots = None
        self.__conversation_status = None
        if not skill_name:
            raise ValueError('skill_name must be provided')
        self.__skill_id = AlexaSkillManagementClient.get_skill_id(skill_name, locale)
        if not self.__skill_id:
            raise ValueError('''cannot find skillId for {}
If you haven\'t created the file {} you can do it by running

   $ ask api list-skills >| {}

'''.format(skill_name, HOME_DOT_ALEXA_SKILLS, HOME_DOT_ALEXA_SKILLS))
        self.__skill_name = skill_name
        self.__locale = locale
        with open(str(pathlib.Path.home()) + '/.ask/cli_config') as f:
            cli_config = json.loads(f.read())
        expires_at = datetime.strptime(cli_config['profiles']['default']['token']['expires_at'],
                                       '%Y-%m-%dT%H:%M:%S.%fZ')
        if expires_at < datetime.utcnow():
            raise RuntimeError("""ASK access token is expired.
You can run 

    $ ask api list-skills >/dev/null
    
to refresh it.""")
        else:
            self.__access_token = cli_config['profiles']['default']['token']['access_token']

    def get_interaction_model(self) -> InteractionModel:
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

    def invocation(self, body_str, slot_values, verbose=False, debug=False):
        method = Request.Method.POST
        request = '/v0/skills/{skillId}/invocations'.format(skillId=self.__skill_id)
        body_str = body_str.format(skillId=self.__skill_id, sessionId='SessionId.{}'.format(uuid.uuid4()),
                                   requestId='EdwRequestId.{}'.format(uuid.uuid4()), userId="TestUser",
                                   timestamp=datetime.now().isoformat())
        # FIXME: original timestamp: "2018-01-08T06:27:33Z" (we have a slightly different format now)
        try:
            request_body = json.loads(body_str)
        except JSONDecodeError as ex:
            print('ERROR: Decoding\n{}\n'.format(body_str))
            raise ex
        r = self.__request(request, request_body, method, debug)
        if r and r['status'] == 'SUCCESSFUL':
            for s in slot_values:
                request_body['skillRequest']['body']['request']['timestamp'] = datetime.now().isoformat()
                request_body['skillRequest']['body']['request']['intent']['slots'][s]['value'] = slot_values[s]
                request_body['skillRequest']['body']['session']['new'] = False
                r = self.__request(request, request_body, method, debug)
                if r['status'] == Response.Status.SUCCESSFUL:
                    try:
                        if verbose:
                            print(r['result']['skillExecutionInfo']['invocationResponse'])
                        if r['result']['skillExecutionInfo']['invocationResponse']['body']['response'][
                                'shouldEndSession']:
                            return True
                    except KeyError:
                        try:
                            if debug:
                                print('r = {}'.format(r))
                            print('ERROR: {}'.format(r['result']['error']['message']), file=sys.stderr)
                        except KeyError:
                            print('no invocation response: r = {}'.format(r), file=sys.stderr)
                else:
                    print('ERROR: {}'.format(r), file=sys.stderr)
        else:
            print('ERROR: {}'.format('No response'), file=sys.stderr)
        return False

    def __get_simulation(self, simulation_id, debug=False):
        """
        Gets the simulation for the specified simulation_id.

        :rtype: SimulationResult
        :param simulation_id: the simulation id
        :param debug: enable debug
        :return: the {SimulationResult}
        """
        method = Request.Method.GET
        request = '/v0/skills/{skillId}/simulations/{simulationId}'.format(skillId=self.__skill_id,
                                                                           simulationId=simulation_id)
        sleep(1)
        attempt = 7
        r = None
        while attempt > 0:
            r = self.__request(request, None, method, debug)
            if r['status'] == Response.Status.SUCCESSFUL:
                break
            if r['status'] == Response.Status.FAILED:
                raise RuntimeError('ERROR: attempt={} response={}'.format(7 - attempt, r))
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
            if debug:
                print('DEBUG: finding outputSpeech in {}'.format(r))
                print('DEBUG: finding outputSpeech in {}'.format(
                    r['result']['skillExecutionInfo']['invocationResponse']['body']['response']['outputSpeech']))
            output_speech = r['result']['skillExecutionInfo']['invocationResponse']['body']['response']['outputSpeech']
            output_speech_type = output_speech['type']
            if output_speech_type == 'PlainText':
                output_speech_text = output_speech['text']
                output_speech_ssml = None
            elif output_speech_type == 'SSML':
                output_speech_ssml = output_speech['ssml']
                output_speech_text = None
            else:
                raise RuntimeError('Unknown output speech type: {}'.format(output_speech_type))
        except KeyError:
            output_speech_ssml = None
            output_speech_text = None
            output_speech_type = None
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
                elicitation_required = None
                if self.__interaction_model_slots:
                    for _s in self.__interaction_model_slots:
                        if _s.get_name() == s:
                            elicitation_required = _s.is_elicitation_required()
                    if elicitation_required and ('value' not in slots[s] or not slots[s]['value']):
                        fulfilled = False
                        break
        except KeyError:
            fulfilled = None
            slots = None
        return SimulationResult({'directives': directives, 'shouldEndSession': should_end_session,
                                 'outputSpeechSsml': output_speech_ssml, 'outputSpeechText': output_speech_text,
                                 'outputSpeechType': output_speech_type,
                                 'reprompt': reprompt,
                                 'fulfilled': fulfilled, 'slots': slots})

    def simulation(self, text: str, verbose: bool, debug: bool = False) -> SimulationResult:
        """
        Starts a simulation sending the specified text.

        :rtype: SimulationResult
        :param verbose: verbose output
        :param text: the text to send
        :param debug: enable debug
        :return: the {SimulationResult}
        """
        method = Request.Method.POST
        request = '/v0/skills/{skillId}/simulations'.format(skillId=self.__skill_id)
        if text:
            text = text.lower()
        body = {'input': {'content': text}, 'device': {'locale': self.__locale}}
        if verbose:
            print(Color.colorize('>> saying: {}'.format(text), Color.BRIGHT_BLUE))
        r = self.__request(request, body, method, debug)
        if r:
            if r['status'] == Response.Status.IN_PROGRESS:
                simulation_id = r['id']
                return self.__get_simulation(simulation_id, debug)
            elif r['status'] == Response.Status.FAILED:
                raise RuntimeError('ERROR: FAILED response: {}'.format(r))
        else:
            raise RuntimeError('ERROR: No response')

    def conversation_step(self, step: {}, verbose: bool, debug: bool = False) -> SimulationResult:
        """
        Moves the conversation one step.

        :param verbose:
        :param step: the step, a dictionary containing slot, prompt and text
        :param debug: show debug messages
        :return: the {SimulationResult}
        """
        if self.__conversation_status != 'STARTED':
            raise RuntimeError('Conversation has not been started')
        forgive = False
        slot = step['slot']
        prompt = step['prompt']
        text = step['text']
        simulation_result = None

        # while forgive and not simulation_result:
        while not simulation_result:
            try:
                if verbose:
                    print('\n')
                if verbose and prompt:
                    print(prompt)
                simulation_result = self.simulation(text, verbose, debug)
                if verbose and simulation_result:
                    if simulation_result.get_output_speech():
                        print(Color.colorize('<< {}'.format(simulation_result.get_output_speech()), Color.BRIGHT_WHITE,
                                             Color.BLACK))
                    else:
                        if debug:
                            print('DEBUG: sr = {}'.format(simulation_result))
                    if slot:
                        print(Color.colorize('<< {}'.format(simulation_result.get_slot_value(slot)), Color.BRIGHT_WHITE,
                                             Color.BRIGHT_BLACK))
                if verbose:
                    print()
            except RuntimeError as ex:
                if forgive:
                    forgive = False
                else:
                    raise ex
        return simulation_result

    def __request(self, request, body=None, method=Request.Method.GET, debug=False):
        headers = {'Authorization': self.__access_token,
                   'content-Type': 'application/json',
                   'accept': 'application/json',
                   'User-Agent': 'ask-cli/1.0.0-beta.8 Node/v9.2.0'}
        if debug:
            print('DEBUG: __request: headers = {}'.format(headers))
            print('DEBUG: __request: {} {}'.format(method, self.ROOT + request))
        if method == Request.Method.GET:
            r = requests.get(self.ROOT + request, headers=headers)
            if r.status_code != 200:
                print(r, file=sys.stderr)
                print(json.loads(r.text)['message'], file=sys.stderr)
                raise RuntimeError('{}: {}'.format(r, r.json()['message']))
        elif method == Request.Method.POST:
            r = requests.post(self.ROOT + request, headers=headers, data=json.dumps(body))
            if debug:
                print('DEBUG: __request: body = {}'.format(body))
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
        try:
            with open(HOME_DOT_ALEXA_SKILLS) as f:
                alexa_skills = json.loads(f.read())['skills']
        except IOError:
            print(
                'ERROR: Cannot open ~/{}.\n'.format(DOT_ALEXA_SKILLS) +
                'You can generate it with the command: \'ask api list-skills > ~/{}\''.format(DOT_ALEXA_SKILLS),
                file=sys.stderr)
            sys.exit(1)
        for s in alexa_skills:
            if debug:
                print('DEBUG: s={}'.format(s))
            if s['nameByLocale'][locale] == skill_name:
                return s['skillId']
        return None

    def conversation_start(self, intent_name: str, conversation: [], verbose: bool, debug=False) -> None:
        if verbose:
            print('\n')
            print("Start conversation")
            print("------------------")
        interaction_model = self.get_interaction_model()
        prompts = interaction_model.get_prompts_by_intent(intent_name)
        self.__interaction_model_slots = interaction_model.get_slots_by_intent(intent_name)
        for c in conversation:
            if c['slot']:
                try:
                    c['prompt'] = prompts[c['slot']]
                except KeyError:
                    self.__invalid_slot(c['slot'], intent_name)
            else:
                c['prompt'] = None
        if debug:
            if self.__interaction_model_slots:
                for s in self.__interaction_model_slots:
                    print('DEBUG: slots_by_intent = {}'.format(s))
            else:
                print('DEBUG: no slots')
        self.__conversation_status = 'STARTED'

    def __invalid_slot(self, slot, intent_name):
        if self.__interaction_model_slots:
            slot_names = [s.get_name() for s in self.__interaction_model_slots]
            raise ValueError(
                'intent \'{}\' of skill \'{}\' does not define a slot named \'{}\'. Valid slots are {}'.format(
                    intent_name, self.__skill_name,
                    slot,
                    slot_names))
        else:
            raise ValueError('intent \'{}\' of skill \'{}\' does not define any slots.'.format(intent_name,
                                                                                               self.__skill_name))

    def conversation_end(self) -> None:
        self.__conversation_status = None


def main():
    bmts = AlexaSkillManagementClient('BookMyTripSkill')
    if not bmts:
        raise RuntimeError('Cannot find skill_name {} definition in ~/{}'.format('BookMyTripSkill', DOT_ALEXA_SKILLS))

    hlg = AlexaSkillManagementClient('High Low Game')
    if not hlg:
        raise RuntimeError('Cannot find skill_name {} definition in ~/{}'.format('High Low Game', DOT_ALEXA_SKILLS))

    # simulation_result = None
    print('\nskill info')
    bmts.get_skill_info()
    hlg.get_skill_info()
    # print('\netag')
    # bmts.get_interaction_model_etag()
    # print('\nmodel')
    # bmts.print_interation_model(bmts.obtain_interaction_model())
    print('\ninvocation')
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
    }}"""
    slot_values = {'CarType': 'luxury', 'PickUpCity': 'san francisco', 'PickUpDate': 'tomorrow',
                   'ReturnDate': 'next week', 'DriverAge': 25}
    print('returns {}'.format(bmts.invocation(body_str, slot_values)))
    # print('\nsimulation')
    # bmts.simulation(conversation[skill_name][0], debug=False)
    # print('\nconversation')
    # high_low_game(hlg, debug=False)
    # print('\nconversation')
    # reserve_a_car(bmts, debug=False)
    # bmts.simulation('start book my trip', debug=True)
    # # bmts.simulation('verdura', debug=True)


if __name__ == '__main__':
    main()
