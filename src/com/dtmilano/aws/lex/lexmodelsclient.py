import boto3

from com.dtmilano.aws.lex.resultbase import ResultBase
from com.dtmilano.util.conversion import to_snake_case


def class_factory(name, arg_names, base_class=ResultBase):
    """
    Class factory.

    Credit: https://stackoverflow.com/questions/15247075/how-can-i-dynamically-create-derived-classes-from-a-base-class

    :param name: the class name
    :param arg_names: the name of the arguments accepted by newly created class
    :param base_class: the base class
    :return: the newly created class
    """

    def __init__(self, dialog_state, **kwargs):
        for key, value in kwargs.items():
            # here, the arg_names variable is the one passed to the class_factory() call
            if key not in arg_names:
                raise TypeError(
                    "Argument {} not valid for {}. Should be one of {}".format(key, self.__class__.__name__, arg_names))
            setattr(self, key, value)
        base_class.__init__(self, name[:-len("Class")], name[:-len('Result')], dialog_state, **kwargs)

    new_class = type(name, (base_class,), {"__init__": __init__})
    return new_class


class LexModelsClient:
    """
    AWS Lex Models Client.
    """

    def __init__(self, bot_name=None, bot_alias=None):
        self.__client = boto3.client('lex-models')
        self.__result_classes = {}
        if bot_name is not None and bot_alias is not None:
            # If bot_name and bot_alias were given to the constructor we can create the result classes
            self.__bot_name = bot_name
            self.__bot_alias = bot_alias
            self.create_result_classes(bot_name, bot_alias)
        elif bot_name is not None or bot_alias is not None:
            raise RuntimeError('bot_name and bot_alias should be != None')

    def get_bots(self):
        return self.__client.get_bots()['bots']

    def get_intent(self, name, version='$LATEST'):
        return self.__client.get_intent(name=name, version=version)

    def get_intents(self):
        return self.__client.get_intents()['intents']

    def get_intents_for_bot(self, bot_name=None, bot_alias=None):
        if bot_name is None:
            bot_name = self.__bot_name
        if bot_alias is None:
            bot_alias = self.__bot_alias
        b = self.__client.get_bot(name=bot_name, versionOrAlias=bot_alias)
        intents = b['intents']
        li = []
        for i in intents:
            li.append(i['intentName'])
        return li

    def create_result_classes(self, bot_name, bot_alias):
        intent_names = self.get_intents_for_bot(bot_name, bot_alias)
        for ina in intent_names:
            intent = self.get_intent(ina)
            result_name = intent['name'].encode('ascii', 'ignore') + 'Result'
            slots = intent['slots']
            slot_names = [to_snake_case(s['name'].encode('ascii', 'ignore')) for s in slots]
            if bot_name not in self.__result_classes:
                self.__result_classes[bot_name] = {}
            self.__result_classes[bot_name][result_name] = class_factory(result_name, slot_names)

    def get_result_class_name(self, intent_name):
        intent = self.get_intent(intent_name)
        return intent['name'].encode('ascii', 'ignore') + 'Result'

    def get_results(self, bot_name):
        return self.__result_classes[bot_name]

    def get_result_class_for_intent(self, intent_name, bot_name=None):
        return self.get_result_class_for_bot(self.get_result_class_name(intent_name), bot_name)

    def get_result_class_for_bot(self, result_name, bot_name=None):
        if bot_name is None:
            bot_name = self.__bot_name
        return self.get_result_class(bot_name, result_name)

    def get_result_class(self, bot_name, result_name):
        return self.__result_classes[bot_name][result_name]
