# CONST:main.py

LOCALIP = ""
LOCALPORT = 8000

# CONST:httpHandler.py

# Path where images from the HoloLens will be stored
IMGPATH = "imgs/HLImage.jpg"
# Path where matrices from the HoloLens will be stored
MATSPATH = "imgs/HLMats"

# CONST:yoloHandler.py

DARKNETBASEPATH = "darknet/"

# YOLO arguments
DARKNETPATH = "./darknet"
DATAPATH = "cfg/coco.data"
CFGPATH = "cfg/yolo.cfg"
WEIGHTPATH = "yolo.weights"

DARKNETMAKECOMMAND = "make"

PROGRAM = "detector"
MODE = "test"

# the pipe used by yolo to ask for an input
FEEDPIPE = "/tmp/yolofeed"
# the pipe used by yolo to send the detections back
DETECTIONSPIPE = "/tmp/detections"

# CONST:rosFeeder.py

OBJECTFEEDPIPE = "/tmp/objectfeed"

# CONST:faceRecognizerHandler.py

FACERECOGNIZERBASEPATH = "faceRecognizer/"
FACERECOGNIZERPATH = "./faceRecognizer"
FACERECOGNIZERMAKECOMMAND = "make"

DUMMYNAME = "Unknown person"
FACEDIR = "imgs/facesToRecognize/"

# CONST:common

PHOTORECEIVEDSIGNAL = 'PhotoReceivedEvent'
