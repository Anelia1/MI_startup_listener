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
from icon_manager import IconManager
from config import Config


lock = Lock()


class MIMonitor:
    """ Class representing the core of MI_Monitor app """
    _is_running = False
    _config = Config()
    _icon_manager = IconManager()
    # Vosk Speech Recognition
    _queue = queue.Queue()
    _device_info = sd.query_devices(kind='input')  # All available devices
    _samplerate = int(_device_info['default_samplerate'])  # Selected device info
    _model = vosk.Model(_config.get_vosk_path())
    _recogniser = vosk.KaldiRecognizer(_model, _samplerate)
    _current_phrase = ""  # Current transcribed text
    # MI app
    _mi_exe = _config.get_mi_exe()
    _mi_folder = _config.get_mi_folder()
    _mi_exe_path = _config.get_mi_exe_path()
    _bat_exit = _config.get_bat_path() # /im
    _bat_forced_exit = _config.get_bat_path("forced") # /f
    _start_phrases = _config.get_trigger_phrases("start")
    _stop_close_phrases = _config.get_trigger_phrases("stop or close")




    @classmethod
    def start(cls) -> None:
        if not cls.is_active():
            cls._is_running = True
        cls.start_audio_recording(cls)
        # start background thread
        thread_background_checks = Thread(target=cls.background_checks, 
                                daemon = True, 
                                name="MIMonitor MainTread helper")
        thread_background_checks.start()


    def start_audio_recording(cls):
        """
        Provides access to setting up the 
        recorder from methods in the class.
        Used for control - start 
        speaker recognition audio stream
        """
        try: 
            cls.ris =  sd.RawInputStream(samplerate=cls._samplerate, blocksize=8000,
                                        device=None, dtype='int16', 
                                        channels=1, callback=cls._callback)
        except Exception as e:
            print(e)
            raise
        else:
            cls._recogniser.Reset()
            cls.ris.start()
            print("KITA Audio Stream Started")


    def stop_audio_recording(cls) -> None:
        """
        Stop/Pause audio stream
        """
        try:
            cls.ris.stop()
            cls.ris.close()
        except Exception as e:
            print(f"<KITA> Audio Stream could not be stopped: {e}")
            raise
        else:
            print("KITA Audio Stream Stopped/Paused")


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
    def run(cls) -> None:
        """
        Run consistently while the app is open
        """
        try:
            # The Loop
            while cls.get_state():
                cls._perform_action()
            cls.stop_audio_recording()
            print("Vosk closed")
        except Exception as e:
            print("MIMonitor run() failed: ", e)


    @classmethod
    def _perform_action(cls):
        # Obtain recognised speaker's phrases
        json_data = cls._get_current_phrase_dict()
        for key, value in json_data.items(): 
            if key in ('partial', 'text'): 
                cls._current_phrase = value

        # If the speaker says a trigger phrase
        if cls._current_phrase == "":
            return
        print("PHRASE: ", cls._current_phrase)

        for ph in cls._stop_close_phrases:
            if ph in cls._current_phrase: 
                cls.do_on_stop_phrase()
                cls._icon_manager.red_icon_set() # icon red

        for ph in cls._start_phrases:
            if ph in cls._current_phrase:
                cls.do_on_start_phrase()
                cls._icon_manager.green_icon_set() # icon green

            cls._current_phrase = "" # reset
            cls._recogniser.Reset()
            sys.stdin.flush()
            sys.stdout.flush()



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
            subprocess.Popen("start cmd /C" + cls._mi_exe, cwd = cls._mi_folder, shell=True)
            print("STARTED MI")
        except Exception as e:
            print("MITracker.do_on_start_phrase(): subprocess issue", e)
        ## MacOS
        #elif sys.platform == "darwin":
        #    subprocess.Popen("./" + MI_EXE, cwd = MI_FOLDER, shell=True)
        MI_instance = cls._MI_process_info()
        if MI_instance:
            print(f"{cls._mi_exe} app detected in process list") # MI app is confirmed running
        else: 
            print(f"{cls._mi_exe} app NOT detected in process list, There was a problem with starting the app.")


    @classmethod
    def do_on_stop_phrase(cls):
        """
        Kills MI instance
        """
# TODO
        MI_instance = cls._MI_process_info()
        if MI_instance:
            print(MI_instance)
            print("Killing MI now...")
            try:
                subprocess.Popen("TASKKILL /IM " + cls._mi_exe) # taskkill attempt
                time.sleep(1) # wait to exit
                print(f"Killed {cls._mi_exe} with /IM")
            except:
                try:
                    subprocess.Popen("TASKKILL /F " + cls._mi_exe) # force termination
                    time.sleep(1) # wait to exit
                    print(f"Killed {cls._mi_exe} with /F")
                except:
                    try:
                        os.open(cls._bat_exit)
                        print(f"Killed {cls._mi_exe} with bat /IM")
                    except:
                        os.open(cls._bat_forced_exit)
                        print(f"Killed {cls._mi_exe} with bat /F")
            time.sleep(1)
            MI_second_check = cls._MI_process_info()
            if MI_second_check:
                print("There was a problem and MI app could not be closed! ")
                raise


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
            raise
        output_list = []
        for task in output.strip().split("\r\r\n\r\r\n"):
            output_list.append(dict(e.split("=", 1) for e in task.strip().split("\r\r\n")))
        for process in output_list:
            if process == cls._mi_exe:
                MI_instance.append(process)
            # Option to search for ANY instance of MI, not just the one we are dealing with
            #for sname in ['UCL-MI3', 'MI3']:
            #    if process['Name'].startswith(sname): # currently if the name starts with UCL or MI !!
            #        MI_instance.append(process)
            #        cls._process_name = process['Name']
                    #print(process)
        return MI_instance


    def do_on_restart_phrase(cls):
        """
        On Start works as a restart as well
        so thing might not be needed
        """
        cls.do_on_stop_phrase()
        cls.do_on_start_phrase()



if __name__ == "__main__":
    try:
        # Start MI
        m = MIMonitor
        m.start()
        print("[MIM Started]")
        print("Say 'start motion/hand/hands/face' to run MI\n or 'close motion/hand/hands/face' to close MI")
        while m.is_active():
                m.run()
        # Stop MIkop
        print("[MIM Stopped]")
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