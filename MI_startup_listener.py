import subprocess
import queue
import sounddevice as sd
import vosk
# Options: 0 = allow model debugging; -1 = remove model debugging
vosk.SetLogLevel(-1)
import os
import sys
import json


VOSK_PATH = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "model", "vosk_english"))


class MIStartupListener:
    
    def __init__(self):
        # queue.Queue() is a deque. To clear a deque use self.q.queue.clear()
        self.q = queue.Queue()
        device_info = sd.query_devices(kind='input') # All available devices
        self.samplerate = int(device_info['default_samplerate']) # Selected device info
        self.model = vosk.Model(VOSK_PATH) # Speech recognition model
        self.recogniser = vosk.KaldiRecognizer(self.model, self.samplerate) # Recogniser (Kaldi function which does the actual speech-to-text conversion)
        self.current_phrase = "" # Current transcribed text 
        self.running = False
        self.trigger_phrase = "start application now"


    def start(self):
        self.running = True
        with sd.RawInputStream(samplerate=self.samplerate, blocksize=8000,\
            device=None, dtype='int16', channels=1, callback=self._callback): 

            # The Loop
            while self.running:
                self._vosk_action()


    def _vosk_action(self):
        try:
            json_data = self._get_current_phrase_dict() 
        except Exception as e:
            print("Exception", e)

        # json_data = {'partial': ''}
        print("json_data.items()", json_data)

        for key, value in json_data.items(): 
            if key in ('partial', 'text'):
                self.current_phrase = value

        if self.current_phrase != "":
           
            # Only if the speaker has said the trigger phrase
            if self.trigger_phrase == self.current_phrase:

# TODO: MI should not allow the app to be open more than once
# TODO: Check if MI is open, track the app 
# TODO: Ensure cross platform persistance - deamon threads?
# TODO: Custom installer to setup in Starter folder
# TODO: It should never ever close -> listen!

                #self.stop() # breaks the loop
                self.open_MI_app()
                # TODO: 
                #while MI_app is open:
                #    wait()
                print("startup listener is closed!")

                #self.start() # starts the loop

        print("vosk:", self.current_phrase)

    def _callback(self, indata, frames: int, time, status) -> None:
        """
        This is called (from a separate thread) for each audio block.
        It returns the microphone audio data
        """
        if status:
            print(status, file=sys.stderr)
            sys.stdout.flush()
        self.q.put(bytes(indata))


    def _get_current_phrase_dict(self):
        json_data = {}
        audio = self.q.get()
        if self.recogniser.AcceptWaveform(audio): # processes the wav (user speech) audio data; convert to text
            json_data = json.loads(self.recogniser.Result()) # Vosk returns a json object by default {"Text", "user speech goes here"} # FinalResult?
        else:
            json_data = json.loads(self.recogniser.PartialResult())
        return json_data

    def stop(self):
        self.running = False

    @staticmethod
    def open_MI_app():
        directory = 'C:\MI_app'
        cmdline = "MI_app.exe"
        subprocess.call("start cmd /C " + cmdline, cwd=directory, shell=True)


m = MIStartupListener()
m.start()
input("Waiting...")

#m.stop() # this needs to be accessible
#m._get_current_phrase_dict() # don't do that!



# TODO: replace methods that do not use self with @staticmethod