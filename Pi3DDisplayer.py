from __future__ import absolute_import, division, print_function, unicode_literals

import pi3d, time, os, sys, ctypes, config
from PIL import Image

class Displayer:
    def __init__(self, slideQueue):
        self.slideQueue = slideQueue

        # Setup display and initialise pi3d
        self.display = pi3d.Display.create(background=(0.0, 0.0, 0.0, 1.0), frames_per_second=20)
        self.shader = pi3d.Shader("2d_flat")

    def run(self):
        camera = pi3d.Camera.instance()
        camera.was_moved = False #to save a tiny bit of work each loop

        curSlide = LoadingSlide(self.display, self.shader);
        nextSlide = LoadingSlide(self.display, self.shader);

        nextSlide.set_alpha(1.0)
        curSlide.startFadeOut()
        nextSlide.startFadeIn()

        while self.display.loop_running():
            if curSlide.isAnimating or nextSlide.isAnimating:
                nextSlide.step()
                curSlide.step()

            if not self.slideQueue.empty():
                curSlide = nextSlide
                nextSlide = ImageSlide(self.slideQueue.get()['image'], self.display, self.shader)
                lastTransitionStart = time.time()
                curSlide.startFadeOut()
                nextSlide.startFadeIn()

            nextSlide.draw()
            curSlide.draw()

    def __del__(self):
        self.display.destroy()

class Pi3dSlide(pi3d.Canvas):
    def __init__(self, display, shader):
        super(Pi3dSlide, self).__init__()
        self.fadeDirectionUp = True
        self.isAnimating = False

        self.display = display
        self.set_shader(shader)

        self.set_alpha(0)

    def loadTexture(self, texture):
        xrat = self.display.width/texture.ix
        yrat = self.display.height/texture.iy
        if yrat < xrat:
            xrat = yrat
        wi, hi = texture.ix * xrat, texture.iy * xrat
        xi = (self.display.width - wi)/2
        yi = (self.display.height - hi)/2
        self.set_texture(texture)
        self.set_2d_size(w=wi, h=hi, x=xi, y=yi)

    def startFadeIn(self):
        self.positionZ(0.5)
        self.fadeDirectionUp = True
        self.isAnimating = True

    def startFadeOut(self):
        self.positionZ(0.6)
        self.fadeDirectionUp = False
        self.isAnimating = True

    def step(self):
        if self.isAnimating:
            if self.fadeDirectionUp:
                newAlpha = self.alpha() + config.ALPHA_STEP
            else:
                newAlpha = self.alpha() - config.ALPHA_STEP

            if newAlpha >= 1.0:
                self.set_alpha(1.0)
                self.isAnimating = False
            elif newAlpha <= 0.0:
                self.set_alpha(0.0)
                self.isAnimating = False
            else:
                self.set_alpha(newAlpha)

class LoadingSlide(Pi3dSlide):
    def __init__(self, display, shader):
        super(LoadingSlide, self).__init__(display, shader)

        self.loadTexture(pi3d.Texture(os.path.dirname(os.path.realpath(__file__)) + '/Loading.jpg', blend=True, mipmap=True))


class ImageSlide(Pi3dSlide):
    def __init__(self, image, display, shader):
        super(ImageSlide, self).__init__(display, shader)

        self.loadTexture(pi3d.Texture(image, blend=True, mipmap=True, defer=False))
    