![Darknet Logo](http://pjreddie.com/media/files/darknet-black-small.png)

#Darknet
Darknet is an open source neural network framework written in C and CUDA. It is fast, easy to install, and supports CPU and GPU computation.

For more information see the [Darknet project website](http://pjreddie.com/darknet).

For questions or issues please use the [Google Group](https://groups.google.com/forum/#!forum/darknet).

This is a copy of the darknet project with small modifications on src/detector.c and src/image.c. The goal was to make the outputs of YOLO usable in another program, this has been done by adding named pipes to feed filepaths to YOLO and retrieve the answers. Please find all the informations on how to install YOLO on their official website.
