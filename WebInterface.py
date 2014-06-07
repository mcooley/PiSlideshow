import cherrypy, os
from cherrypy.lib.static import serve_file


class WebInterface:
	def __init__(self, configQueue):
		self.configQueue = configQueue

	def run(self):
		conf = {
	    	'/static': {
	 			'tools.staticdir.on': True,
				'tools.staticdir.dir': os.path.dirname(os.path.realpath(__file__)) + '/web'
			}
		}
		cherrypy.quickstart(SlideshowWebController(self.configQueue), '/', conf)


class SlideshowWebController(object):
	def __init__(self, configQueue):
		super(SlideshowWebController, self).__init__();
		self.configQueue = configQueue;

	@cherrypy.expose
	def index(self):
		return serve_file(os.path.dirname(os.path.realpath(__file__)) + '/web/main.html');

	@cherrypy.expose
	@cherrypy.tools.json_in()
	def setPaths(self):
		self.configQueue.put(cherrypy.request.json);

	@cherrypy.expose
	@cherrypy.tools.json_out()
	def getPaths(self):
		return {'paths': ['/ff/a', '/ff/b']}