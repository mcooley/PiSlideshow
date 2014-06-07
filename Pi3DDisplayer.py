import pi3d, time, config

# Setup display and initialise pi3d
DISPLAY = pi3d.Display.create(background=(0.0, 0.0, 0.0, 1.0), frames_per_second=20)
SHADER = pi3d.Shader("2d_flat")

class Slide(pi3d.Canvas):
  def __init__(self, filename):
    super(Slide, self).__init__()
    self.fadeDirectionUp = True
    self.isAnimating = False

    self.set_shader(SHADER)

    tex = DropboxImage(filename, blend=True, mipmap=True)
    xrat = DISPLAY.width/tex.ix
    yrat = DISPLAY.height/tex.iy
    if yrat < xrat:
      xrat = yrat
    wi, hi = tex.ix * xrat, tex.iy * xrat
    xi = (DISPLAY.width - wi)/2
    yi = (DISPLAY.height - hi)/2
    self.set_texture(tex)
    self.set_2d_size(w=wi, h=hi, x=xi, y=yi)
    self.set_alpha(0)

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

class DropboxImage(pi3d.Texture):
  def _load_disk(self):
    from PIL import Image
    from pi3d.Texture import MAX_SIZE
    from pi3d.Texture import WIDTHS
    VERBOSE = False
    import ctypes

    s = self.file_string + ' '
    im = Image.open(cStringIO.StringIO(sync.getFile(self.file_string)))

    self.ix, self.iy = im.size
    s += '(%s)' % im.mode
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

    if VERBOSE:
      print('Loading ...{}'.format(s))

    if self.flip:
      im = im.transpose(Image.FLIP_TOP_BOTTOM)

    RGBs = 'RGBA' if self.alpha else 'RGB'
    self.image = im.convert(RGBs).tostring('raw', RGBs)
    self._tex = ctypes.c_int()

def displayLoop(slideQueue):

    # Fetch key presses (kills logging to stdout!)
    #mykeys = pi3d.Keyboard()

    CAMERA = pi3d.Camera.instance()
    CAMERA.was_moved = False #to save a tiny bit of work each loop

    curSlide = Slide("/family photos/christmas years/2005 christmas pix.jpg") #TODO: find a better way to prime the sequence
    nextSlide = Slide("/family photos/christmas years/2005 christmas pix.jpg")

    nextSlide.set_alpha(1.0)
    curSlide.startFadeOut()
    nextSlide.startFadeIn()

    lastTransitionStart = time.time()

    while DISPLAY.loop_running():
        #k = mykeys.read()
        k = -1
        if k==27: #ESC
            mykeys.close()
            DISPLAY.stop()
            break

        if curSlide.isAnimating or nextSlide.isAnimating:
            nextSlide.step()
            curSlide.step()
        elif (time.time() - lastTransitionStart) >= config.HOLD_TIME and not slideQueue.empty():
            lastTransitionStart = time.time()
            curSlide = nextSlide
            nextSlide = slideQueue.get()
            curSlide.startFadeOut()
            nextSlide.startFadeIn()

        curSlide.draw()
        nextSlide.draw()

    DISPLAY.destroy()