#########################################################
# Automated Scale removal for SEM images by 
# FEI / Thermofischer SEM devices
#
# © 2019 Florian Kleiner
#   Bauhaus-Universität Weimar
#   Finger-Institut für Baustoffkunde
#
# programmed using python 3.7, Fiji/ImageJ 1.52k
# don't forget to install PIL with pip!
#
#########################################################


import csv
import os, sys, getopt
import subprocess
import math
import tkinter as tk
import mmap
from PIL import Image
from tkinter import filedialog
from subprocess import check_output

print("#########################################################")
print("# Automatically remove scale bar and set scale for TIFF #")
print("# images from FEI/Thermofischer Scientific SEM devices  #")
print("# in a selected folder.                                 #")
print("#                                                       #")
print("# © 2019 Florian Kleiner                                #")
print("#   Bauhaus-Universität Weimar                          #")
print("#   Finger-Institut für Baustoffkunde                   #")
print("#                                                       #")
print("#########################################################")
print()


#### directory definitions
home_dir = os.path.dirname(os.path.realpath(__file__))

#### global var definitions
infoBarHeight = 63
metricScale = 0
pixelScale  = 0
pixelSize = 0
outputDirName = "cut"
showDebuggingOutput = False

#### process given command line arguments
def processArguments():
    global outputDirName
    argv = sys.argv[1:]
    usage = sys.argv[0] + " [-h] [-o] [-d]"
    try:
        opts, args = getopt.getopt(argv,"ho:d",[])
    except getopt.GetoptError:
        print( usage )
    for opt, arg in opts:
        if opt == '-h':
            print( 'usage: ' + usage )
            print( '-h,                  : show this help' )
            print( '-o,                  : setting output directory name [' + outputDirName + ']' )
            print( '-d                   : show debug output' )
            print( '' )
            sys.exit()
        elif opt in ("-o"):
            outputDirName = arg
            print( 'changed output directory to ' + outputDirName )
        elif opt in ("-d"):
            print( 'show debugging output' )
            global showDebuggingOutput
            showDebuggingOutput = True
    print( '' )

#### searching for a set pixel scale in the metadata of the TIFF
def getPixelSizeFromMetaData( directory, filename, silent ):
    global pixelSize
    global metricScale
    global pixelScale
    pixelSize = 0
    with open(directory + '/' + filename, 'rb', 0) as file, \
        mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_READ) as s:
        if s.find(b'PixelWidth') != -1:
            file.seek(s.find(b'PixelWidth'))
            tempLine = str( file.readline() ).split("=",1)[1]
            pixelSize = float( tempLine.split("\\",1)[0] )*1000000000
            pixelScale = 1
            metricScale = pixelSize
            if ( not silent ) : print( "  detected image scale: " + str( pixelSize ) + " nm / px" )
    return pixelSize

#### determining the height of the info / scale bar in the TIFF
def getInfoBarHeightFromMetaData( directory, filename ):
    contentHeight = 0
    global infoBarHeight
    with open(directory + '/' + filename, 'rb', 0) as file, \
        mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_READ) as s:
        ## get original image height
        if s.find(b'ResolutionY') != -1:
            file.seek(s.find(b'ResolutionY'))
            tempLine = str( file.readline() ).split("=",1)[1]
            contentHeight = float( tempLine.split("\\",1)[0] )
    if ( contentHeight > 0 ):
        ## get actual image size of the TIFF
        im = Image.open( directory + '/' + filename )
        width, height = im.size
        ## calculate the difference, which is the info bar heigt
        infoBarHeight = int( height - contentHeight )
        print( "  detected info bar height: " + str( infoBarHeight ) + " px" )# + str( height ) + '|' + str(contentHeight))
    else:
        print( "  info bar height not detected" )
    return infoBarHeight

#### check if the expected metadata in the first file of a directory is present
def scaleInMetaData( directory ):
    global infoBarHeight
    result = False
    for file in os.listdir(directory):
        filename = os.fsdecode(file)
        if ( filename.endswith(".jpg") or filename.endswith(".JPG") or filename.endswith(".tif") or filename.endswith(".TIF")):
            print( "checking if file \"" + filename + "\" has expected metadata", end = '' )
            if getPixelSizeFromMetaData( directory, filename, True ) > 0:
                result = True
                break
    if ( result ) : print( ' [successfull]' ) #colored('hello', 'red'), colored('world', 'green')
    return result

#### run the actual code
def analyseImages( directory, file ):
    global metricScale
    global pixelScale
    global infoBarHeight
    global outputDirName
    options = "|" + outputDirName + "|" + str(infoBarHeight) + "|" + str(metricScale) + "|" + str(pixelScale)
    ##if ( file == "" ) :
    ##    command = "ImageJ-win64.exe -macro \"" + home_dir +  "\\remove_scalebar.ijm\" \"" + directory + "/" + options + "\""
    ##else:
    command = "ImageJ-win64.exe -macro \"" + home_dir +"\\remove_scalebar_single_file.ijm\" \"" + directory + "/" + filename + options + "\""
    print( "  starting ImageJ Macro...", end = '' )
    if ( showDebuggingOutput ) : print( command )
    try:
        subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        if ( showDebuggingOutput ) : print( " possible error while closing ImageJ!", end = '' )
        pass
    print( " [done]")

### actual program start
processArguments()
if ( showDebuggingOutput ) : print( "I am living in '" + home_dir + "'" )
workingDirectory = filedialog.askdirectory(title='Please select the image / working directory')
if ( showDebuggingOutput ) : print( "Selected working directory: " + workingDirectory )

if scaleInMetaData( workingDirectory ) :
    count = 0
    position = 0
    ## count files
    if os.path.isdir( workingDirectory ) :
        for file in os.listdir(workingDirectory):
            if ( file.endswith(".tif") or file.endswith(".TIF")):
                count = count + 1
    print( str(count) + " Tiffs found!" )
    ## run actual code
    if os.path.isdir( workingDirectory ) :
        for file in os.listdir(workingDirectory):
            if ( file.endswith(".tif") or file.endswith(".TIF")):
                filename = os.fsdecode(file)
                position = position + 1
                print( " Analysing " + filename + " (" + str(position) + "/" + str(count) + ") :" )
                getPixelSizeFromMetaData( workingDirectory, filename, False )
                getInfoBarHeightFromMetaData( workingDirectory, filename )
                analyseImages( workingDirectory, filename )
else:
    print( "no metadata found!" )

print( "Script DONE!" )