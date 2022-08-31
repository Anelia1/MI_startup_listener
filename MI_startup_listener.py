import queue
import sounddevice as sd
import vosk
vosk.SetLogLevel(-1)
import os, sys, subprocess, json
import psutil
import threading

""" 
To test this app, place MI_app.exe in C:/ location or change the location
"""

"""
--------------------------------------------------------------------
TODO: Use in KITA - MI should not allow the app to be open more than once
TODO: replace methods in KITA that do not use self with @staticmethod
--------------------------------------------------------------------
"""

#### --------------------------------------------------------------------
# DONE: Cross platform 
# TODO: Ensure PERSISTENCE - deamon threads? - run as a service?

# TODO: Compile with Nuitka and setup with Installer to add this app to os Startup folder
# TODO: Use Installer (there are free open source ones) to add this app to os Startup folder
# TODO: Make sure the Installer adds this app to os Startup folder (or Mac/Linux equivalent)
# TODO: It should never ever close
# TODO: Look into MI_app name and path
# TODO: REPLACE model HACK with communicating threads (maybe condition object)
#### --------------------------------------------------------------------

VOSK_PATH = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "model", "vosk_english"))
lock = threading.RLock()
lock2 = threading.Lock()


class MIStartupListener(threading.Thread):
    _instance = None
    _is_running = False
    _pause_listener = False

    def __new__(cls):
        with lock:
            if cls._instance is None and not cls._is_running:
                # General
                cls._instance = super(MIStartupListener, cls).__new__(cls)
                #cls.daemon = True # inherited property
                cls._condition_object = threading.Condition()
                cls._flag = False
                cls._queue = queue.Queue()
                # Speech recognition
                device_info = sd.query_devices(kind='input') # All available devices
                cls.samplerate = int(device_info['default_samplerate']) # Selected device info
                cls.model = vosk.Model(VOSK_PATH) # Speech recognition model
                cls.recogniser = vosk.KaldiRecognizer(cls.model, cls.samplerate) # Recogniser (Kaldi function which does the actual speech-to-text conversion)
                cls.current_phrase = "" # Current transcribed text 
                #cls.trigger_phrase = "start application now" 
                cls.trigger_phrase = "start" # used for testing

                cls._waiting = threading.Thread(target=cls._waiting)
                cls._waiting.start()
                cls._waiting.join()
            return cls._instance


    def run(self):
        """
        START Listener
        """
        with lock:
            MIStartupListener._is_running = True

        with sd.RawInputStream(samplerate=self.samplerate, blocksize=8000,\
            device=None, dtype='int16', channels=1, callback=self._callback): 

            # The Loop
            while MIStartupListener._is_running:
                self._listening_action()







    def _waiting(self):
        with lock2:
            with self._condition_object:
                if not self._flag:
                    self._condition_object.wait()
                while "mi_app" not in ' '.join([str(p).lower() for p in psutil.process_iter()]):
                    pass # wait until MI app opens
                print("MI app app opened")
                self._wait_MI_closed()


    def _wait_MI_closed(self):
        while "mi_app" in ' '.join([str(p).lower() for p in psutil.process_iter()]):
            pass  # wait until MI app closes
        print("MI app closed")
        self._condition_object


    def _listening_action(self):
        """
        Ran consistently during the app is open
        """


        try:
            json_data = self._get_current_phrase_dict() 
        except Exception as e:
            print("Exception", e)

        for key, value in json_data.items(): 
            if key in ('partial', 'text'):
                self.current_phrase = value
        
        # If something has been said
        if self.current_phrase != "":
            # If the speaker has said the trigger phrase
            if self.trigger_phrase in self.current_phrase:

                MIStartupListener._pause_listener = True

                print("Startup Listener is closed")
                # Runs MI app
                self.open_MI_app() #Note, this command only STARTS the trigeering of the app, 
                # it may take a few seconds for app to start fully. 
                print("MI app triggered")

                self._condition_object.notify()

                # Starts the listener again
                MIStartupListener._pause_listener = False
                print("Listener started again")

        #print("vosk:", self.current_phrase)

    def _callback(self, indata, frames: int, time, status) -> None:
        """
        This is called (from a separate thread) for each audio block.
        It returns the microphone audio data
        """
        if status:
            print(status, file=sys.stderr)
            sys.stdout.flush()
        self._queue.put(bytes(indata))

    def _get_current_phrase_dict(self):
        """
        Get current phrase from vosk
        """
        json_data = {}

        audio = self._queue.get()
        # Pause if MI app is open

        if MIStartupListener._pause_listener:
            audio = b'\x00'
        # Processes the wav (user speech) audio data; convert to text
        if self.recogniser.AcceptWaveform(audio): 
            # Get complete result
            # vosk returns a json object by default {"Text", "user speech goes here"} # FinalResult?
            json_data = json.loads(self.recogniser.Result()) 
        else:
            # Get partial result
            json_data = json.loads(self.recogniser.PartialResult())
        return json_data

    @staticmethod
    def open_MI_app():
        """
        Open MI app
        """
        directory = 'C:\MI_app'
        cmdline = "MI_app.exe"
        subprocess.call("start cmd /C " + cmdline, cwd=directory, shell=True)

    def get_is_running(self):
        """
        Returns whether KITA is ON or OFF
        """
        with lock:
            return MIStartupListener._is_running

    def end(self):
        """
        STOP 
        """
        with lock:
            MIStartupListener._is_running = False


#listener_app = MIStartupListener()
#listener_app.start()


