#!/usr/bin/env python
from __future__ import absolute_import, division, print_function, unicode_literals

import threading

from SlideshowController import SlideshowController
#from Pi3DDisplayer import Displayer
from DummyDisplayer import Displayer

controller = SlideshowController();
displayer = Displayer(controller.showQueue);

# Run the controller, which controls the slide loading and transition timing.
controllerThread = threading.Thread(target=controller.run)
controllerThread.daemon = True
controllerThread.start();

# Finally, in this thread run the display loop.
displayer.run();