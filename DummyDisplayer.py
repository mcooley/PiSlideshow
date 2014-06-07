# Substitute for the pi3d-based display functionality to enable testing while not on a Pi.
# This just prints filenames to stdout for now.
# In ssRunner, you can comment out the import for Pi3DDisplayer and replace it with an import from DummyDisplayer.

import time, config

class Slide:
	def __init__(self, filename):
		self.filename = filename

	def startFadeIn(self):
		print('Fading in ' + self.filename)

	def startFadeOut(self):
		print('Fading out ' + self.filename)

def displayLoop(slideQueue):
    curSlide = Slide("/family photos/christmas years/2005 christmas pix.jpg") #TODO: find a better way to prime the sequence
    nextSlide = Slide("/family photos/christmas years/2005 christmas pix.jpg")

    curSlide.startFadeOut()
    nextSlide.startFadeIn()

    lastTransitionStart = time.time()

    while True:
        if (time.time() - lastTransitionStart) >= config.HOLD_TIME and not slideQueue.empty():
            lastTransitionStart = time.time()
            curSlide = nextSlide
            nextSlide = slideQueue.get()
            curSlide.startFadeOut()
            nextSlide.startFadeIn()
