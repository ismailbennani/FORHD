 #-*- coding: utf-8 -*-

def printlog(tag, msg):
    print("[%s] %s" % (tag, msg))

def debuglog(msg, verbose = True):
    if verbose:
        printlog("DEBUG", msg)

def warninglog(msg):
    printlog("WARNING", msg)

def infolog(msg):
    printlog("INFO", msg)

def str3DPoint(point):
    return "%s,%s,%s" % (point[0],
                         point[1],
                         point[2])
