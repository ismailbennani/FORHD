 #-*- coding: utf-8 -*-

import os, os.path, sys
from time import sleep

from multiprocessing import Queue, Process, Value, Manager, Array
from ctypes import c_char_p
from subprocess import Popen, PIPE, DEVNULL, STDOUT

from blinker import signal

from .objects import Object2D
from .raycast import Raycast
from .utils import infolog, warninglog
from .const import DARKNETBASEPATH, DARKNETPATH, DARKNETMAKECOMMAND, DATAPATH,\
                   CFGPATH, WEIGHTPATH, PROGRAM, MODE, FEEDPIPE, DETECTIONSPIPE,\
                   PHOTORECEIVEDSIGNAL

class YoloHandler():
    """ The class used to communicate with YOLO """

    def __init__(self, verbose = True):
        self.verbose = verbose

        # running is a synchronized int that we use to run and stop the
        # processes we spawn
        infolog("Initializing yoloHandler")
        self.running = Value('i', 1)

        # open YOLO in a new thread, after it is opened we can send it filepaths
        # by writing to yolo.stdin
        infolog("Launching YOLO")

        if not os.path.isfile(DARKNETBASEPATH+DARKNETPATH):
            warninglog("Couldn't find %s%s, running %s%s" %\
                        (DARKNETBASEPATH,
                         DARKNETPATH,
                         DARKNETBASEPATH,
                         DARKNETMAKECOMMAND))
            Popen(DARKNETMAKECOMMAND.split(), cwd = DARKNETBASEPATH)

        self.yolo = Popen([DARKNETPATH, PROGRAM, MODE, DATAPATH, CFGPATH,
                           WEIGHTPATH], stdin = PIPE, bufsize = 1,
                           stdout = DEVNULL, stderr = STDOUT,
                           universal_newlines = True, cwd = DARKNETBASEPATH)

        # manager that will enable us to share state between processes
        self.manager = Manager()
        # synchronized string that stores the path to the last photo taken
        self.nextPhoto = self.manager.Value(c_char_p, "")
        # synchronized string that stores the path to the last matrices received
        self.nextMats = self.manager.Value(c_char_p, "")

        # synchronized queue where we store the rays we compute
        self.raycastQueue = Queue()
        # synchronized float array used to store the camera resolution
        self.camsize = Array('f', (1280., 720.))

        # we spawn a process that will feed yolo whenever it needs to (which is
        # at every new picture received if yolo is finished with the previous
        # one)
        infolog("Start feeding YOLO")
        self.yoloFeeder = Process(target = self.writeToYolo)
        self.yoloFeeder.start()

        # we spawn a process that will constantly retrieve data from yolo, parse
        # it, convert the 2D points data to raycasts and store them in the queue
        infolog("Start listening to YOLO")
        self.yoloListener = Process(target = self.retrievefromYolo)
        self.yoloListener.start()

        # we connect to the photoreceived signal
        self.PhotoReceivedEvent = signal(PHOTORECEIVEDSIGNAL)
        self.PhotoReceivedEvent.connect(self.write)

    def write(self, sender, **kw):
        """ Give yoloHandler the new IMGPATH and the corresponding
            matrices in MATSPATH.
        """
        IMGPATH = kw["imgpath"]
        MATSPATH = kw["matspath"]

        # we update the synchronized strings storing those values
        self.nextPhoto.value = ("../"+IMGPATH+"\n")
        self.nextMats.value = (MATSPATH)

    def writeToYolo(self):
        """ Launched in a new process. We listen for a "SendMore" request from
            YOLO on FEEDPIPE and we send the path to the last picture taken
            if it has not already been processed.
        """
        while not os.path.exists(FEEDPIPE):
            sleep(1)
        yolopipe = open(FEEDPIPE, 'rb+', buffering = 0)

        while(self.running.value):
            lastLine = yolopipe.readline()[:-1].decode("utf8")
            if lastLine == "SendMore":
                while self.nextPhoto.value == "":
                    pass
                self.yolo.stdin.write(self.nextPhoto.value)
                self.nextPhoto.value = ""

        yolopipe.close()

    def retrievefromYolo(self):
        """ Launched in a new process. We listen for new inputs on
            DETECTIONSPIPE, we parse each input (which looks like
            "label;confidence;x;y;width;height\n"), we ask for a Raycast from
            our 2D object and we add that raycast to the queue
        """
        while not os.path.exists(DETECTIONSPIPE):
            sleep(1)
        yolopipe = open(DETECTIONSPIPE, 'rb+', buffering = 0)

        while(self.running.value):
            # Lines look like label;x;y;w;h where x,y are the center of the
            # the bounding rect and w,h half its width and height
            lastLine = yolopipe.readline()[:-1].decode("utf8")
            parsedLine = lastLine.split(";")
            object2D = Object2D(parsedLine[0], parsedLine[1], parsedLine[2],
                                parsedLine[3], parsedLine[4], parsedLine[5])

            matsString = self.nextMats.value
            while matsString == "":
                matsString = self.nextMats.value
            with open(matsString, 'r') as f:
                projection, world = Raycast.parseMats(f.read())
            raycast = Raycast.fromObject2D(object2D, projection, world, self.camsize)
            self.raycastQueue.put(raycast)

        yolopipe.close()

    def getNextRaycast(self, block = True, timeout = None):
        """ Return the next element in the raycast queue
        """
        return self.raycastQueue.get(block, timeout)

    def hasObject(self):
        """ Return if the queue has at least an object in it or not
        """
        return not self.raycastQueue.empty()

    def close(self):
        """ Clean everything, that means stop the processes by setting running
            to false (0) and join them
        """
        self.running.value = 0
        self.yoloFeeder.join()
        self.yoloListener.join()
