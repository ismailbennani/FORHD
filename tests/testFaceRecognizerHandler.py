import unittest
import os.path
from context import faceRecognizerHandler as FRH
from context import objects
from context import const

import os
os.chdir("FORHD")

class TestFRH(unittest.TestCase):

    frh = FRH.FaceRecognizerHandler()

    def test_write(self):
        IMGPATH = "randomImgPath"
        MATSPATH = "randomMatsPath"

        self.frh.write(self, imgpath = IMGPATH, matspath = MATSPATH)
        self.assertEquals(self.frh.nextPhoto.value, IMGPATH+"\n")
        self.assertEquals(self.frh.nextMats.value, MATSPATH)

    def testGetFaceFilepath(self):
        filepath = self.frh.getFaceFilepath()
        self.assertFalse(os.path.isfile(filepath))

    def testEmptyRecognizedFaces(self):
        self.frh.emptyRecognizedFaces()
        self.assertFalse(self.frh.hasRecognizedFaces())

    def testEmptyUnknownFaces(self):
        self.frh.emptyUnknownFaces()
        self.assertFalse(self.frh.hasUnknownFaces())

    def testAddGetHasRecognizedFace(self):
        self.frh.emptyRecognizedFaces()
        filepath = "dummy"
        raycast = Raycast("dummy", 0, (0,0,0), (0,0,0))
        addedFace = objects.Face("dummy", raycast)
        self.frh.addRecognizedFace(addedFace)

        self.assertTrue(self.frh.hasRecognizedFaces())
        face = self.frh.getRecognizedFace()

        self.assertEquals(face, addedFace)

    def testAddGetHasUnknownFace(self):
        self.frh.emptyUnknownFaces()
        filepath = "dummy"
        raycast = Raycast("dummy", 0, (0,0,0), (0,0,0))
        addedFace = objects.Face("dummy", raycast)
        self.frh.addUnknownFace(addedFace)

        self.assertTrue(self.frh.hasUnknownFaces())
        face = self.frh.getUnknownFace()

        self.assertEquals(face, addedFace)

    def testClose(self):
        self.frh.close()

        self.assertEquals(self.frh.running.value, 0)
        self.assertFalse(os.path.isdirectory(const.FACEDIR))
        self.assertFalse(self.frh.faceRecognizerHandle.isAlive())
        self.assertFalse(self.frh.faceMaker.isAlive())
