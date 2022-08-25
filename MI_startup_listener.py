import queue
import sounddevice as sd
import vosk
vosk.SetLogLevel(-1)
import os, sys, subprocess, json
import wmi # used to check if MI app is open 
import psutil

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
# TODO: Cross platform - account for MAC and maybe Linux
# TODO: Ensure PERSISTENCE - deamon threads? - run as a service?

# TODO: Compile with Nuitka and setup with Installer to add this app to os Startup folder
# TODO: Use Installer (there are free open source ones) to add this app to os Startup folder
# TODO: Make sure the Installer adds this app to os Startup folder (or Mac/Linux equivalent)
# TODO: It should never ever close
# TODO: Look into MI_app name and path
# # TODO: REPLACE model HACK with communicating threads (maybe condition object)
#### --------------------------------------------------------------------

VOSK_PATH = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "model", "vosk_english"))

class MIStartupListener:
    
    def __init__(self):
        self._queue = queue.Queue()
        device_info = sd.query_devices(kind='input') # All available devices
        self.samplerate = int(device_info['default_samplerate']) # Selected device info
        self.model = vosk.Model(VOSK_PATH) # Speech recognition model
        self.recogniser = vosk.KaldiRecognizer(self.model, self.samplerate) # Recogniser (Kaldi function which does the actual speech-to-text conversion)
        self.current_phrase = "" # Current transcribed text 
        self._running = False
        #self.trigger_phrase = "start application now" 
        self.trigger_phrase = "start" # used for testing

    def start(self):
        self._running = True

        with sd.RawInputStream(samplerate=self.samplerate, blocksize=8000,\
            device=None, dtype='int16', channels=1, callback=self._callback): 

            # The Loop
            while self._running:
                self._vosk_action()


    def _vosk_action(self):
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
                self.stop() # breaks the loop

                # Stops listening when MI app is open
                # These are unnecessary while MI app is running
                # TODO: Review whether this is good practice? Maybe there is a more canonical way to achive this
                self.model = None # clear out vosk model
                self.recogniser = None # clear out vosk recogniser
                
                print("Startup Listener is closed")
                # Runs MI app
                self.open_MI_app() #Note, this command only STARTS the trigeering of the app, it may take a few seconds for app to start fully. 
                # 
                print("MI app triggered")

                wmi_tasks = wmi.WMI() # This only works for windows
                
                # TODO: Delete this
                # By the time it gets to the second while loop it does not recognise that
                # MI app is open, because it is in a process of opening but doesn't show up yet
                # So then new speech is generated
                # Which leads to opening the app multiple times if the phrase is said


                # Even though MI_app has been triggered, it may not yet
                # show in the process list in Windows (or be accesible from WMI)
                # So we now wait until it IS visible in the process list.
                # (if you don't wait and do this, then the listener app might think MI_app
                # has ALREADY been closed and start up its listening for the trigger word again!

                # This is used because of a delay in Windows Task Processes to show that the app has opened 
                # and/or accounting for a delay of the MI app opening
                while True not in ("MI_app" in p_str for p_str in (str(p) for p in wmi_tasks.Win32_Process())):
                    pass # wait until MI app opens
                print("MI app app opened")
  
                # Wait until MI_app.exe is in the process list
                # If MI app NOT opened
                while True in ("MI_app" in p_str for p_str in (str(p) for p in wmi_tasks.Win32_Process())):
                    pass  # wait until MI app sloses
 
                print("MI app closed")

                # Begins listening again when MI app is closed
                self.model = vosk.Model(VOSK_PATH) # restore vosk model
                self.recogniser = vosk.KaldiRecognizer(self.model, self.samplerate) # restore vosk recogniser
                
                # Starts the loop again
                self.start() 
                print("Startup Listener started again")
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
        # Pause while MI app is open
        if not self._running:
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

    def stop(self):
        """
        STOP == PAUSE
        """
        self._running = False

    @staticmethod
    def open_MI_app():
        """
        Open MI app
        """
        directory = 'C:\MI_app'
        cmdline = "MI_app.exe"
        subprocess.call("start cmd /C " + cmdline, cwd=directory, shell=True)


"""
Instantiate class object
"""
m = MIStartupListener()
m.start()
input("Waiting...")


