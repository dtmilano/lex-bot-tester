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

    def get_skill_info(self):
        method = Request.Method.GET
        request = '/v0/skills/{}'.format(self.__skill_id)
        print(self.__request(request, method=method))

    def get_interaction_model(self):
        # GET /v0/skills/{skillId}/interactionModel/locales/{locale}
        method = Request.Method.GET
        request = '/v0/skills/{skillId}/interactionModel/locales/{locale}'.format(skillId=self.__skill_id,
                                                                                  locale=self.__locale)
        r = self.__request(request, method=method, debug=False)
        pprint(r)
        if r:
            print('dialog')
            intents = r['interactionModel']['dialog']['intents']
            for i in intents:
                print(i['name'])
                for s in i['slots']:
                    print('\t{}: {} {}'.format(s['name'], s['type'], s['elicitationRequired']))
                    for p in s['prompts'].keys():
                        v = s['prompts'][p]
                        for p2 in r['interactionModel']['prompts']:
                            if p2['id'] == v:
                                for v2 in p2['variations']:
                                    if v2['type'] == 'PlainText':
                                        print('\t\t{}'.format(v2['value']))
            print()
            print('languageModel')
            intents = r['interactionModel']['languageModel']['intents']
            for i in intents:
                print(i['name'])
        else:
            print('ERROR', file=sys.stderr)

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
        method = Request.Method.GET
        request = '/v0/skills/{skillId}/simulations/{simulationId}'.format(skillId=self.__skill_id,
                                                                           simulationId=simulation_id)
        sleep(1)
        attempt = 5
        while attempt > 0:
            r = self.__request(request, None, method, debug)
            if r['status'] == Response.Status.SUCCESSFUL:
                break
            if r['status'] == Response.Status.FAILED:
                print('ERROR: {}'.format(r), file=sys.stderr)
                return
            if r['status'] == Response.Status.IN_PROGRESS:
                attempt -= 1
                sleep(1)

        if attempt == 0:
            raise RuntimeError('Could not get simulation with id={}'.format(simulation_id))
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
        return {'response': response, 'reprompt': reprompt}

    def simulation(self, text, debug=False):
        method = Request.Method.POST
        request = '/v0/skills/{skillId}/simulations'.format(skillId=self.__skill_id)
        body = {'input': {'content': text}, 'device': {'locale': self.__locale}}
        print('>>> saying: {}'.format(text))
        r = self.__request(request, body, method, debug)
        if r['status'] == Response.Status.IN_PROGRESS:
            simulation_id = r['id']
            return self.__get_simulation(simulation_id, debug)
        else:
            raise RuntimeError('{}'.format(r))

    def conversation(self, conversation, debug=False):
        if not isinstance(conversation, list):
            raise ValueError('conversation should be a list of strings')
        rere = None
        lowest = 1
        highest = 100
        for text in conversation:
            if text == '$random':
                text = self.n2w(random.randint(1, 100))
            elif text == '$guess':
                if rere:
                    print('searching "{}" for number and condition'.format(rere['response']))
                    m = re.search('.*?(\d+) is correct.*', rere['response'])
                    if m:
                        print('***** {} is correct !!! *****'.format(m.group(1)))
                        break
                    m = re.search('.*?(\d+) is too (\w+).*', rere['response'])
                    if m:
                        n = int(m.group(1))
                        w = m.group(2)
                        if w == 'high':
                            highest = n
                            randint = random.randint(lowest, highest)
                            text = self.n2w(randint)
                            print('{} is top high, will try {} ({}) in [{}..{}]'.format(n, randint, text, lowest,
                                                                                        highest))
                        else:
                            lowest = n
                            randint = random.randint(lowest + 1, highest)
                            text = self.n2w(randint)
                            print(
                                '{} is top low, will try {} ({}) in [{}..{}]'.format(n, randint, text, lowest, highest))
                    else:
                        raise RuntimeError('rere = {}'.format(rere))
                else:
                    text = self.n2w(random.randint(1, 100))
            rere = self.simulation(text, debug)
            print(re.sub('<.*?speak>', '', rere['response']))
            print(re.sub('<.*?speak>', '', rere['reprompt']))

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
    def get_skill_id(skill_name, locale='en-US'):
        alexa_skills = json.loads(open(str(pathlib.Path.home()) + '/.alexa_skills').read())['skills']
        for s in alexa_skills:
            print('s={}'.format(s))
            if s['nameByLocale'][locale] == skill_name:
                return s['skillId']
        return None

    @staticmethod
    def n2w(n):
        """
        Converts the number to words.
        Supported range is [0..99].

        :param n: the number
        :return: the words representing the number (i.e. forty one)

        :see https://stackoverflow.com/questions/19504350/how-to-convert-numbers-to-words-in-python
        """
        num2words = {1: 'One', 2: 'Two', 3: 'Three', 4: 'Four', 5: 'Five',
                     6: 'Six', 7: 'Seven', 8: 'Eight', 9: 'Nine', 10: 'Ten',
                     11: 'Eleven', 12: 'Twelve', 13: 'Thirteen', 14: 'Fourteen',
                     15: 'Fifteen', 16: 'Sixteen', 17: 'Seventeen', 18: 'Eighteen',
                     19: 'Nineteen', 20: 'Twenty', 30: 'Thirty', 40: 'Forty',
                     50: 'Fifty', 60: 'Sixty', 70: 'Seventy', 80: 'Eighty',
                     90: 'Ninety', 0: 'Zero'}
        try:
            return num2words[n].lower()
        except KeyError:
            try:
                return num2words[n - n % 10].lower() + ' ' + num2words[n % 10].lower()
            except KeyError:
                raise ValueError('Number out of range. Valid range [0..99]')


def main():
    # skill_name = 'Aristo'
    # skill_name = 'BookMyTripSkill'
    skill_name = 'High Low Game'
    conversation = {'BookMyTripSkill': 'ask book my trip to reserve a car',
                    'High Low Game': ['start high low game', 'yes', 'twenty four', '$random',
                                      '$guess', '$guess', '$guess', '$guess', '$guess', '$guess', '$guess',
                                      '$guess', '$guess', '$guess', '$guess']}
    asmc = AlexaSkillManagementClient(skill_name)
    if not asmc:
        raise RuntimeError('Cannot find skill_name {} definition in ~/.alexa_skills'.format(skill_name))
    # print('\nskill_name inf')
    # asmc.get_skill_info()
    # print('\netag')
    # asmc.get_interaction_model_etag()
    # print('\nmodel')
    # asmc.get_interaction_model()
    # print('\ninvocation')
    # asmc.invocation()
    # print('\nsimulation')
    # asmc.simulation(conversation[skill_name][0], debug=False)
    print('\nconversation')
    asmc.conversation(conversation[skill_name], debug=False)
    # asmc.simulation('start book my trip', debug=True)
    # # asmc.simulation('verdura', debug=True)


if __name__ == '__main__':
    main()
