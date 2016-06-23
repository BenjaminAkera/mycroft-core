import os
import wave
from glob import glob

import pyaudio
import pyee
from os.path import dirname, join
from speech_recognition import Microphone, AudioSource

from mycroft.client.speech.listener import AudioConsumer
from mycroft.client.speech.local_recognizer import LocalRecognizer
from mycroft.client.speech.mic import MutableStream, ResponsiveRecognizer
from mycroft.util.log import getLogger
from mycroft.client.speech.mic import logger as speech_logger

__author__ = 'wolfgange3311999'
logger = getLogger('audio_test_runner')


class MockStream(object):
    def __init__(self, file_name):
        self.file = wave.open(file_name, 'rb')
        self.size = self.file.getnframes()
        self.sample_rate = self.file.getframerate()
        self.sample_width = self.file.getsampwidth()

    def read(self, chunk_size):
        if abs(self.file.tell() - self.size) < 10:
            raise EOFError
        return self.file.readframes(chunk_size)

    def close(self):
        self.file.close()


class MockMicrophone(AudioSource):
    def __init__(self, file_name):
        self.stream = MockStream(file_name)
        self.SAMPLE_RATE = self.stream.sample_rate
        self.SAMPLE_WIDTH = self.stream.sample_width
        self.CHUNK = 1024

    def close(self):
        self.stream.close()


class AudioTester(object):
    def __init__(self, samp_rate):
        self.ww_recognizer = LocalRecognizer(samp_rate, 'en-us')
        self.listener = ResponsiveRecognizer(self.ww_recognizer)
        speech_logger.setLevel(100)  # Disables logging to clean output

    @staticmethod
    def absolute_path(name):
        root_dir = dirname(dirname(__file__))
        return join(root_dir, 'audio-test', 'data', 'query_after', name)

    def test_audio(self, file_name):
        source = MockMicrophone(file_name)
        ee = pyee.EventEmitter()

        class SharedData:
            found = False

        def on_found_wake_word():
            SharedData.found = True

        ee.on('recognizer_loop:record_begin', on_found_wake_word)

        try:
            self.listener.listen(source, ee)
        except EOFError:
            pass

        return SharedData.found


BOLD = '\033[1m'
NORMAL = '\033[0m'
GREEN = '\033[92m'
RED = '\033[91m'

def bold_str(val):
    return BOLD + str(val) + NORMAL

if __name__ == "__main__":
    file_names = glob(AudioTester.absolute_path('*.wav'))

    # Grab audio format info from first file
    ex_file = wave.open(file_names[0], 'rb')
    tester = AudioTester(ex_file.getframerate())

    num_found = 0
    total = len(file_names)

    for file_name in file_names:
        short_name = os.path.basename(file_name)
        was_found = tester.test_audio(file_name)
        print(BOLD)
        if was_found:
            print(GREEN + "Detected " + NORMAL + " - " + short_name)
            num_found += 1
        else:
            print(RED + "Not found" + NORMAL + " - " + short_name)
        print(NORMAL)


    def to_percent(numerator, denominator):
        return "{0:.2f}".format((100.0 * numerator) / denominator) + "%"


    print("Found " + bold_str(num_found) + " out of " + bold_str(total))
    print(bold_str(to_percent(num_found, total)) + " accuracy.")
    print
