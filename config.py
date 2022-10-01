'''
Author: Anelia Gaydardzhieva
Comments:
A class to get information from the config.json
Adapted from MotionInput
#TODO: Could optimise and introduce improved data validations 
with @dataclass-es or, even better, pydantic library.
'''
import os
import json
from typing import Dict, List


def check_paths(*paths):
    """
    Multipath checks
    """
    for path in paths:
        if not os.path.exists(path):
            raise FileNotFoundError(f"[MI_Monitor] Path {path} - was not found")

DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "data"))


class Config:
    """ Class to manage the JSON app configurations """

    def __init__(self, json_name: str = "config.json"):
        """
        Passing a "config.json" (json file name)
        """
        self.json_path = DATA_PATH + "\\" + json_name
        check_paths(self.json_path)
        self.data = self.set_config_data()
        print("DATA: ", self.data)
        self.current_mode = self.data["current_mode"]
        self.vosk_model_name = self.data["model"]
        print("CURRENT_MODE: ", self.current_mode)
        self.mode_data = self.data["modes"][self.current_mode]
        self.mi_exe = self.mode_data["mi_exe"]


    def get_mi_exe(self) -> str:
        """
        Returns only MI exe name
        """
        return self.mi_exe


    def get_trigger_phrases(self, action : str) -> List[str]:
        """
        Returns all allowed start trigger phrases
        """
        temp_phrases = self.mode_data["trigger_phrases"]
        if action == "start":
            trigger_phrases = ["start " + phrase for phrase in temp_phrases]
            return trigger_phrases # start
        temp_stop = ["stop " + phrase for phrase in temp_phrases]
        temp_close = ["close " + phrase for phrase in temp_phrases]
        trigger_phrases = temp_stop + temp_close
        return trigger_phrases # stop


    def get_bat_path(self, specification : str) -> str:
        """
        Returns the requested bat file path
        for the mode
        """
        prefix = "exit_"
        if specification == "forced":
            prefix = "forced_exit_"
        return prefix + self.current_mode + ".bat"


    def get_bat_folder_path(self):
        """
        """
        return os.path.join(DATA_PATH, "bats")


    def get_mi_folder_path(self) -> str:
        """
        Returns MI exe folder path
        """
        return os.path.join(DATA_PATH, "..", "..", self.mode_data["mi_folder"])


    def set_config_data(self) -> Dict[str, str]:
        """
        Reads the JSON data
        """
        with open(self.json_path, "r") as f:
            data = json.load(f)
        return data


    def get_file_data(self) -> Dict[str, str]:
        """
        Grabs the whole dict from JSON file
        """
        return self.data


    def get_vosk_path(self) -> str:
        """
        Vosk Path
        """
        return os.path.join(DATA_PATH, 'models', self.vosk_model_name)
