import queue
import threading
import logging
from pystray import MenuItem as item
import pystray # cross-platform
from PIL import Image, ImageTk
import time

def name_logging(log):
    my_filename = __file__.split("/")[-1]
    logging.info(f"<{my_filename}> {log}")

lock = threading.Lock()

class StrayIconManager(threading.Thread):
    running = False
    _current_icon = ""
    _icon_name = ""
    icon_flag = False
    icon = None
    # _instance # __new__(cls)
    # ? Explain thread extention
    # Remove class variables

    def __init__(self):
        super(StrayIconManager, self).__init__()
        self._event = threading.Event()
        #self.trigger_event()


    def run(self):
        StrayIconManager.running = True
        
        
        StrayIconManager._current_icon = "red.ico"
        
        while StrayIconManager.running:
            #time.sleep(5)
            #while not self._event.is_set:
            if not self._event.is_set:
                self._event.wait()
            self._icon_action()
            #StrayIconManager.icon.stop()


    def _icon_action(self):
        
        if not StrayIconManager.icon_flag:
            StrayIconManager._current_icon = "red.ico"
            StrayIconManager._icon_name = "MotionInput OFF"
            print("Red icon")
        elif StrayIconManager.icon_flag:
            StrayIconManager._current_icon = "green.ico"
            StrayIconManager._icon_name = "MotionInput ON"
            print("Green icon")


        image=Image.open(StrayIconManager._current_icon)
        icon_stop=(item('Quit', self.hide_icon),)
        StrayIconManager.icon=pystray.Icon("name", image, StrayIconManager._icon_name, icon_stop)
        print("Setting up Icon")
        StrayIconManager.icon.run()
        print("Stopping Icon")
            
    @staticmethod
    def hide_icon():
        StrayIconManager.icon.stop()

    def trigger_event(self):
        if not self._event.is_set:
            self._event.set()
        #StrayIconManager.running = False

    def reset(self):
        #StrayIconManager.running = False
        self.hide_icon()
        #if not self._event.is_set:
        if not self._event.is_set:
            self._event.clear()
            self.trigger_event()


    def is_running(self):
        return self._event.is_set()

#sil = StrayIconManager()
#sil.start()
#sil.join()