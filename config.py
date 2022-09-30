'''
Author: Anelia Gaydardzhieva
Comments:
Adapted from MotionInput
'''
import os
import json
from typing import Optional

def check_paths(*paths):
    """
    Multipath checks
    """
    for path in paths:
        if not os.path.exists(path):
            raise FileNotFoundError(f"[MI_Monitor] Path {path} - was not found")

DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "data"))



# Bats
BATS_FOLDER_PATH = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "bats"))
EXIT_BAT = os.path.join(BATS_FOLDER_PATH, BAT_EXIT)
FORCED_EXIT_BAT = os.path.join(BATS_FOLDER_PATH, BAT_FORCED_EXIT)



class Config:
    """ Class to manage the JSON app configurations """

    def __init__(self, json_name: str = "config.json"):
        """
        Passing a "config.json" (json file name)
        """
        self.json_path = DATA_PATH + "\\" + json_name
        check_paths(self.json_path)
        self.data = self.set_config_data()
        self.current_mode = self.data["current_mode"]
        self.mode_data = self.get_mode_data()


    def get_mi_folder(self):
        """
        Returns only the exe name
        """
        return self.mode_data[mi_folder]


    def get_mi_exe(self):
        """
        Returns only the exe name
        """
        return self.mode_data[mi_exe]


    def get_trigger_phrases(self, action : str) -> List[str]:
        """
        Returns all allowed start trigger phrases
        """
        if action == "start":
            trigger_phrases = ["start " + phrase for phrase in temp_phrases]
            return trigger_phrases # start
        temp_phrases = self.mode_data["trigger_phrases"]
        temp_stop = ["stop " + phrase for phrase in temp_phrases]
        temp_close = ["close " + phrase for phrase in temp_phrases]
        trigger_phrases = temp_stop + temp_close
        return trigger_phrases # stop


    def get_bat_path(self, Optional[forced] : str) -> str:
        """
        Returns the requested bat file path
        for the mode
        """
        prefix = "exit_"
        if forced:
            prefix = "forced_exit_"
        return prefix + self.current_mode + ".bat"


    def get_mi_exe_path(self):
        """
        Returns the executable to be managed path
        """
        return os.path.join(DATA_PATH, "..", "..", self.mode_data["mi_exe_path"])


    def set_config_data(self) -> Dict[str : Any]:
        """
        Reads the JSON data
        """
        with open(self.json_path, "r") as f:
            data = json.load(f)
        return data


    def get_mode_data(self) -> Dict[str, Any]:
        """
        Grabs the current mode data
        """
        return self.data[self.current_mode]


    def get_file_data(self) -> Dict[str, Any]:
        """
        Grabs the whole dict from JSON file
        """
        return self.data


    def get_vosk_path(self):
        """
        Vosk Path
        """
        return os.path.join(DATA_PATH, 'models', self.get_data("vosk_model"))
