'''
Author: Anelia Gaydardzhieva
Comments: A separate thread to 
show/change/hide Windows system tray icon.

It keeps an icon in Windows system tray, 
which switches between red when MI app is closed 
and green when MI app is running.
Hovering over the icon show text 'UCL MotionInput - ON/OFF'
# Note: Clicking on the icon has no effect at the moment
and this can be implemented to do great things in the future :)

Note: pystray's Icon is required and it is a Thread
as well as this class is. Icon's stop() method however can ONLY
be called from MainThread!
stop() enables the app to distroy an icon object and
create a new one afterwards with a different colour. 
'''
from pystray import MenuItem as item
import pystray # cross-platform
from PIL import Image
from threading import Thread, Lock


RED_ICON = 'assets//red.ico'
GREEN_ICON = 'assets//green.ico'
TRAY_ICON_NAME = 'UCL MotionInput'


lock = Lock()

class IconManager(Thread):
    """ System Tray Icons Manager """

    def __init__(self):
        super().__init__()
        self.name = "Icon Manager Thread"
        self.daemon = True
        self._is_running = False
        self.icon = None
        self.icon_name = ""
        self.current_icon = ""
        self.icon_flag = False # Red Icon
        self.start()

    def run(self):
        """
        Main loop for displaying the icon
        """
        self._is_running = True
        while self.is_running:
            self._icon_action()
        self._stop()

    def _icon_action(self):
        try:
            if not self.icon_flag:
                self.current_icon = RED_ICON
                self.icon_name = TRAY_ICON_NAME + " - OFF"
                print("Red Icon")
            else:
                self.current_icon = GREEN_ICON
                self.icon_name = TRAY_ICON_NAME + " - ON"
                print("Green Icon")
            # setup system tray icon
            image = Image.open(self.current_icon)
            icon_stop = (item('Quit', self.stop_icon),)
            self.icon = pystray.Icon("name", image, self.icon_name, icon_stop)
            self.icon.run() # start icon thread
        except Exception as e:
            print(e)
            
            
    def stop_icon(self):
        try:
            self.icon.stop()
        except Exception as e:
            print(e)

    def green_icon_set(self):
        """
        Trigger Icon change to Green
        """
        # TODO: Consider implementing # self.icon.update_menu() 
        self.stop_icon()
        self.icon_flag = True

    def red_icon_set(self):
        """
        Trigger Icon change to Red
        """
        self.stop_icon()
        self.icon_flag = False

    def is_running(self):
        return self._is_running

    def _stop(self):
        self.stop_icon()
        self._is_running = False