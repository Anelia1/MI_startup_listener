'''
Author: Anelia Gaydardzhieva
Comments: 
MI Tracker manages the MI app process condition.
It runs commands directed by MIMonitor to open/close MI app.

Note: The global variables are used to define 
the app of interest
'''
import json
import os
import psutil
import subprocess
from datetime import datetime
from threading import Thread, Event, Lock
from prettytable import PrettyTable

GLOBAL_EVENT = Event()

#DOING_JSON_WORK = False

def check_paths(*paths):
    for path in paths:
        if not os.path.exists(path):
            raise FileNotFoundError(f"[MI_Monitor] Path {path} was not found")

MI_FOLDER = "MI_app"
MI_EXE = MI_FOLDER + ".exe"

MI_FOLDER_PATH = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", MI_FOLDER))
MI_EXE_PATH = os.path.join(MI_FOLDER_PATH, MI_EXE)
check_paths(MI_FOLDER_PATH, MI_EXE_PATH)

lock = Lock()


class MITracker(Thread):
    """
    MITracker
    """

    def __init__(self):
        Thread.__init__(self)
        self.name = "Tracker Thread"
        self.daemon = True
        self.report = f"MI closed because of: "
        self._instance = None
        self._is_running = False
        self.process_name = "MI_app"
        self.start()

    def run(self):
        """
        Main loop 
        """
        with lock:
            self._is_running = True
        while self.is_running():

            GLOBAL_EVENT.wait()

            #print("----")
            data = {}
            try:
                data = self.get_data()

            except Exception as e:
                print("MITracker.run(): GENERAL ERROR: ", e)
                raise
                self._stop()

            if data:
                try:

                    if data['start_phrase'] == "true":
                        self.do_on_start_phrase()

                except Exception as e:

                    print("MITracker.run(): ", e)
                    raise
                    self._stop()

                try:

                    if data['stop_phrase'] == "true":
                        self.do_on_stop_phrase()

                except Exception as e:
                
                    print("MITracker.run(): ", e)
                    raise
                    self._stop()


    @staticmethod
    def get_data():
        data = {}
        try:
            with lock:
            #with open('info.json', 'r') as js:
                #data = json.load(js)
                #print("Data before: ", data)
                #data = data["info"]
                #print("Data after: ", data)
                #print("start_phrase bool ::::: ", data['start_phrase'])
                #print("stop_phrase bool ::::: ", data['stop_phrase'])
                #return data
                data = json.loads(open('info.json').read())
                return data
        except ValueError as ev:
            print("MITracker.get_data(): ValuError: ", ev)
            raise
        except Exception as e:
            print("MITracker.run(): General exception: ", e)
            raise



    def restart_MI(self):
        self.do_on_stop_phrase()
        self.do_on_start_phrase()


    def do_on_start_phrase(self):
        """
        Method to start MI
        """
        try:
            MI_instance = self._MI_process_info()
            if MI_instance:
                self.kill_MI() # to make sure
                print("KILLED MI")
        except Exception as e:
            print("MITracker.do_on_start_phrase(): get process instance and kill MI", e)
            raise

        ## Windows
        #if sys.platform == "win32":
        #    print("Starting MI now...")
        try: 
            subprocess.Popen("start cmd /C" + MI_EXE, cwd = MI_FOLDER_PATH, shell=True)
            print("STARTED MI")
        except Exception as e:
            print("MITracker.do_on_start_phrase(): subprocess issue", e)
            raise
        ## MacOS
        #elif sys.platform == "darwin":
        #    subprocess.Popen("./" + MI_EXE, cwd = MI_FOLDER, shell=True)
        MI_instance = self._MI_process_info()
        while not MI_instance:
            pass # Wait until MI_app.exe is in the process list (has started)
        print(f"{MI_EXE} app detected in process list") # MI app is confirmed running
        self.reset_info_file()


    def do_on_stop_phrase(self):
        """
        Method to close MI
        """
        print("On stop phrase, Process_Name: ", self.process_name)
        self.kill_MI()
        self.reset_info_file()


    @staticmethod
    def reset_info_file():
        with lock:
            try: 
                d = {"start_phrase": "false","stop_phrase": "false"}
                json.dump(d, open('info.json', 'w'))
            except Exception as e:
                print("MITracker.reset_info_file(): json issue: ", e)
                raise


    def do_on_restart_phrase(self):
        """
        Method to restart MI
        """
        self.restart_MI()


    def kill_MI(self):
        try:
            MI_instance = self._MI_process_info()
            if MI_instance:
                print(MI_instance)
                print("Killing MI now...")
                subprocess.Popen("TASKKILL /IM " + self.process_name)

                #for p in psutil.process_iter():
                #    if MI_EXE in str(p) and p.info(['pid']!=os.getpid()): # no suidides!
                #        p.kill()
                print(f"Killed {MI_EXE}")
        except subprocess.SubprocessError as es:
            print("MITracker.kill_MI(): subprocess error: ", es)
            raise
        except Exception as e:
            print("MITracker.kill_MI(): general error: ", e)
            raise

    def _MI_process_info(self):
        MI_instance = []
        try:
            output = subprocess.check_output(["wmic", "process", "list", "full", "/format:list"])
            output = output.decode("utf-8") # binary
        except Exception as e:
            print("ERROR <MI_process_info> subprocess.check_output: ", e)
            raise
        output_list = []
        try:
            for task in output.strip().split("\r\r\n\r\r\n"):
                output_list.append(dict(e.split("=", 1) for e in task.strip().split("\r\r\n")))
            for process in output_list:
                if process['Name'].startswith('UCL') or process['Name'].startswith('MI'):
                    MI_instance.append(process)
                    self.process_name = process['Name']
                    #print(process)
        except Exception as ex:
            print("ERROR <MI_process_info> strip(), append(), process_name: ", ex)
            raise
        return MI_instance


    def _stop(self):
        """
        STOP 
        """
        self.do_on_stop_phrase()
        self._is_running = False


    def is_running(self):
        return self._is_running






    ########################## Static methods to make use of ###############################


    @staticmethod
    def system_info_table():
        """
        Method for visual display of system information
        Not actively used at the moment but has great potential
        (if we do not require fast outputs because psutil is much slower)
        """
        process_table = PrettyTable(['PID', 'PNAME', 'STATUS', 'NUM_THREADS', 'MEMORY(MB)'])
        try:
            for p in psutil.process_iter():
                # oneshot is very fast
                with p.oneshot():
                    process_table.add_row([
                        str(p.pid),
                        p.name(),
                        p.status(),
                        p.num_threads(),
                        f'{p.memory_info().rss / 1e6:.3f}'
                        ])
                    print(process_table)
        except Exception as e:
            print(e)


    @staticmethod
    def time_MI_process_created():
        """
        Formatted date and time for MI exe trigger
        Not actively used at the moment (added to todo list:)
        """
        p = psutil.Process
        for p in psutil.process_iter():
            if "MI_app" in p.info['name']:
                p_time = p.create_time()
                formatted_time = datetime.datetime.fromtimetostamp(p_time).strftime("%Y-%m-%d %H:%M:%S")
                print("MI executed on: ", formatted_time)


    @staticmethod
    def _active_processes_names() -> list:
        """
        Return a list of the names of running processes 
        on Windows
        """
        return [p.info['name'] for p in psutil.process_iter(['pid', 'name', 'status'])]


    ########################################################################################
