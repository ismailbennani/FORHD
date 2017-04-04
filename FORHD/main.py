from http.server import HTTPServer

from .yoloHandler import YoloHandler
from .httpHandler import HttpHandler
from .faceRecognizerHandler import FaceRecognizerHandler
from .const import LOCALIP, LOCALPORT
from .utils import infolog

class Main:
    """ The main class of our program """

    def __init__(self, verbose = True):
        """ We start by instantiating yoloHandler and faceRecognizer and
            giving it to the HttpHandler as a static variable.
            Then we start the HTTP server
        """
        self.verbose = verbose

        self.yoloHandler = YoloHandler(verbose = self.verbose)
        HttpHandler.yoloHandler = self.yoloHandler

        self.faceRecognizerHandler = FaceRecognizerHandler(verbose = self.verbose)
        HttpHandler.faceRecognizerHandler = self.faceRecognizerHandler

        self.server = HTTPServer((LOCALIP, LOCALPORT), HttpHandler)

        self.run()

    def run(self):
        """ Run the HTTPServer until we get a KeyboardInterrupt (^C)
        """
        try:
            self.server.serve_forever()
        except KeyboardInterrupt:
            infolog('^C received, shutting down the web server')
            self.close()

    def close(self):
        """ Close and clean the server and the yoloHandler """
        self.server.socket.close()
        self.yoloHandler.close()
