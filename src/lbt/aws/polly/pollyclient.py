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

import boto3


class PollyClient:
    """
    Polly Client.
    """

    def __init__(self):
        self.__client = boto3.client('polly')
        self.output_format = 'pcm'
        self.voice_id = 'Nicole'

    def synthesize_speech(self, text):
        return self.__client.synthesize_speech(Text=text, OutputFormat=self.output_format, VoiceId=self.voice_id)
