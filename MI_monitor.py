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
import os
from subprocess import Popen, check_output, call
import sys
import time
from threading import Thread, Lock
import queue

import sounddevice as sd
from typing import Dict, List
from vosk import Model, KaldiRecognizer, SetLogLevel

from config import Config
from icon_manager import IconManager
SetLogLevel(-1)

lock = Lock()

class MIMonitor:
    """ Class representing the core of MI_Monitor app """

    def __init__(self):
        self._is_running = False
        self._config = Config()
        self._icon_manager = IconManager()
        # Vosk Speech Recognition
        self._queue = queue.Queue()
        self._device_info = sd.query_devices(kind='input')  # All available devices
        self._samplerate = int(self._device_info['default_samplerate'])  # Selected device info
        self._model = Model(self._config.get_vosk_path())
        self._recogniser = KaldiRecognizer(self._model, self._samplerate)
        self._current_phrase = ""  # Current transcribed text
        # MI app
        self._mi_exe = self._config.get_mi_exe()
        self._mi_folder_path = self._config.get_mi_folder_path()
        self._bat_exit = self._config.get_bat_path("exit") # /im
        self._bat_forced_exit = self._config.get_bat_path("forced") # /f
        self._bat_folder_path = self._config.get_bat_folder_path()
        self._start_phrases = self._config.get_trigger_phrases("start")
        self._stop_close_phrases = self._config.get_trigger_phrases("stop or close")
        self._last_MI_check = False # Starts at False since the icon is initially set to red; True == green icon
        #self._current_icon_status = False
        self.thread_instances_tracker = Thread(target=self.MI_instances_tracker, 
                                daemon = True,
                                name="MIMonitor Instances Tracker")
        self.thread_icon_status_tracker = Thread(target=self.icon_status_tracker, 
                                daemon = True,
                                name="MIMonitor Icon Status Tracker")


    def start(self) -> None:
        """
        Start MIMonitor
        """
        if self.is_active():
            return
        self._is_running = True
        self.start_audio_recording()
        # start background thread
        self.thread_instances_tracker.start()
        self.thread_icon_status_tracker.start()


    def MI_instances_tracker(self) -> None:
        """
        If more than one processess start with UCL or MI
        we are currently assuming that there are multiple instances of the 
        same application. The names os each application can be defined
        at the top of this file.
        """
        while self.is_active():
            with lock:
                MI_instances = self._MI_process_info()
            if len(MI_instances) > 1: 
                with lock:
                    self.do_on_stop_phrase() # close all
                    self.do_on_start_phrase() # open one


    def icon_status_tracker(self) -> None:
        """
        Keeps the icon up to date
        Helps improve MIMonitor speed
        """
        while self.is_active():
            # Check if MI status has changed
            with lock:
                MI_instances = self._MI_process_info()
            if len(MI_instances) == 0:
                self.set_icon(False) # update icon red
            elif len(MI_instances) == 1:
                self.set_icon(True) # update icon green
            elif len(MI_instances) > 1:
                self.do_on_restart_phrase()


    def start_audio_recording(self) -> None:
        """
        Provides access to setting up the 
        recorder from methods in the class.
        Used for control - start 
        speaker recognition audio stream
        """
        try: 
            self.ris =  sd.RawInputStream(samplerate=self._samplerate, blocksize=8000,
                                        device=None, dtype='int16', 
                                        channels=1, callback=self._callback)
        except Exception as e:
            print(e)
            raise
        else:
            self.ris.start()
            print("KITA Audio Stream Started")


    def stop_audio_recording(self) -> None:
        """
        Stop/Pause audio stream
        """
        try:
            self.ris.stop()
            self.ris.close()
        except Exception as e:
            print(f"<KITA> Audio Stream could not be stopped: {e}")
            raise
        else:
            print("KITA Audio Stream Stopped/Paused")


    def run(self) -> None:
        """
        The main loop method
        """
        # Obtain recognised speaker's phrases
        json_data = self._get_current_phrase_dict()
        for key, value in json_data.items(): 
            if key in ('partial', 'text'): 
                self._current_phrase = value
        # If the speaker said nothing return
        if self._current_phrase == "":
            return
        print("PHRASE: ", self._current_phrase)
        # If they said a stop/close phrase
        for phrase in self._stop_close_phrases:
            if phrase in self._current_phrase: 
                with lock:
                    self.do_on_stop_phrase()
        # If they said a start phrase
        for phrase in self._start_phrases:
            if phrase in self._current_phrase:
                with lock:
                    self.do_on_start_phrase()
        self._current_phrase = "" # reset


    def set_icon(self, value) -> None:
        """
        Sets the icon to the correct colour
        """
        if self._last_MI_check and not value:
            self._icon_manager.red_icon_set() # set icon red
            self._last_MI_check = False
        elif not self._last_MI_check and value:
            self._icon_manager.green_icon_set() # set icon green
            self._last_MI_check = True


    def _get_current_phrase_dict(self) -> Dict[str, str]:
        """
        Get current phrase from vosk
        """
        json_data = {}
        audio = self._queue.get()
        # Processes the wav (user speech) audio data; convert to text
        if self._recogniser.AcceptWaveform(audio): 
            # Get complete result
            # Vosk returns a json object by default {"Text", "user speech goes here"} 
            json_data = json.loads(self._recogniser.Result()) 
        # Partials can be enabled for faster responses, however, only single words
        # speech commands are accurate. In addition
        #else:
        #    # Get partial result
        #    json_data = json.loads(self._recogniser.PartialResult())
        return json_data


    def _callback(self, indata, frames: int, time, status) -> None:
        """
        This is called (from a separate thread) for each audio block.
        It returns the microphone audio data
        """
        if status:
            print(status, file=sys.stderr)
            sys.stdout.flush()
        if self._is_running:
            self._queue.put(bytes(indata))


    def stop(self) -> None:
        """
        STOP 
        """
        self._is_running = False
        try:
            self.stop_audio_recording()
        except:
            print("<_stop()> There was a problem stopping audio recording.")


    def is_active(self) -> bool:
        return self._is_running


    #######################################################################


    def do_on_start_phrase(self) -> None:
        """
        Method to start MI
        """
        MI_instances = self._MI_process_info()
        if len(MI_instances) == 1:
            return
        elif len(MI_instances) > 1:
            self.do_on_stop_phrase()
        ## Windows
        #if sys.platform == "win32":
        #    print("Starting MI now...")
        try: 
            Popen("start cmd /C" + self._mi_exe, cwd=self._mi_folder_path, shell=True)
            #p = Popen("start cmd /C" + self._mi_exe, cwd = self._mi_folder_path, shell=True)
            #stdout, stderr = p.communicate()
        except Exception as e:
            print("MIMonitor.do_on_start_phrase(): start subprocess issue", e)
            raise
        ## MacOS
        #elif sys.platform == "darwin":
        #    Popen("./" + MI_EXE, cwd = MI_FOLDER, shell=True)
        time.sleep(0.5) # wait for process to get added to os processes
        MI_instances = self._MI_process_info()
        if len(MI_instances) == 1:
            print(f"{self._mi_exe} app detected in process list") # MI app is confirmed running
            self.set_icon(True)
        else: # second check
            time.sleep(0.5) # wait for process to get added to os processes
            MI_instances = self._MI_process_info()
            if len(MI_instances) == 1:
                print(f"{self._mi_exe} app detected in process list") # MI app is confirmed running
                self.set_icon(True)
            else:
                raise RuntimeError(f"{self._mi_exe} app NOT detected in process list. There was a problem with starting the app. Please make sure the path is correct.")


    def do_on_stop_phrase(self) -> None:
        """
        Kills MI instance(s)
        """
        MI_instances = self._MI_process_info()
        if len(MI_instances) == 0:
            return
        print("bat_exit: ", self._bat_exit, "bat_folder: ", self._bat_folder_path)
        Popen("start cmd /C" + self._bat_exit, cwd=self._bat_folder_path, shell=True) # attempt image process kill
        time.sleep(0.5) # wait for process to get removed from os processes
        MI_instances = self._MI_process_info()
        if len(MI_instances) == 0:
            self.set_icon(False)
            print("MI closed")
        else:
            Popen("start cmd /C" + self._bat_forced_exit, cwd=self._bat_folder_path, shell=True) # forced process kill
            print("MI forced closed")


    def _MI_process_info(self) -> List[str]:
        """
        Returns MI instance
        or instances
        """
        MI_instances = []
        try:
            output = check_output(["wmic", "process", "list", "full", "/format:list"])
            output = output.decode("utf-8") # binary
        except Exception as e:
            print("ERROR <MI_process_info> subprocess.check_output: ", e)
            raise
        output_list = []
        for task in output.strip().split("\r\r\n\r\r\n"):
            output_list.append(dict(e.split("=", 1) for e in task.strip().split("\r\r\n")))
        for process in output_list:
            if process['Name'] == self._mi_exe:
                MI_instances.append(process)
            # Option to search for ANY instance of MI, not just the one we are dealing with
            #for sname in ['UCL-MI3', 'MI3']:
            #    if process['Name'].startswith(sname):
            #        MI_instances.append(process)
            #        self._process_name = process['Name']
                    #print(process)
        return MI_instances


    def do_on_restart_phrase(self) -> None:
        """
        On Start works as a restart as well
        so thing might not be needed
        """
        self.do_on_stop_phrase()
        time.sleep(0.5)
        self.do_on_start_phrase()

    #######################################################################



if __name__ == "__main__":
    try:
        # Start MI
        m = MIMonitor()
        m.start()
        print("[MIM Started]")
        print("Say 'start motion/hands/face' to run MI\n or 'stop/close motion/hands/face' to close MI")
        while m.is_active():
            m.run()
        # Stop MI
        m.stop()
        print("[MIM Stopped]")
    except Exception:
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