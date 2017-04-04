 #-*- coding: utf-8 -*-

import os, os.path
import shutil

from multiprocessing import Process, Manager, Value, Queue, Array
from ctypes import c_char_p
from subprocess import Popen, PIPE

import numpy as np
import cv2

from blinker import signal

from .const import PHOTORECEIVEDSIGNAL, DUMMYNAME, FACEDIR,\
                   FACERECOGNIZERBASEPATH, FACERECOGNIZERPATH,\
                   FACERECOGNIZERMAKECOMMAND
from .raycast import Raycast
from .objects import Object2D, Face
from .utils import infolog, warninglog

class FaceRecognizerHandler:
    """ The class used to communicate with faceRecognizer """

    def __init__(self, verbose = True):
        self.verbose = verbose

        infolog("Initializing faceRecognizerHandler")
        self.running = Value('i', 1)

        # open faceRecognizer in a new thread, after it is opened we can send
        # it filepaths by writing to faceRecognizer.stdin
        infolog("Launching faceRecognizer")

        if not os.path.isfile(FACERECOGNIZERBASEPATH+FACERECOGNIZERPATH):
            warninglog("Couldn't find %s%s, running %s%s" %\
                        (FACERECOGNIZERBASEPATH,
                         FACERECOGNIZERPATH,
                         FACERECOGNIZERBASEPATH,
                         FACERECOGNIZERMAKECOMMAND))
            Popen(FACERECOGNIZERMAKECOMMAND.split(), cwd = FACERECOGNIZERBASEPATH)

        self.faceRecognizer = Popen([FACERECOGNIZERPATH], stdin = PIPE,
                                    stdout = PIPE, bufsize = 1,
                                    universal_newlines = True,
                                    cwd = FACERECOGNIZERBASEPATH)

        self.manager = Manager()
        # synchronized string that stores the path to the last photo taken
        self.nextPhoto = self.manager.Value(c_char_p, "")
        self.nextMats = self.manager.Value(c_char_p, "")
        # synchronized queues that stores faces
        self.faces = Queue()
        self.unknownFaces = Queue()
        self.recognizedFaces = Queue()
        # synchronized float array used to store the camera resolution
        self.camsize = Array('f', (1280., 720.))

        # cascade classifier that will get faces from images
        self.face_cascade = cv2.CascadeClassifier('models/haarcascade_frontalface_default.xml')

        # we connect to the photoreceived signal
        self.PhotoReceivedEvent = signal(PHOTORECEIVEDSIGNAL)
        self.PhotoReceivedEvent.connect(self.write)

        infolog("Starting faceMaker")
        self.faceMaker = Process(target = self.makeFaces)
        self.faceMaker.start()

        infolog("Start handling faceRecognizer")
        self.faceRecognizerHandle = Process(target = self.handleFaceRecognizer)
        self.faceRecognizerHandle.start()

        if not os.path.isdir(FACEDIR):
            os.makedirs(FACEDIR)

    def write(self, sender, **kw):
        """ Give faceRecognizerHandler the new IMGPATH and the corresponding
            matrices in MATSPATH.
        """
        IMGPATH = kw['imgpath']
        MATSPATH = kw['matspath']

        self.nextPhoto.value = IMGPATH+"\n"
        self.nextMats.value = MATSPATH

    def getFaceFilepath(self):
        """ Get a valid unused filepath in FACEDIR to save a new image
        """
        i = 0
        while True:
            filepath = FACEDIR+str(i)+".jpg"
            if not os.path.exists(filepath):
                return filepath
            i += 1

    def makeFaces(self):
        """ Launched in a new process. Find faces in the images, cut them out
            and save them before telling the recognizer handler that it needs
            to recognize new files
        """
        while self.running.value:
            while self.nextPhoto.value == "":
                pass
            img = cv2.imread(self.nextPhoto.value[:-1], cv2.IMREAD_GRAYSCALE)
            if img is not None:
                faces = self.face_cascade.detectMultiScale(img, 1.3, 5)
                for (x, y, w, h) in faces:
                    faceimg = img[x:x+w, y:y+w]
                    filepath = self.getFaceFilepath()
                    cv2.imwrite(filepath, faceimg)
                    object2D = Object2D("Unknown face", 100, x+w/2., y+h/2.,
                                        w, h)
                    matsString = self.nextMats.value
                    with open(matsString, 'r') as f:
                        projection, world = Raycast.parseMats(f.read())
                    raycast = Raycast.fromObject2D(object2D, projection, world, self.camsize)
                    face = Face(filepath, raycast, "Unknown")

                    self.faces.put(face)
                self.nextPhoto.value = ""

    def handleFaceRecognizer(self):
        """ Launched in a new process. We listen for "Enter a path" and provide
            a path to the face recognizer, then we wait for an answer. If the
            face was recognized it goes to the recognizedFaces queue, else it
            goes to the unknownFaces queue
        """
        while self.running.value:
            lastline = self.faceRecognizer.stdout.readline()
            if lastline == "Enter a path":
                nextFace = self.faces.get(block = True)
                debuglog("Giving %s to faceRecognizer" % nextFace.filepath,
                         self.verbose)
                self.faceRecognizer.stdin.write(nextFace.filepath)
                lastline = self.faceRecognizer.stdout.readline()
                if lastline == "Coudln't recognize this person, give me their name":
                    self.unknownFaces.put(nextFace)
                    debuglog("Unrecognized face", self.verbose)
                else:
                    nextFace.name = lastline[-1]
                    self.addRecognizedFace(nextFace)
                    debuglog("Recognized %s" % nextFace.name, self.verbose)
                os.remove(nextFace.filepath)
        self.faceRecognizer.stdin.write("Stop")


    def getRecognizedFace(self, block = True, timeout = None):
        """ Return the first element in recognizedFaces queue
        """
        return self.recognizedFaces.get(block, timeout)

    def addRecognizedFace(self, face):
        """ Put an element in recognizedFaces queue
        """
        self.recognizedFaces.put(face)

    def getUnknownFace(self, block=True, timeout = None):
        """ Return the first element in unknownFaces queue
        """
        return self.unknownFaces.get(block, timeout)

    def hasRecognizedFaces(self):
        """ Return True if there is at least one element in recognizedFaces,
            else false
        """
        return not self.recognizedFaces.empty()

    def hasUnknownFaces(self):
        """ Return True if there is at least one element in unknownFaces,
            else false
        """

    def emptyRecognizedFaces(self):
        """ Empty the queue
        """
        while self.hasRecognizedFaces():
            self.recognizedFaces.get()

    def emptyUnknownFaces(self):
        """ Empty the queue
        """
        while self.hasUnknownFaces():
            self.unknownFaces.get()

    def close(self):
        """ Clean everything, that means stop the processes by setting running
            to false (0) and join them
        """
        self.running.value = 0
        if os.exists(FACEDIR):
            shutil.rmtree(FACEDIR)
        self.faceRecognizerHandle.join()
        self.faceMaker.join()
