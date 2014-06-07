import os

# You can find these at http://www.dropbox.com/developers/apps
DROPBOX_APP_KEY = '<<YOUR KEY HERE>>'
DROPBOX_APP_SECRET = '<<YOUR SECRET HERE>>'

# The folder the photos are in.
DROPBOX_PATH_PREFIX = "/Photos"

# How long, in seconds, to display an image on the screen.
HOLD_TIME = 11

# How much to increment/decrement the image transparency each frame.
ALPHA_STEP = 0.025

# How many images to keep loaded at once.
MAX_IMAGES_IN_BUFFER = 3

# How long to wait between Dropbox syncs.
DROPBOX_SYNC_INTERVAL = 10000
