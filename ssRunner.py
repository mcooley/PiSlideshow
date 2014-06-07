#!/usr/bin/env python

from __future__ import absolute_import, division, print_function, unicode_literals

import time, threading, os, sys, sqlite3, cStringIO
from dateutil import parser
from dropbox import client, rest, session
from six.moves import queue

import config

#from Pi3DDisplayer import Slide, displayLoop
from DummyDisplayer import Slide, displayLoop

# Place to store the database files, etc.
RESOURCE_DIR = os.path.dirname(os.path.realpath(__file__)) + '/data'

class DropboxSync:
    TOKEN_FILE = RESOURCE_DIR + "/token_store.txt"
    CURSOR_FILE = RESOURCE_DIR + "/dropbox_cursor.txt"
    
    def __init__(self, app_key, app_secret, prefix = "/"):
        self.app_key = app_key
        self.app_secret = app_secret
        self.path_prefix = prefix
        self.cursor = None

        self.api_client = None
        try:
            serialized_token = open(self.TOKEN_FILE).read()
            if serialized_token.startswith('oauth2:'):
                access_token = serialized_token[len('oauth2:'):]
                self.api_client = client.DropboxClient(access_token)
                print("Loaded OAuth 2 access token.")
            else:
                print("Malformed access token in %r." % (self.TOKEN_FILE,))
        except IOError:
            sys.stdout.write("An access token file could not be loaded.\n")
            flow = client.DropboxOAuth2FlowNoRedirect(self.app_key, self.app_secret)
            authorize_url = flow.start()
            sys.stdout.write("1. Go to: " + authorize_url + "\n")
            sys.stdout.write("2. Click \"Allow\" (you might have to log in first).\n")
            sys.stdout.write("3. Copy the authorization code.\n")
            code = raw_input("Enter the authorization code here: ").strip()

            try:
                access_token, user_id = flow.finish(code)
            except rest.ErrorResponse, e:
                self.stdout.write('Error: %s\n' % str(e))
                return

            with open(self.TOKEN_FILE, 'w') as f:
                f.write('oauth2:' + access_token)
            self.api_client = client.DropboxClient(access_token)
    
    def loadCursor(self):
        try:
            self.cursor = open(self.CURSOR_FILE).read()
        except IOError:
            print ("Could not load cursor from file. Will download Dropbox changes from the beginning of time.")
            self.cursor = None
        
    def saveCursor(self):
        with open(self.CURSOR_FILE, 'w') as f:
            f.write(self.cursor)
    
    def doDeltaPoll(self):
        hasMore = True
        while hasMore:
            results = self.api_client.delta(cursor=self.cursor, path_prefix=self.path_prefix)

            store = PhotoMetadataStore()
        
            if results['reset']:
                store.wipe()
        
            for item in results['entries']:
                if (len(item[0].split('/.')) > 1) or item[1].get('is_dir'):
                    # ignore directories and hidden things
                    continue
                if item[1] is None:
                    store.deleteItem(item[0])
                else:
                    store.addItem(item[0], item[1])

            self.cursor = results['cursor']
            hasMore = results.get('has_more', False)
            self.saveCursor()

    def getFile(self, filename):
        try:
            out = cStringIO.StringIO()
            with self.api_client.get_file(filename) as f:
	        out.write(f.read())
            return out.getvalue()
        except:
            print("Got an error in a dropbox file fetch.")
            raise

class PhotoMetadataStore:
    DB_FILE = RESOURCE_DIR + "/dropbox_photos.db"
    
    def __init__(self):
        self.connection = sqlite3.connect(self.DB_FILE)
        self.c = self.connection.cursor()
        
    def tryCreateDB(self):
        self.c.execute("CREATE TABLE IF NOT EXISTS photos (path TEXT PRIMARY KEY, month INTEGER)")
        self.connection.commit()
    
    def addItem(self, path, metadata):
        month = parseMonthFromPath(path)
        if month is None and 'client_mtime' in metadata:
            t = parser.parse(metadata['client_mtime'])
            month = ((t.year - 1970) * 12) + t.month
        self.c.execute("INSERT OR REPLACE INTO photos VALUES (?,?)", (path, month))
        self.connection.commit()
        
    def deleteItem(self, path):
        self.c.execute("DELETE FROM photos WHERE path = ? LIMIT 1", path)
        self.connection.commit()
    
    def wipe(self):
        self.c.execute("DELETE FROM photos")
        self.connection.commit()
    
    def getRandomPhoto(self):
        self.c.execute("SELECT path FROM photos ORDER BY RANDOM() LIMIT 1")
        return self.c.fetchone()[0]

    def __del__(self):
        self.connection.close()

def parseMonthFromPath(path):
    parts = path.split("/")
    year = None
    month = -1
    MONTHS = dict(zip(['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december'], range(12)))
    for part in parts:
        try:
            if not year:
                year = int(part)
            elif month == -1 and part in MONTHS:
                month = MONTHS[part]
        except:
            pass
    if not year:
        return None
    return ((year - 1970) * 12) + month;

slideQueue = queue.Queue()

sync = DropboxSync(config.DROPBOX_APP_KEY, config.DROPBOX_APP_SECRET, config.DROPBOX_PATH_PREFIX)

def load_slides():
    sync.loadCursor()
    timeSinceLastSync = time.time()
    db = PhotoMetadataStore()
    db.tryCreateDB()
    hasDoneInitialSync = False
    while True:
        if (not hasDoneInitialSync) or (timeSinceLastSync - time.time()) > config.DROPBOX_SYNC_INTERVAL:
            try:
                print("Checking for Dropbox changes.")
                sync.doDeltaPoll()
                hasDoneInitialSync = True
                timeSinceLastSync = time.time()
            except:
                print("There was an error polling for Dropbox changes.")
        if slideQueue.qsize() < config.MAX_IMAGES_IN_BUFFER:
            try:
                slideQueue.put(Slide(db.getRandomPhoto()))
            except:
                print("There was an error fetching a random photo.")
        else:
            time.sleep(2)

t = threading.Thread(target=load_slides)
t.daemon = True
t.start()

displayLoop(slideQueue);