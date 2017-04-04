 #-*- coding: utf-8 -*-

from http.server import BaseHTTPRequestHandler
from multiprocessing import Process, Queue
from time import sleep

from blinker import signal

from .const import IMGPATH, MATSPATH, PHOTORECEIVEDSIGNAL
from .utils import debuglog, infolog


class HttpHandler(BaseHTTPRequestHandler):
    """ The handler for each HTTP request the server will receive. One instance
        of this class is fired at each request and is closed after it has
        answered.
    """

    # We need to access the yoloHandler to give it the images and the matrices
    # but we don't want to instanciate a new yoloHandler object at each
    # request we receive.
    yoloHandler = None
    faceRecognizerHandler = None
    verbose = True
    PhotoReceivedEvent = signal(PHOTORECEIVEDSIGNAL)

    # LOG UTILITIES

    def debuglog(self, msg):
        debuglog(msg, self.verbose)

    # ANSWERS

    def generic_answer(self, msg):
        """ Send a generic HTTP answer with msg:
                - Status code: 200
                - Header fields: Content-Type, Content-Length
                - Body: msg
        """
        try:
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", len(msg))
            self.end_headers()
            self.wfile.write(msg.encode("utf8"))
            self.debuglog("Sent:\n%s" % msg)
        except ConnectionResetError as cre:
            print(cre)
            self.finish()
            self.connection.close()

    def dummy_answer(self):
        """ Send an answer that won't be used by the HoloLens.
            (Every request should be answered, even if in our case some of them
            don't need to be)
        """
        self.generic_answer("Good")

    def request_photo(self):
        """ Send "PhotoRequest" as an answer to ask a photo from the HoloLens
        """
        self.generic_answer("PhotoRequest")

    def send_object_rays(self):
        """ Send all the rays we computed since last time we called this function.
            null stands for no ray
        """
        rays = "ray:null"
        # Get all the object rays we have ..
        while self.yoloHandler.hasObject():
            nextRay = self.yoloHandler.getNextRaycast()
            rays += "\nray:%s" % str(nextRay)
        # .. and all the face rays we have
        if rays == "ray:null":
            sleep(0.5)
        self.generic_answer(rays)

    def send_recognized_faces(self):
        rays = "faceray:null"
        while self.faceRecognizerHandler.hasRecognizedFaces():
            nextRecognizedFace = self.faceRecognizerHandler.getRecognizedFace()
            rays += "\nfaceray:%s" % str(nextRecognizedFace)
        if rays == "ray:null":
            sleep(0.5)
        self.generic_answer(rays)


    def send_unknown_faces(self):
        """ Send all the faces we didn't recognize
        """
        rays = "unknownface:ray:null"
        while self.faceRecognizerHandler.hasUnkownFaces():
            nextUnknownFace = self.faceRecognizerHandler.get()
            rays += "\nunknownface:ray:%s" % str(nextUnknownFace.raycast)
        if rays == "ray:null":
            sleep(0.5)
        self.generic_answer(rays)

    # HTTP REQUESTS

    def do_PUT(self):
        """ Deal with a PUT request. PUT requests are only used to send photos
            and matrices (see parse_input). We parse the message we get and
            store the photo in IMAGEPATH and the matrices in MATSPATH. We then
            notify the yoloHandler that we have new inputs
        """
        msg_length = int(self.headers['Content-Length'])
        self.debuglog('### PUT ### %d' % msg_length)

        rawImage, mats = self.splitImageMats(self.rfile.read(msg_length))
        with open(IMGPATH, "w+b") as f:
            f.write(rawImage)
        with open(MATSPATH, "w+") as f:
            f.write(mats)
        self.PhotoReceivedEvent.send("HttpHandler", imgpath = IMGPATH,
                                                    matspath = MATSPATH)
        self.dummy_answer()

    def do_GET(self):
        """ Deal with GET requests. We ignore them since they are the first
            request sent by the HoloLens when it tries to reach the server
        """
        self.dummy_answer()

    def do_POST(self):
        """ Deal with a POST request. Depending on what message we get we do :
                - letsgo: that's the initial request sent by the HoloLens to
                          begin the program. We ask for a photo in return
                - nextrays: whenever the HoloLens has dealt with all the
                            rays it has received, it asks for more rays. So we
                            send them
                - camsize(w)x(h): the HoloLens sends the camera resolution at
                                  the beginning, we store that information
                - obj*: when a message starts with obj, that means the HoloLens
                        is sending us the 3D position of the objects it has
                        stored, we parse the message and store the objects
        """
        msg_length = int(self.headers['Content-Length'])
        msg = self.rfile.read(msg_length).decode("utf8")
        self.debuglog('### POST ### %s' % msg)

        self.handle_msg(msg)

    # HANDLE MESSAGES

    def handle_msg(self, msg):
        if msg == "letsgo":
            self.handle_letsgo(msg)
        if msg == "nextobjects":
            self.handle_nextobjects(msg)
        if msg == "nextfaces":
            self.handle_nextfaces(msg)
        if msg[:7] == "camsize":
            self.handle_camsize(msg)
        if msg[:3] == "obj":
            self.handle_obj(msg)

    def handle_letsgo(self, msg):
        """ Request an image
        """
        self.request_photo()

    def handle_nextobjects(self, msg):
        """ Send all the objects we have
        """
        self.send_object_rays()

    def handle_camsize(self, msg):
        """ Set camsize on faceRecognizer and yoloHandler and send a dummy
            answer
        """
        parseMsg = msg[7:].split("x")
        self.yoloHandler.camsize[0] = float(parseMsg[0])
        self.yoloHandler.camsize[1] = float(parseMsg[1])
        self.faceRecognizerHandler.camsize[0] = float(parseMsg[0])
        self.faceRecognizerHandler.camsize[1] = float(parseMsg[1])
        self.dummy_answer()

    def handle_obj(self, msg):
        """ obj messages contain the actual 3D objects displayed by the Hololens
        """
        self.dummy_answer()

    def handle_nextfaces(self, msg):
        """ Send all the faces we have
        """
        self.send_recognized_faces()
        self.send_unknown_faces()

    # UTILS

    def splitImageMats(self, byteArray):
        """ byteArray looks like b"Length(4 bytes)
                                   [Photo]
                                   Projection:[Matrix];
                                   World:[Matrix]"
            We separate the photo from the matrices and return them
        """
        length = int.from_bytes(byteArray[:4], 'little')
        rawImage = byteArray[4:length+4]
        mats = byteArray[length+4:].decode("utf8")
        # The message always contain these characters near the matrices, and
        # they can't be translated to utf8. So we get rid of them
        mats = mats.replace("\x00", " ")

        return rawImage, mats
