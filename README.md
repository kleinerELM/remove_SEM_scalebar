# remove_SEM_scalebar
simple script to remove scale and info bar at the bottom of SEM images made with a FEI / thermofischer scientific SEM 

## standard automatical processing

run "python .\remove_scalebar.py" and select the working directory containing the TIF images created by a FEI / thermofischer scientific SEM software. It will automatically scan for the typical metadata at the end of the image. The scale will be read out and the size of the info bar will be calculated and removed using an ImageJ macro.

The processed images will be saved in a subfolder of the data folder named "cut".

Help output of the python script:

```
#########################################################
# Automatically remove scale bar and set scale for TIFF #
# images from FEI/Thermofischer Scientific SEM devices  #
# in a selected folder.                                 #
#                                                       #
# © 2019 Florian Kleiner                                #
#   Bauhaus-Universität Weimar                          #
#   Finger-Institut für Baustoffkunde                   #
#                                                       #
#########################################################

usage: .\remove_scalebar.py [-h] [-o] [-d]
-h,                  : show this help
-o,                  : setting output directory name [cut]
-d                   : show debug output
```

## fast processing

remove_scalebar.ijm can be used to fastly process a folder with many images with the same image size and scale, or if the scale does not matter.
Usage:

ImageJ-win64.exe -macro "\path\to\remove_scalebar.ijm" "\path\to\data\|infoBarheight|metricScale|pixelScale"
eg: ImageJ-win64.exe -macro "C:\remove_scalebar.ijm" "D:\SEM-images\|140|1|1"
