import subprocess
import queue
import sounddevice as sd
import vosk
# Options: 0 = allow model debugging; -1 = remove model debugging
vosk.SetLogLevel(-1)
import os
import sys
import json
import wmi # used to check if MI app is open 

""" 
To test this app, place MI_app.exe in C:/ location or change the location
"""

# TODO: compile and setup with Installer to add this app to os Startup folder

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
        self._running = False
        #self.trigger_phrase = "start application now"
        self.trigger_phrase = "start"

    def start(self):
        self._running = True
        with sd.RawInputStream(samplerate=self.samplerate, blocksize=8000,\
            device=None, dtype='int16', channels=1, callback=self._callback): 

            # The Loop
            while self._running:
                self._vosk_action()


    def _vosk_action(self):

        try:
            json_data = self._get_current_phrase_dict() 
        except Exception as e:
            print("Exception", e)

        # json_data = {'partial': ''}
        #print("json_data.items()", json_data)

        for key, value in json_data.items(): 
            if key in ('partial', 'text'):
                self.current_phrase = value

        if self.current_phrase != "":
           
            # Only if the speaker has said the trigger phrase
            if self.trigger_phrase in self.current_phrase:

# TODO: MI should not allow the app to be open more than once
# TODO: Check if MI is open, track the app 
# TODO: Ensure cross platform persistance - deamon threads?
# TODO: Custom installer to setup in Starter folder
# TODO: It should never ever close -> listen!

                self.stop() # breaks the loop
                # stops listening when MI app is open
                self.model = None # clear out vosk model
                self.recogniser = None # clear out vosk recogniser     
                print("Startup Listener is closed")
                self.open_MI_app() # runs MI app
                print("MI app triggered")

                while True not in ("MI_app" in p_str for p_str in (str(p) for p in f.Win32_Process())):
                    pass
                print("MI_app registered in psutil")
  


# TODO: Test
                #if "MI_app" in (p.name() for p in psutil.process_iter()): # while MI app is _running
                while True in ("MI_app" in p_str for p_str in (str(p) for p in f.Win32_Process())):
                    pass # do nothing
 

                print("MI app closed")
                # begins listening again when MI app is closed
                self.model = vosk.Model(VOSK_PATH) # restore vosk model
                self.recogniser = vosk.KaldiRecognizer(self.model, self.samplerate) # restore vosk recogniser
        
                self.start() # starts the loop again
                print("Startup Listener startED again")

        #print("vosk:", self.current_phrase)

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
        if not self._running:
            audio = b'\x00'

        if self.recogniser.AcceptWaveform(audio): # processes the wav (user speech) audio data; convert to text
            json_data = json.loads(self.recogniser.Result()) # Vosk returns a json object by default {"Text", "user speech goes here"} # FinalResult?
        else:
            json_data = json.loads(self.recogniser.PartialResult())
        return json_data

    def stop(self):
        self._running = False

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