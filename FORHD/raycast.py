 #-*- coding: utf-8 -*-

import numpy as np
from .utils import str3DPoint

class Raycast():
    """ A representation of a raycast """

    def __init__(self, label, confidence, wpointCenterNear, wpointCenterFar,
                       width, height):
        self.label = label
        self.confidence = confidence
        self.wpointCenterNear = wpointCenterNear
        self.wpointCenterFar = wpointCenterFar
        self.width = width
        self.height = height

    @staticmethod
    def parseMats(matsString):
        """ Parse a string that looks like
            "Projection:[ProjectionMat];World:[WorldMat]" and return them as
            numpy 2D arrays
        """
        def parseMatrix4x4(matString):
            """ Parse a matrix that looks like
                elt0,0 elt0,1 elt0,2 ... elt0,n\n
                .
                .
                .
                eltm,0 eltm,1 eltm,2 ... eltm,n\n
                with any spacing character between elements (such as \t or a
                normal space character)
            """
            res = []
            lines = matString.split("\n")
            for line in matString.split("\n"):
                elts = [float(s) for s in line.split()]
                if elts != []:
                    res.append(elts)
            return np.array(res)

        parseMatsString = matsString.split(";")

        projection = parseMatrix4x4(parseMatsString[0].split(':')[1])
        world = parseMatrix4x4(parseMatsString[1].split(':')[1])

        return projection, world

    @staticmethod
    def unProjectVector(projection, vector):
        """ Inputs:
                - projection is a 4x4 numpy 2D array
                - vector is a 1x3 numpy array
            Return one of the 3D vectors that are projected into vector by
            projection
        """
        _from = np.array([0., 0., 0.])
        axsX = projection[0]
        axsY = projection[1]
        axsZ = projection[2]
        _from[2] = vector[2] / axsZ[2] # from.z = to.z / axsZ.z;
        _from[1] = (vector[1] - (_from[2] * axsY[2])) / axsY[1] # from.y = (to.y - (from.z * axsY.z)) / axsY.y;
        _from[0] = (vector[0] - (_from[2] * axsX[2])) / axsX[0] # from.x = (to.x - (from.z * axsX.z)) / axsX.x;

        return _from

    @staticmethod
    def fromObject2D(object2D, projection, world, camsize):
        """ Return a raycast which pointing toward the location of object2D
            in the 3D space of the camera. projection and world are the
            parameters of the camera at the time the photo was taken, camsize is
            the resolution of the image containing object2D
        """
        def get3DPoint(point2D):
            """ 2DPoint is a tuple containing the x and y coordinates on the
                image
            """
            # we transform the coordinates of object2D to relative coordinates
            ImagePosZeroToOne = [point2D[0] / camsize[0],
                                 1. - (point2D[1] / camsize[1])]
            # we transform them into coordinates between -1 and 1
            ImagePosProjected = [ImagePosZeroToOne[0] * 2 - 1,
                                 ImagePosZeroToOne[1] * 2 - 1]
            # we compute one possible position of the object in the camera space
            # coordinates
            CameraSpacePos = Raycast.unProjectVector(projection,
                                                     [
                                                        ImagePosProjected[0],
                                                        ImagePosProjected[1],
                                                        1.
                                                     ])
            # we convert camera space coordinates to world space coordinates thanks
            # to world. (0, 0, 0) are the coordinates of the camera in its own
            # space and CameraSpacePos is the position of the object in the camera
            # space. Those two points define a ray going from the camera to the
            # 3D object we are looking for
            wpointCamera = world.dot(np.array([0., 0., 0., 1.]))
            wpoint = world.dot(np.concatenate((CameraSpacePos, [1.])))

            return wpointCamera, wpoint

        wpointCamera, wpointCenter = get3DPoint([object2D.x, object2D.y])

        res = Raycast(object2D.label,
                      object2D.confidence,
                      wpointCamera,
                      wpointCenter,
                      object2D.w,
                      object2D.h)

        return res

    def __str__(self):
        return "%s;%s;%s;%s;%s;%s" % (self.label,
                                   self.confidence,
                                   str3DPoint(self.wpointCenterNear),
                                   str3DPoint(self.wpointCenterFar),
                                   self.width,
                                   self.height)

    def __eq__(self, otherRaycast):
        return self.wpointcamera == otherRaycast.wpointCenterNear\
           and self.wpointCenter == otherRaycast.wpointCenterFar
