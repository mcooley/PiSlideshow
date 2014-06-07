from __future__ import absolute_import, division, print_function, unicode_literals

import os, sys, cStringIO

from dropbox import client, rest, session
import config

class DropboxSync:
    TOKEN_FILE = config.RESOURCE_DIR + "/token_store.txt"
    CURSOR_FILE = config.RESOURCE_DIR + "/dropbox_cursor.txt"
    
    def __init__(self, app_key, app_secret, store, prefix = "/"):
        self.app_key = app_key
        self.app_secret = app_secret
        self.path_prefix = prefix
        self.cursor = None
        self.db = store

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

            if results['reset']:
                self.db.wipe()
        
            for item in results['entries']:
                if (len(item[0].split('/.')) > 1) or item[1].get('is_dir'):
                    # ignore directories and hidden things
                    continue
                if item[1] is None:
                    self.db.deleteItem(item[0])
                else:
                    self.db.addItem(item[0], item[1])

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
