from __future__ import absolute_import, division, print_function, unicode_literals

import time, os, sys, sqlite3, cStringIO
from six.moves import queue
from PIL import Image

import config
from PhotoMetadataStore import PhotoMetadataStore
from DropboxSync import DropboxSync

class SlideshowController:
    def __init__(self):
        # Contains upcoming slides.
        self.loadQueue = queue.Queue()

        # Contains a slide that should be transitioned in immediately.
        self.showQueue = queue.Queue()

    def run(self):
        db = PhotoMetadataStore(config.RESOURCE_DIR + "/dropbox_photos.db")
        db.tryCreateDB()

        sync = DropboxSync(config.DROPBOX_APP_KEY, config.DROPBOX_APP_SECRET, db, config.DROPBOX_PATH_PREFIX)
        sync.loadCursor()

        timeSinceLastSync = time.time()
        hasDoneInitialRun = False
        lastTransitionStart = time.time()
        while True:
            # Check for Dropbox changes
            if (not hasDoneInitialRun) or (timeSinceLastSync - time.time()) > config.DROPBOX_SYNC_INTERVAL:
                try:
                    print("Checking for Dropbox changes.")
                    sync.doDeltaPoll()
                    timeSinceLastSync = time.time()
                except:
                    print("There was an error polling for Dropbox changes.")
                    raise

            # Check if we should advance the slide
            if ((not hasDoneInitialRun) or (time.time() - lastTransitionStart) >= config.HOLD_TIME) and not self.loadQueue.empty():
                lastTransitionStart = time.time()
                self.showQueue.put(self.loadQueue.get())

            # Check if we should load any new images
            if self.loadQueue.qsize() < config.MAX_IMAGES_IN_BUFFER:
                try:
                    filename = db.getRandomPhoto()
                    image = Image.open(cStringIO.StringIO(sync.getFile(filename)))
                    self.loadQueue.put(image)
                except:
                    print("There was an error fetching a random photo.")
                    raise

            hasDoneInitialRun = True