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

DEBUG = False


def to_snake_case(name):
    if DEBUG:
        print('>>>>>>> to_snake_case({}) {}'.format(name, type(name)))
    if type(name) == bytes:
        name = name.decode()
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def to_camel_case(name):
    if type(name) == bytes:
        name = name.decode()
    components = name.split('_')
    return "".join(x.title() for x in components)


def number_to_words(n):
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
