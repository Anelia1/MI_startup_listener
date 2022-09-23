'''
Author: Anelia Gaydardzhieva
Comments: 
MI Monitor is the starting point for the app

All modules in this app are cross platform, 
however, some commands are not 
#TODO: and it requires MacOS adaptation

The info file is used as a communication mailbox 
between MIMonitor and MITracker.
'''
import json
import os, sys, time
import queue
import sys
import sounddevice as sd
from threading import Lock
import vosk
vosk.SetLogLevel(-1)
from MI_tracker import MITracker, check_paths, GLOBAL_EVENT
from Icon_manager import IconManager

VOSK_MODEL_NAME = "vosk_english"
VOSK_PATH = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "model", VOSK_MODEL_NAME))
check_paths(VOSK_PATH)

lock = Lock()

class MIMonitor:
    """
    Singleton class for MI_Monitor
    """
    _is_running = False
    _queue = queue.Queue()
    _device_info = sd.query_devices(kind='input')  # All available devices
    _samplerate = int(_device_info['default_samplerate'])  # Selected device info
    _model = vosk.Model(VOSK_PATH)
    _recogniser = vosk.KaldiRecognizer(_model, _samplerate)  # Recogniser (Kaldi function which does the actual speech-to-text conversion)
    _current_phrase = ""  # Current transcribed text


    #def run(self):
    #    """
    #    START MI_Monitor app (MainThread)
    #    """

    #    print("Listening...")
    #    with sd.RawInputStream(samplerate=cls._samplerate, blocksize=8000,
    #                            device=None, dtype='int16', channels=1, callback=cls._callback): 

    #        # The Loop - MainThread
    #        while cls.is_running():
    #            cls._vosk_action()

    @classmethod
    def start(cls) -> None:
        cls._is_running = True
        GLOBAL_EVENT.set()



    @classmethod
    def get_state(cls) -> bool:
        """
        Returns if there is an instance of the MI Monitor running
        """
        return cls._is_running


    @classmethod
    def run(cls) -> None :
        """
        Run consistently while the app is open
        """


        try:
            cls.ris =  sd.RawInputStream(samplerate=cls._samplerate, blocksize=8000,
                                            device=None, dtype='int16', channels=1, callback=cls._callback)
            cls.ris.start()
            # The Loop
            while cls.get_state():
                cls._perform_action()

            cls.ris.stop()
            cls.ris.close()
            cls._stop()
        except Exception as e:
            print("MIMonitor run() failed: ", e)


# TODO: 



    @classmethod
    def _perform_action(cls):
        GLOBAL_EVENT.clear()
        json_data = {}
        # Obtain recognised speaker's phrases
        try:
            json_data = cls._get_current_phrase_dict()
        except Exception as e:
            print(f"Exception {e} in _vosk_action()")
            #sys.exit()

        if json_data: 
            for key, value in json_data.items(): 
                if key in ('partial', 'text'): cls._current_phrase = value
            # If the speaker says the trigger phrase
            if cls._current_phrase != "":
                print("PHRASE: ", cls._current_phrase)
                time.sleep(1)
                with lock:

                    
                    if "stop motion" in cls._current_phrase: 
                        d = {"start_phrase": "false","stop_phrase": "true"}
                        json.dump(d, open('info.json', 'w'))
                    elif "start motion" in cls._current_phrase:
                        d = {"start_phrase": "true","stop_phrase": "false"}
                        json.dump(d, open('info.json', 'w'))
                    GLOBAL_EVENT.set()

                try:
                    cls._current_phrase = "" # reset
                    cls._recogniser.Reset()
                    sys.stdin.flush()
                except Exception as ex:
                    print("Exception with json parsing or vosk", ex)
                    raise


    @classmethod
    def _get_current_phrase_dict(cls):
        """
        Get current phrase from vosk
        """
        json_data = {}

        audio = cls._queue.get()
        # Processes the wav (user speech) audio data; convert to text
        if cls._recogniser.AcceptWaveform(audio): 
            # Get complete result
            # Vosk returns a json object by default {"Text", "user speech goes here"} 
            # TODO: What does FinalResult do?
            json_data = json.loads(cls._recogniser.Result()) 

        # Partials can be enabled for faster responses, however, only single words
        # speech commands are accurate. In addition
        #else:
        #    # Get partial result
        #    json_data = json.loads(cls._recogniser.PartialResult())

        return json_data

    @classmethod
    def _callback(cls, indata, frames: int, time, status) -> None:
        """
        This is called (from a separate thread) for each audio block.
        It returns the microphone audio data
        """
        if status:
            print(status, file=sys.stderr)
            sys.stdout.flush()
        if cls._is_running:
            cls._queue.put(bytes(indata))

    @classmethod
    def _stop(cls) -> None:
        """
        STOP 
        """
        cls._is_running = False
        


    @classmethod
    def is_running(cls) -> bool:
        return cls._is_running





if __name__ == '__main__':
    try:
        # Threads
        #mit = MITracker()
        #sim = StrayIconManager()

        MITracker()
        IconManager()

        # MIM
        m = MIMonitor()
        m.start()
        print("MI Monitor started")
        print("Say 'start motion' to run MI or 'close motion' to close MI")
        while m.get_state():
            m.run()
    except Exception:
        try:
            m._stop()
            #os.startfile('quitMIapp.bat') # Ensures the MI is completely closed
        except Exception:
            raise
        raise







    #    while MIMonitor.get_state():
    #        MIMonitor.run()
    #    MITracker._stop()
    #except Exception:
    #    try:
    #        MITracker._stop()
    #        #os.startfile('quitMIapp.bat') # Ensures the MI is completely closed
    #    except Exception:
    #        raise
    #    raise


