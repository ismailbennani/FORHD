# FORHD
Face and Object Recognition on Holographic Devices

# Installation guide

To build the application, you will need [Unity](https://store.unity.com/download?ref=personal) and [Visual Studio](https://www.visualstudio.com/downloads/).

Once you have them, create a new project in Unity and import the [holotoolkit unity package](https://github.com/Microsoft/HoloToolkit-Unity/tree/master/External/Unitypackages). You will need to import the [FORHD unity package](https://github.com/ismailbennani/FORHD/tree/master/FORHD/Unity) too.

Once everything is uploaded to Unity, please drag the Main.scene scene found in Assets/Scenes to unity's scenes view and remove the default one and configure unity for the hololens, you can do that by running the configuration tools in Holotoolkit -> Configure menu.

Finally, you can export to a Visual Studio SLN (Holotoolkit -> Build Window -> Build Visual Studio SLN), open the SLN (Holotoolkit -> Build Window -> Open SLN). To build and deploy the application to the Hololens, please select the x86 platform and compile to Remote Machine. You will probably need to enter the IP address of the Hololens.
