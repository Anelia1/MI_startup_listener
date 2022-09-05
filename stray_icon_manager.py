"""
Author: Anelia Gaydardzhieva
Comments: A separate thread 
to show/change/hide Windows system tray icon
"""
import threading
import logging
from pystray import MenuItem as item
import pystray # cross-platform
from PIL import Image

# Inserts app name in front of log
def name_logging(log):
    my_filename = __file__.split("/")[-1]
    logging.info(f"<{my_filename}> {log}")

class StrayIconManager(threading.Thread): # Maybe remove, or not
    running = False
# TODO: Explain thread extention

    def __init__(self):
        super(StrayIconManager, self).__init__()
        self.running = False
        self._event = threading.Event()
        self.icon = None
        self.icon_name = ""
        self.current_icon = ""
        self.icon_flag = False # Red Icon

    def run(self):
        """
        Main loop for displaying the icon
        """
        self.running = True
        while self.running:
            if not self._event.is_set:
                self._event.wait()
            self._icon_action()

    def _icon_action(self):
        if not self.icon_flag:
            self.current_icon = "red.ico"
            self.icon_name = "MotionInput OFF"
            print("Red Icon")
        elif self.icon_flag:
            self.current_icon = "green.ico"
            self.icon_name = "MotionInput ON"
            print("Green Icon")
        image = Image.open(self.current_icon)
        icon_stop = (item('Quit', self.stop_icon),)
        self.icon = pystray.Icon("name", image, self.icon_name, icon_stop)
        self.icon.run()
            
    def stop_icon(self):
        self.icon.stop()

    def green_icon_set(self):
        """
        Trigger Icon change to Green
        """
        # TODO: Use for optimisation
        # self.icon.update_menu()

        self.stop_icon()
        self.icon_flag = True
        self._event.set()

    def red_icon_set(self):
        """
        Trigger Icon change to Red
        """
        self.stop_icon()
        self.icon_flag = False
        self._event.clear()

    def is_running(self):
        return self.running
