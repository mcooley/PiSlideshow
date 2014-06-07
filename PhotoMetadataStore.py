from __future__ import absolute_import, division, print_function, unicode_literals

import sqlite3
from dateutil import parser

class PhotoMetadataStore:
    def __init__(self, db_file):
        self.db_file = db_file

        self.connection = sqlite3.connect(self.db_file)
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

    def setPhotoPaths(self, paths):
        print(paths)

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