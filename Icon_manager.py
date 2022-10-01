'''
Author: Anelia Gaydardzhieva
Comments: 
A separate thread to 
show/change/hide Windows system tray icon.

It keeps an icon in Windows system tray, 
which switches between red when MI app is closed 
and green when MI app is running.
Hovering over the icon show text 'UCL MotionInput - ON/OFF'
# Note: Clicking on the icon has no effect at the moment
and this can be implemented to do great things in the future :)

Note: pystray's Icon is required and it is a Thread
as well as this class is. Icon's stop() method can ONLY
be called from MainThread!
stop() enables the app to destroy an Icon object (end the Icon thread's loop) and
create a new one afterwards with a different colour. 
# TODO: There might be a way to optimise this and have a single 
Icon thread changing its image. 
Currently the tray updates when opened and if MI ran and closed multiple
times, it could showmultiple instances before clearing out to the most recent one.
'''
from threading import Thread

from PIL import Image
from pystray import Icon, MenuItem as item

# Adjustable global variables
RED_ICON = 'data//assets//red.ico'
GREEN_ICON = 'data//assets//green.ico'
TRAY_ICON_NAME = 'UCL MotionInput'


class IconManager(Thread):
    """ System Tray Icon Manager """

    def __init__(self):
        super().__init__()
        self.name = "Icon Manager Thread"
        self.daemon = True
        self._is_running = False
        self.icon = None
        self.icon_title = ""
        self.current_icon = ""
        self.icon_flag = False # Red Icon
        self.start()


    def run(self) -> None:
        """
        Main loop for displaying the icon
        """
        self._is_running = True
        while self.is_running:
            self._icon_action()
        self._stop()


    def _icon_action(self) -> None:
        """
        Main Icon activity
        Setting up the icon
        """
        if not self.icon_flag:
            self.current_icon = RED_ICON
            self.icon_title = TRAY_ICON_NAME + " - OFF"
            print("Red Icon")
        else:
            self.current_icon = GREEN_ICON
            self.icon_title = TRAY_ICON_NAME + " - ON"
            print("Green Icon")
        # setup system tray icon
        image = Image.open(self.current_icon)
        icon_stop = (item('Quit', self.stop_icon),)
        self.icon = Icon("name", image, self.icon_title, icon_stop)
        self.icon.run() # start icon thread


    def stop_icon(self) -> None:
        self.icon.visible = False
        self.icon.stop()


    def green_icon_set(self) -> None:
        """
        Trigger Icon change to Green
        """
        # TODO: Consider implementing # self.icon.update_menu() 
        self.stop_icon()
        self.icon_flag = True


    def red_icon_set(self) -> None:
        """
        Trigger Icon change to Red
        """
        self.stop_icon()
        self.icon_flag = False


    def is_running(self) -> bool:
        """
        Returns True is the IconManager is running
        """
        return self._is_running


    def _stop(self) -> None:
        """
        Stops the IconManager thread
        """
        self.stop_icon()
        self._is_running = False