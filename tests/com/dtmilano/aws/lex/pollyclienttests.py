import unittest

from com.dtmilano.aws.lex.pollyclient import PollyClient


class PollyClientTests(unittest.TestCase):

    def tearDown(self):
        super(PollyClientTests, self).tearDown()

    def setUp(self):
        super(PollyClientTests, self).setUp()
        self.pc = PollyClient()

    def test_synthesize_speech(self):
        response = self.pc.synthesize_speech("Hello world")
        speech = response['AudioStream'].read()
        self.assertIsNotNone(speech)


if __name__ == '__main__':
    unittest.main()
