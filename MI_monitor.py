'''
Author: Anelia Gaydardzhieva
Comments: 
MI Monitor is the starting point for the app

All modules in this app are cross platform, 
however, some commands are not 
#TODO: and it requires improvement for MacOS adaptation

The info file is used as a communication mailbox 
between MIMonitor and MITracker.
'''
import json
import os, sys
import queue
import sys
import time
import sounddevice as sd
import subprocess
from threading import Lock, Thread
import vosk
vosk.SetLogLevel(-1)
from Icon_manager import IconManager

icon_manager = IconManager()

def check_paths(*paths):
    """
    Adapted for multipath checks
    """
    for path in paths:
        if not os.path.exists(path):
            raise FileNotFoundError(f"[MI_Monitor] Path {path} was not found")

VOSK_MODEL_NAME = "vosk_english"
VOSK_PATH = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "model", VOSK_MODEL_NAME))


MI_APP_NAME = "MI3-FacialNavigation-3.04" # app name
MI_EXE = MI_APP_NAME + ".exe" # executable name
MI_FOLDER = "UCL MI3 Facial Navigation" # folder name of executable

# By default we are assuming MI and MIMonitor are in the same directory since they will be installed 
# via the same installer software with default locations (if the user hasn't changed it).
# TODO: This class's _MI_process_info() method and various more in tests dir allow us
# to grab plenty of system information (extept 'status' which is apparently a problem)
# including selecting running processes by name and returning it ExecutablePath. 
# This has not yet been handled, because it it heavily dependent on the circumstances in which
# the app will be used. Currently MIMonitor assumes that there will be only one MI app running on 
# the machine and closes all instances of it if more than one.

MI_FOLDER_PATH = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", MI_FOLDER)) # expected path
MI_EXE_PATH = os.path.join(MI_FOLDER_PATH, MI_EXE)

check_paths(VOSK_PATH, MI_FOLDER_PATH, MI_EXE_PATH)




ACCEPTABLE_START_PHRASES = ['start hand', 'start face', 'start motion'] # easier to adjust from here
ACCEPTABLE_STOP_PHRASES = ['stop hand', 'stop face', 'stop motion']

LIST_MI_NAME_STARTS_WITH = ['UCL-MI3', 'MI3']


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
    _report = f"MI closed because of: "
    _process_name = "MI_app"



    @classmethod
    def start(cls) -> None:
        cls._is_running = True


        cls.ris =  sd.RawInputStream(samplerate=cls._samplerate, blocksize=8000,
                                        device=None, dtype='int16', channels=1, 
                                        callback=cls._callback)

        thread_background_checks = Thread(target=cls.background_checks, 
                                        daemon = True, 
                                        name="MIMonitor MainTread helper")

        cls.ris.start()
        thread_background_checks.start()
        
        cls.run(cls.ris)


    @classmethod
    def background_checks(cls) -> None:
        """
        If more than one processess start with UCL or MI
        we are currently assuming that there are multiple instances of the 
        same application. The names os each application can be defined
        at the top of this file.
        """
        while True:
            proc_names_ls = []
            with lock:
                MI_instances = cls._MI_process_info()
            if MI_instances: 
                proc_names_ls = [proc['Name'] for proc in MI_instances]
            if len(proc_names_ls) > 1: # if MI running 2 on more times
                with lock:
                    cls.do_on_stop_phrase() # close all and open one
                    time.sleep(2)
                    cls.do_on_start_phrase()



    @classmethod
    def get_state(cls) -> bool:
        """
        Returns if there is an instance of the MI Monitor running
        """
        return cls._is_running


    @classmethod
    def run(cls, recorder) -> None :
        """
        Run consistently while the app is open
        """
        try:
            # The Loop
            while cls.get_state():
                cls._perform_action()

            recorder.stop()
            recorder.close()
            cls._stop()
            print("Vosk closed")
        except Exception as e:
            print("MIMonitor run() failed: ", e)


    @classmethod
    def _perform_action(cls):

        json_data = {}
        # Obtain recognised speaker's phrases
        try:
            json_data = cls._get_current_phrase_dict()
        except Exception as e:
            print(f"Exception {e} in _perform_action()")
            #sys.exit()

        if json_data: 
            for key, value in json_data.items(): 
                if key in ('partial', 'text'): 
                    cls._current_phrase = value

            # If the speaker says a trigger phrase
            if cls._current_phrase != "":
                print("PHRASE: ", cls._current_phrase)
                for ph in ACCEPTABLE_STOP_PHRASES:
                    if ph in cls._current_phrase: 
                        cls.do_on_stop_phrase()
                        icon_manager.red_icon_set() # icon red
                for ph in ACCEPTABLE_START_PHRASES:
                    if ph in cls._current_phrase:
                        cls.do_on_start_phrase()
                        icon_manager.green_icon_set() # icon green

                try:
                    cls._current_phrase = "" # reset
                    cls._recogniser.Reset()
                    sys.stdin.flush()
                    sys.stdout.flush()
                except Exception as ex:
                    print("Exception with json parsing or vosk", ex)


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
    def is_active(cls) -> bool:
        return cls._is_running


    #######################################################################



    @classmethod
    def do_on_start_phrase(cls):
        """
        Method to start MI
        """
        try:
            MI_instance = cls._MI_process_info()
            if MI_instance:
                cls.do_on_stop_phrase() # making sure
        except Exception as e:
            print("MITracker.do_on_start_phrase(): get process instance and kill MI", e)
            return

        ## Windows
        #if sys.platform == "win32":
        #    print("Starting MI now...")
        try: 
            subprocess.Popen("start cmd /C" + MI_EXE, cwd = MI_FOLDER_PATH, shell=True)
            print("STARTED MI")
        except Exception as e:
            print("MITracker.do_on_start_phrase(): subprocess issue", e)
        ## MacOS
        #elif sys.platform == "darwin":
        #    subprocess.Popen("./" + MI_EXE, cwd = MI_FOLDER, shell=True)

        MI_instance = cls._MI_process_info()
        if MI_instance:
            print(f"{MI_EXE} app detected in process list") # MI app is confirmed running
        else: 
            print(f"{MI_EXE} app NOT detected in process list, There was a problem with starting the app.")

    @classmethod
    def do_on_stop_phrase(cls):
        """
        Kills MI instance
        """
        try:
            MI_instance = cls._MI_process_info()
            if MI_instance:
                print(MI_instance)
                print("Killing MI now...")
                subprocess.Popen("TASKKILL /IM " + cls._process_name) # taskkill attempt
                time.sleep(1) # wait to exit
                MI_instance = cls._MI_process_info() # check
                if MI_instance: # if still running
                    time.sleep(3) # wait to exit 
                    MI_instance = cls._MI_process_info() # check
                    print(f"Note killed yet {MI_EXE}")
                    if MI_instance: # if still running
                        subprocess.Popen("TASKKILL /F " + cls._process_name) # force termination
                        return
                #for p in psutil.process_iter():
                #    if MI_EXE in str(p) and p.info(['pid']!=os.getpid()): # no suidides!
                #        p.kill()
                print(f"Killed {MI_EXE}")
        except Exception as e:
            print("MITracker.kill_MI(): general error: ", e)
            try:
                subprocess.Popen("TASKKILL /F " + cls._process_name)
               
            except Exception:
                print(f" /F didn't work either'")
                return
            return


    @classmethod
    def _MI_process_info(cls):
        """
        Returns MI instance
        or instances
        """
        MI_instance = []
        try:
            output = subprocess.check_output(["wmic", "process", "list", "full", "/format:list"])
            output = output.decode("utf-8") # binary
        except Exception as e:
            print("ERROR <MI_process_info> subprocess.check_output: ", e)
        output_list = []
        try:
            for task in output.strip().split("\r\r\n\r\r\n"):
                output_list.append(dict(e.split("=", 1) for e in task.strip().split("\r\r\n")))
            for process in output_list:
                for sname in LIST_MI_NAME_STARTS_WITH:
                    if process['Name'].startswith(sname): # currently if the name starts with UCL or MI !!
                        MI_instance.append(process)
                        cls._process_name = process['Name']
                        #print(process)
        except Exception as ex:
            print("ERROR <MI_process_info> strip(), append(), _process_name: ", ex)
        return MI_instance


    def do_on_restart_phrase(cls):
        """
        On Start works as a restart as well
        so thing might not be needed
        """
        cls.do_on_stop_phrase()
        cls.do_on_start_phrase()




if __name__ == '__main__':
    try:
        # MIM
        m = MIMonitor
        m.start()
        print("MI Monitor Started")
        
        while m.get_state():
            pass
    except Exception as e:
        try:
            m._stop()
            print(f"Stopped with Exception: {e}")
        except Exception as ex:
            print(f"Failed to stop with _stop() Exception: {ex}")
            raise
        raise
    # Error Stop: Not Emergency
    except SystemExit as se:
        print("SystemExit: ", se)
        if se.code != 255:
            raise
    # Error Stop: Emergency
    else:
        print("Emergency Exit")
        os._exit(255)


if __name__ == "__main__":
    try:
        # Start MI
        m = MIMonitor
        m.start()
        print("[[[MIM Started]]]")
        print("Say 'start motion/hand/hands/face' to run MI \nor 'close motion/hand/hands/face' to close MI")
        while m.is_active():
                m.run()
        # Stop MIkop
        print("[[[MIM Stopped]]]")
    except Exception as e:
        try:
            m._stop()
            print(f"[MIM Stopped with _stop() because of Exception: {e}]")
        except Exception as ex:
            print(f"[MIM failed to stop with _stop() because of Exception: {ex}]")
            raise
        raise
    # Error
    except SystemExit as se:
        print(f"SystemExit: {se}")
        if se.code != 255:
            print(f"SystemExit: non-emergency")
            raise
        else:
            print(f"SystemExit: emergency")
            os._exit(255)