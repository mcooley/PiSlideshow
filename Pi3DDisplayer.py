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
                nextSlide = Pi3dSlide(slideQueue.get(), self.display, self.shader)
                curSlide.startFadeOut()
                nextSlide.startFadeIn()

            curSlide.draw()
            nextSlide.draw()

    def __del__(self):
        self.display.destroy()

# A pi3d texture which takes a PIL image directly instead of loading from disk.
class MemTexture(pi3d.Texture):
  def __init__(self, image, blend=False, flip=False, size=0, defer=True, mipmap=True):
    super(MemTexture, self).__init__('', blend=blend, flip=flip, size=size, defer=defer, mipmap=mipmap)
    self.memImage = image

  def _load_disk(self):
    from pi3d.Texture import MAX_SIZE
    from pi3d.Texture import WIDTHS
    import ctypes

    im = self.memImage

    self.ix, self.iy = im.size
    self.alpha = (im.mode == 'RGBA' or im.mode == 'LA')

    if self.mipmap:
      resize_type = Image.BICUBIC
    else:
      resize_type = Image.NEAREST

    # work out if sizes > MAX_SIZE or coerce to golden values in WIDTHS
    if self.iy > self.ix and self.iy > MAX_SIZE: # fairly rare circumstance
      im = im.resize((int((MAX_SIZE * self.ix) / self.iy), MAX_SIZE))
      self.ix, self.iy = im.size
    n = len(WIDTHS)
    for i in xrange(n-1, 0, -1):
      if self.ix == WIDTHS[i]:
        break # no need to resize as already a golden size
      if self.ix > WIDTHS[i]:
        im = im.resize((WIDTHS[i-1], int((WIDTHS[i-1] * self.iy) / self.ix)),
                        resize_type)
        self.ix, self.iy = im.size
        break

    if self.flip:
      im = im.transpose(Image.FLIP_TOP_BOTTOM)

    RGBs = 'RGBA' if self.alpha else 'RGB'
    self.image = im.convert(RGBs).tostring('raw', RGBs)
    self._tex = ctypes.c_int()


class LoadingSlide(Pi3dSlide):
    def __init__(self, display, shader):
        super(Slide, self).__init__(display, shader)

        self.loadTexture(pi3d.Texture(os.path.dirname(os.path.realpath(__file__)) + '/Loading.jpg', blend=True, mipmap=True))


class ImageSlide(Pi3dSlide):
    def __init__(self, image, display, shader):
        super(Slide, self).__init__(display, shader)

        self.loadTexture(MemTexture(image, blend=True, mipmap=True))


class Pi3dSlide(pi3d.Canvas):
    def __init__(self, image, display, shader):
        super(Slide, self).__init__()
        self.fadeDirectionUp = True
        self.isAnimating = False

        self.set_shader(shader)

        self.set_alpha(0)

    def loadTexture(self, texture):
        xrat = display.width/texture.ix
        yrat = display.height/texture.iy
        if yrat < xrat:
            xrat = yrat
        wi, hi = texture.ix * xrat, texture.iy * xrat
        xi = (display.width - wi)/2
        yi = (display.height - hi)/2
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
            self.set_alpha(newAlpha)
            if newAlpha >= 1.0 or newAlpha <= 0.0:
                self.isAnimating = False
    