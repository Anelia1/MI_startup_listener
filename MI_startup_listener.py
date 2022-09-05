"""
Author: Anelia Gayrardzhieva
Comments: MI_Monitor main file. 
It runs and closes MI app. 
It keep an icon in Windows system tray, 
which shows red when MI app is closed 
and green when MI app is running.
"""
from ast import excepthandler
import queue
import logging
import random
import sounddevice as sd
import vosk
vosk.SetLogLevel(-1)
import os, sys, subprocess, json
import psutil
import platform
import threading
from stray_icon_manager import StrayIconManager
from win32gui import GetWindowText, GetForegroundWindow

# Inserts app name in front of log
def name_logging(log):
    my_filename = __file__.split("/")[-1]
    logging.info(f"<{my_filename}> {log}")
""" 
To test this app, place MI_app.exe in C:/ location or change the location
--------------------------------------------------------------------
TODO: Look into MI_app name and path

TODO: Use in KITA - MI should not allow the app to be open more than once
TODO: Get icons working on Mac if possible
TODO: Compile with Nuitka and setup with Installer to add this app to os Startup folder
TODO: Make sure the Installer adds this app to os Startup folder (or Mac/Linux equivalent)
TODO: Replace methods in KITA that do not use self with @staticmethod
--------------------------------------------------------------------
"""
lock = threading.Lock()
VOSK_PATH = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "model", "vosk_english"))

class MIStartupListener:
    """
    Singleton class for MI_Monitor
    """
    _instance = None
    
    def __new__(cls): # Prevents multiple instantiations of the class
        if cls._instance is None:
            cls._instance = super(MIStartupListener, cls).__new__(cls)
            cls._queue = queue.Queue()
            device_info = sd.query_devices(kind='input')  # All available devices
            cls.samplerate = int(device_info['default_samplerate'])  # Selected device info
            cls._instance.model = vosk.Model(VOSK_PATH)
            name_logging("model created")
            cls._instance.recogniser = vosk.KaldiRecognizer(cls._instance.model,
                                                    cls.samplerate)  # Recogniser (Kaldi function which does the actual speech-to-text conversion)
            name_logging("recogniser started")
            cls.current_phrase = ""  # Current transcribed text
            cls._running = False
# TODO: Replace with 'start hands mode', 'start face mode'
            cls.trigger_phrase = "start" # used for testing
            cls.triggered_app = "MI_app.exe"
            cls.triggered_app_directory = 'C:\MI_app'
            cls.icon_manager = StrayIconManager()
            cls.previous_app_opened = ""
            cls.current_app_opened = ""

        else:
            name_logging("MIStartupListener: can only have one listener object - assigning to first object")
        return cls._instance

    def start(self):
        """
        START MI_Monitor app (main thread)
        """
        with lock:
            self._running = True
            self.icon_manager.start()

        name_logging("Listening...")
        print("Listening...")
        with sd.RawInputStream(samplerate=self.samplerate, blocksize=8000,\
            device=None, dtype='int16', channels=1, callback=self._callback): 

            # The Loop
            while self._running:
                self._vosk_action()

    @staticmethod
    def _active_process_names() -> list:
        """
        Return a list of the names of running processes 
        on Windows
        """
        return [p.info['name'] for p in psutil.process_iter(['name'])]

    def _triggered_app_process_info(self) -> tuple:
        """
        Return id, status tuple to check for 
        a zombie process.
        This is needed to close running app completely
        in close_MI_app() method
        """
        ppi = psutil.process_iter(['name', 'pid', 'status'])
        for p in ppi:
            if p.info['name'] == self.triggered_app:
                return p.info['pid'], p.info['status']
        return None, None 

    def focused_app(self):
        """
        Track current app on focus - Hotkeys
        """
        self.current_app_opened = GetWindowText(GetForegroundWindow())
        if self.current_app_opened != self.previous_app_opened:
            print("Window opened:",self.current_app_opened)
        self.previous_app_opened = self.current_app_opened


    def close_MI_app(self):
        while (self.triggered_app in self._active_process_names() and
                self._triggered_app_process_info()[1] != "zombie"):
            if random.random() > 0.99:
                name_logging(f"{self.triggered_app} still detected")
                name_logging(self._triggered_app_process_info())
        for p in psutil.process_iter():
            if self.triggered_app in str(p):
                p.kill()
                name_logging(f"Killed {self.triggered_app} {p.pid}")
        name_logging(f"{self.triggered_app} no longer in process list")

    def _vosk_action(self):
        """
        Run consistently while the app is open
        """
        self.focused_app()
        # Obtain recognised speaker's phrases
        try:
            json_data = self._get_current_phrase_dict()
        except Exception as e:
            name_logging(f"Exception {e} in _vosk_action()")
            sys.exit()
        for key, value in json_data.items(): 
            if key in ('partial', 'text'):
                self.current_phrase = value
        # If the speaker has said something
        if self.current_phrase != "":
            name_logging(f"heard: {self.current_phrase}")
            # If the speaker has said the trigger phrase
            if self.trigger_phrase in self.current_phrase:
                self.stop() # breaks the loop
                print(f"{self.current_phrase}")

                # Stops listening when MI app is open
                # Prevents multiple runs of MI_app.exe
                # TODO: Review whether this is good practice? 
                # Perhaps there is a more canonical way to achive this
                del self.recogniser
                name_logging("MI_Monitor recognition closed")

                # Run MI app
                self.open_MI_app() # Note, this command only STARTS 
                # the trigeering of the app, it may take a few seconds
                # for app to start fully. 
                
                while self.triggered_app not in self._active_process_names():
                    pass  # Wait until MI app runs
                name_logging(f"{self.triggered_app} app detected in process list")

                # Change icon to green once MI app is confirmed running
                self.icon_manager.green_icon_set()
                
# TODO: Delete this
                # By the time it gets to the second while loop it does not 
                # recognise that MI app is open, because it is in a process of 
                # opening but doesn't show up yet. So then new speech is generated
                # Which leads to opening the app multiple times if the phrase is said

                # Even though MI_app has been triggered, it may not yet
                # show in the process list in Windows (or be accesible from WMI)
                # So we now wait until it IS visible in the process list.
                # Otherwise the listener app might think MI_app
                # has ALREADY been closed and start up its listening for 
                # the trigger word again.

                # This is used because of a delay in Windows Task Processes 
                # to show that the app has opened and/or accounting for 
                # a delay of the MI app opening

                # Wait until MI_app.exe is in the process list
                # Kill the zombie process - close MI
                self.close_MI_app()

                # Change the icon to Red again
                self.icon_manager.red_icon_set()

                # recogniser.Reset() only prevents the first command from triggering
                # in order to prevent the app from opening multiple times
                # the recogniser gets deleted and then redefined
                # TODO: There might be a way to optimise this

                sys.stdin.flush()
                # Begins listening again when MI app is closed
                self.recogniser = vosk.KaldiRecognizer(self.model,
                                                      self.samplerate)  # Recogniser (Kaldi function which does the actual speech-to-text conversion)
                name_logging("Recogniser re-started")
                self.current_phrase = ""
                self._running = True
                name_logging("Startup Listener is running again")

    def _callback(self, indata, frames: int, time, status) -> None:
        """
        This is called (from a separate thread) for each audio block.
        It returns the microphone audio data
        """
        if status:
            print(status, file=sys.stderr)
            sys.stdout.flush()
        if self._running:
            self._queue.put(bytes(indata))

    def _get_current_phrase_dict(self):
        """
        Get current phrase from vosk
        """
        json_data = {}
        audio = self._queue.get()

        # Processes the wav (user speech) audio data; convert to text
        if self.recogniser.AcceptWaveform(audio): 
            # Get complete result
            # Vosk returns a json object by default {"Text", "user speech goes here"} 
            # TODO: What does FinalResult do?
            json_data = json.loads(self.recogniser.Result()) 
        else:
            # Get partial result
            json_data = json.loads(self.recogniser.PartialResult())
        return json_data

    def stop(self):
        """
        STOP == PAUSE
        """
        self._running = False

    def open_MI_app(self):
        """
        Open MI app
        """
        directory = self.triggered_app_directory
        cmdline = self.triggered_app

        # Check if the app is being ran on Mac or Windows
        machine_os = ''.join(platform.win32_ver())
        # If joined string is empty => the app is currently running on a Windows machine
        if machine_os != '':
            subprocess.Popen("start cmd /C" + cmdline, cwd = directory, shell=True)
            name_logging("Windows os detected")

        # Non-Windows (Currently Mac only)
        # TODO: The below will run for Mac but have not 
        # implemented all decision logic for other machines yet. 
        else:
            try:
                subprocess.Popen("./" + cmdline, cwd = directory, shell=True)
            except subprocess.CalledProcessError as e:
                print("There was an error. MI_Monitor not available for this machine yet", e.output)
        name_logging("Popen finished")


if __name__ == '__main__':
    # Empty logfile
    with open("MIStartupListener_log.txt","w") as f:
        pass
    # Set up logging
    # format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
    logging.basicConfig(filename="MIStartupListener_log.txt",
                        filemode='a',
                        format='%(asctime)s,%(msecs)d %(message)s',
                        datefmt='%H:%M:%S',
                        level=logging.DEBUG)
    """
    Instantiate class object
    """
    m = MIStartupListener()
    name_logging("Object Created")
    m.start()
    m.join()
    name_logging("Complete")

