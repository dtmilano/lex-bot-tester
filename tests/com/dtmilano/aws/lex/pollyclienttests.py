import unittest
from tempfile import NamedTemporaryFile

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

    def test_synthesize_speech_audio(self):
        speech = self.pc.synthesize_speech('This is a sample sentence to test synthesizer')['AudioStream'].read()
        temp = NamedTemporaryFile(suffix='.pcm', delete=False)
        temp.write(speech)
        print('Audio saved to {}'.format(temp.name))
        temp.close()


if __name__ == '__main__':
    unittest.main()
