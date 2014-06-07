from __future__ import absolute_import, division, print_function, unicode_literals

# Substitute for the pi3d-based display functionality to enable testing while not on a Pi.
# This just prints to stdout for now.
# In ssRunner, you can comment out the import for Pi3DDisplayer and replace it with an import from DummyDisplayer.

import time, config


class Displayer:
    def __init__(self, slideQueue):
        self.slideQueue = slideQueue

    def run(self):
        while True:
            if not self.slideQueue.empty():
            	self.slideQueue.get()
            	print('Switching slides!')
