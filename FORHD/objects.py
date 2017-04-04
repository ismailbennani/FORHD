 #-*- coding: utf-8 -*-
""" Representation of 2D objects, 3D objects and faces """

class Object2D:
    """ Representation of a 2D object on a photograph """

    def __init__(self, label, confidence, x, y, w, h):
        self.label = label
        self.confidence = float(confidence)
        self.x = float(x)
        self.y = float(y)
        self.w = float(w)
        self.h = float(h)

    def __str__(self):
        return "%s;%s;%s;%s;%s;%s" % (self.label,
                                   str(self.confidence),
                                   str(self.x),
                                   str(self.y),
                                   str(self.w/2),
                                   str(self.h/2))

class Object3D:
    """ Representation of a 3D object in world space """

    def __init__(self, label, confidence, x, y, z, w, h):
        self.label = label
        self.confidence = confidence
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
        # width and height are currently the same as in Object2D, that means
        # they are just the pixel size of the object on the photograph
        self.w = float(w)
        self.h = float(h)

    def __str__(self):
        return "%s;%s;%s;%s;%s" % (self.label,
                                   self.confidence,
                                   self.x,
                                   self.y,
                                   self.z)

class Face:

    def __init__(self, filepath, raycast, name = "Unknown"):
        self.filepath = filepath
        self.raycast = raycast
        self.name = name

    def __str__(self):
        return "ray:%s|name:%s" % (raycast, name)

    def __eq__(self, otherFace):
        return self.raycast == otherFace.raycast
