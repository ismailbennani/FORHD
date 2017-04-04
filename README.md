# FORHD
Face and Object Recognition on Holographic Devices

## Installation guide
In order to run the FORHD server you will need to install OpenCV3 (you can follow the instructions [here](http://www.pyimagesearch.com/2016/10/24/ubuntu-16-04-how-to-install-opencv/)) and darknet (you can follow the instructions [here](https://pjreddie.com/darknet/yolo/), note that darknet sources are already available in this repo).

Once it is done, you need to install some python packages, for that you can run :
```
pip3 install -r requirements.txt
```

And finally you need to build faceRecognizer:
```
cd faceRecognizer
make
```

Now, you should be able to run the server:
```
python3 FORHD.py
```
