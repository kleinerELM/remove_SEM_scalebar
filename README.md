# remove_SEM_scalebar

__This Script is depricated! The functionality is mostly included in `tiff_scaling`__

simple script to remove scale and info bar at the bottom of SEM images aquired using a FEI / thermofischer scientific SEM

## standard automatical processing

run
```bash
python .\remove_SEM_scalebar.py
```

and select the working directory containing the TIF images aquired by a FEI / thermofischer scientific SEM software. It will automatically scan for the typical metadata at the end of the image. The scale will be read out and the size of the info bar will be calculated and removed using an ImageJ macro.

The processed images will be saved in a subfolder of the data folder named "cut".

Help output of the python script:

```
#########################################################
# Automatically remove scale bar and set scale for TIFF #
# images from FEI/Thermofischer Scientific SEM devices  #
# in a selected folder.                                 #
#                                                       #
# © 2021 Florian Kleiner                                #
#   Bauhaus-Universität Weimar                          #
#   Finger-Institut für Baustoffkunde                   #
#                                                       #
#########################################################

usage: D:\Nextcloud\Uni\WdB\REM\Fiji Plugins & Macros\Selbstgeschrieben\remove_scalebar\remove_SEM_scalebar.py [-h] [-o] [-s] [-p] [-d]
-h,                  : show this help
-o,                  : setting output directory name [cut]
-s,                  : sort output by pixel size [cut/1.234nm/]
-p,                  : remove scale bar using PIL (no ImageJ processing, -b is not doing anything)
-b,                  : create a jpg image with an included scale bar
-d                   : show debug output
```

## processing without using ImageJ
To only remove the scale bar without setting the scale in the image for ImageJ, the following start parameters should be used:
```bash
python .\remove_scalebar.py -p -s
```
The images will be put in subfolders named by the pixel size. Eg:

```
./cut/5.82812nm
```
The contained 8-bit grayscale images in this example have a scale of 5.82812 nm per pixel.

## manual processing using the ImageJ Macro

remove_scalebar.ijm can be used to fastly process a folder with many images with the same image size and scale, or if the scale does not matter.
Usage:
```bash
ImageJ-win64.exe -macro "\path\to\remove_scalebar.ijm" "\path\to\data\|infoBarheight|metricScale|pixelScale|sortByPixelSize|addScaleBarImage"
```
eg:
```bash
ImageJ-win64.exe -macro "C:\remove_scalebar.ijm" "D:\SEM-images\|140|1|1|0|0"
```
