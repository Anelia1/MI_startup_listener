'''
Author: Anelia Gaydardzhieva
Comments: A separate thread to 
show/change/hide Windows system tray icon.

It keep an icon in Windows system tray, 
which shows red when MI app is closed 
and green when MI app is running.
# Note: Clicking on the icon has no effect at the moment
and this can be implemented to do great things in the future :)

Note: pystray's Icon is required and it is a Thread
as well as this class is. Icon's stop() method however can ONLY
be called from MainThread!

# TODO: The Icon refresh/update happens only when the systemtray
is opened, which is an unpleasant inconvenience that requires fixing!
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
        Thread.__init__(self)
        self.name = "Icon Manager Thread"
        self.daemon = True
        self._instance = None
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

    def _icon_action(self):
        try:
            if not self.icon_flag:
                self.current_icon = RED_ICON
                self.icon_name = TRAY_ICON_NAME + " - OFF"
                print("Red Icon")
            elif self.icon_flag:
                self.current_icon = GREEN_ICON
                self.icon_name = TRAY_ICON_NAME + " - ON"
                print("Green Icon")
            image = Image.open(self.current_icon)
            icon_stop = (item('Quit', self.stop_icon),)
            self.icon = pystray.Icon("name", image, self.icon_name, icon_stop)
            self.icon.run()
        except Exception as e:
            print(e)
            self._stop()
            
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