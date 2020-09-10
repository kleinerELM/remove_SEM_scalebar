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
from subprocess import check_output
from tkinter import filedialog

home_dir = os.path.dirname(os.path.realpath(__file__))

ts_path = os.path.dirname( home_dir ) + os.sep + 'tiff_scaling' + os.sep
ts_file = 'set_tiff_scaling'
if ( os.path.isdir( ts_path ) and os.path.isfile( ts_path + ts_file + '.py' ) or os.path.isfile( home_dir + ts_file + '.py' ) ):
    if ( os.path.isdir( ts_path ) ): sys.path.insert( 1, ts_path )
    import set_tiff_scaling as ts
else:
    programInfo()
    print( 'missing ' + ts_path + ts_file + '.py!' )
    print( 'download from https://github.com/kleinerELM/tiff_scaling' )
    sys.exit()

def programInfo():
    print("#########################################################")
    print("# Automatically remove scale bar and set scale for TIFF #")
    print("# images from FEI/Thermofischer Scientific SEM devices  #")
    print("# in a selected folder.                                 #")
    print("#                                                       #")
    print("# © 2020 Florian Kleiner                                #")
    print("#   Bauhaus-Universität Weimar                          #")
    print("#   Finger-Institut für Baustoffkunde                   #")
    print("#                                                       #")
    print("#########################################################")
    print()

#### process given command line arguments
def processArguments():
    global outputDirName
    global showDebuggingOutput
    global sortByPixelSize
    global addScaleBarImage
    global noImageJProcessing
    argv = sys.argv[1:]
    usage = sys.argv[0] + " [-h] [-o] [-s] [-p] [-d]"
    try:
        opts, args = getopt.getopt(argv,"hsb:po:d",[])
    except getopt.GetoptError:
        print( usage )
    for opt, arg in opts:
        if opt == '-h':
            print( 'usage: ' + usage )
            print( '-h,                  : show this help' )
            print( '-o,                  : setting output directory name [' + outputDirName + ']' )
            print( '-s,                  : sort output by pixel size [' + outputDirName + '/1.234nm/]' )
            print( '-p,                  : remove scale bar using PIL (no ImageJ processing, -b is not doing anything)' )
            print( '-b,                  : create a jpg image with an included scale bar [' + str( addScaleBarImage ) + ']' )
            print( '                       scale bar size: 1 = small, 2 = medium, 3 = large' )
            print( '-d                   : show debug output' )
            print( '' )
            sys.exit()
        elif opt in ("-o"):
            outputDirName = arg
            print( 'changed output directory to ' + outputDirName )
        elif opt in ("-s"):
            sortByPixelSize = 1
            print( 'sorting output by pixel size' )
        elif opt in ("-p"):
            noImageJProcessing = True
            print( 'remove scale bar using PIL (faster but no scaling for ImageJ)' )
        elif opt in ("-b"):
            addScaleBarImage = int( arg )
            if ( addScaleBarImage == 3 ):
                print( 'Will create an image including a large scalebar' )
            if ( addScaleBarImage == 2 ):
                print( 'Will create an image including a medium scalebar' )
            else:
                print( 'Will create an image including a small scalebar' )
        elif opt in ("-d"):
            print( 'show debugging output' )
            showDebuggingOutput = True
    print( '' )

#### searching for a set pixel scale in the metadata of the TIFF
def getPixelSizeFromMetaData( directory, filename, silent ):
    global pixelSize
    global metricScale
    global pixelScale
    pixelSize = 0
    with open(directory + os.sep + filename, 'rb', 0) as file, \
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
    with open(directory + os.sep + filename, 'rb', 0) as file, \
        mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_READ) as s:
        ## get original image height
        if s.find(b'ResolutionY') != -1:
            file.seek(s.find(b'ResolutionY'))
            tempLine = str( file.readline() ).split("=",1)[1]
            contentHeight = float( tempLine.split("\\",1)[0] )
    if ( contentHeight > 0 ):
        ## get actual image size of the TIFF
        im = Image.open( directory + os.sep + filename )
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
    if os.path.isdir(directory):
        for file in os.listdir(directory):
            filename = os.fsdecode(file)
            if ( filename.endswith(".jpg") or filename.endswith(".JPG") or filename.endswith(".tif") or filename.endswith(".TIF")):
                print( 'checking if file "{}" has expected metadata'.format(filename), end = '' )
                if getPixelSizeFromMetaData( directory, filename, True ) > 0:
                    result = True
                    break
    else: print(' {} is no direcotry'.format(directory))
    if ( result ) : print( ' [successfull]' ) #colored('hello', 'red'), colored('world', 'green')
    return result

def removeScaleBarPIL( directory, filename, scale ):
    global metricScale
    global pixelScale
    global infoBarHeight
    global outputDirName
    global resultCSVTable

    targetDirectory = directory + os.sep + outputDirName + os.sep

    ## create output directory if it does not exist
    if not os.path.exists( targetDirectory ):
        os.makedirs( targetDirectory )

    im = Image.open( directory + "/" + filename )
    width, height = im.size

    
    scaling = { 'x' : scale, 'y' : scale, 'unit' : 'nm'}

    # Setting the points for cropped image
    left = 0
    top = 0
    right = width
    bottom = height-infoBarHeight

    im1 = im.crop((left, top, right, bottom))
    im1.convert('L').save( targetDirectory + filename , "TIFF", tiffinfo = ts.setImageJScaling( scaling ))
    im.close()
    im1.close()

    resultCSVTable += filename + ',' + str( metricScale ) + ',' + str( infoBarHeight ) + "\n"

### actual program start
if __name__ == '__main__':
    #remove root windows
    root = tk.Tk()
    root.withdraw()

    #### global var definitions
    infoBarHeight = 63
    metricScale = 0
    pixelScale  = 0
    pixelSize = 0
    pixelSize = 0
    outputDirName = "cut"
    showDebuggingOutput = False
    sortByPixelSize = 0
    addScaleBarImage = 0
    noImageJProcessing = False
    createResultCSV = False
    resultCSVTable = ""

    programInfo()

    processArguments()
    if ( showDebuggingOutput ) : print( "I am living in '{}'".format(home_dir) )
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
        print( "{} Tiffs found!".format(count) )
        ## run actual code
        if os.path.isdir( workingDirectory ) :
            ## processing files
            for file in os.listdir(workingDirectory):
                if ( file.endswith(".tif") or file.endswith(".TIF")):
                    filename = os.fsdecode(file)
                    position = position + 1
                    print( " Analysing {} ({}/{}) :".format(filename,position,count) )
                    scale = getPixelSizeFromMetaData( workingDirectory, filename, False )
                    getInfoBarHeightFromMetaData( workingDirectory, filename )
                    removeScaleBarPIL( workingDirectory, filename, scale )                    

            targetDirectoryParent = workingDirectory + os.sep + outputDirName + os.sep
            if createResultCSV:
                scalingCSV = "scaling.csv"
                if ( showDebuggingOutput ) : print( ' writing result CSV: ' + scalingCSV )
                csv_result_file = open( targetDirectoryParent + scalingCSV, 'w' )
                csv_result_file.write( resultCSVTable )
                csv_result_file.close()
                #setImageJScale( workingDirectory )

            if ( sortByPixelSize == 1 ):
                print( " Moving files to their target directories..." )
                for file in os.listdir(workingDirectory):
                    if ( file.endswith(".tif") or file.endswith(".TIF")):
                        filename = os.fsdecode(file)
                        getPixelSizeFromMetaData( workingDirectory, filename, False )

                        srcFile = targetDirectoryParent + filename
                        targetDirectory = targetDirectoryParent + str( metricScale ) + "nm" + os.sep
                        
                        ## create output directory if it does not exist
                        if not os.path.exists( targetDirectory ):
                            os.makedirs( targetDirectory )
                        
                        if ( os.path.isfile( targetDirectory + filename ) ) : 
                            if ( showDebuggingOutput ) : print( "  overwriting file" )
                            os.remove( targetDirectory + filename )

                        os.rename(srcFile, targetDirectory + filename )
                        if ( showDebuggingOutput ) : print( "  moved " + filename )

            #if ( showDebuggingOutput ) : print( "not deleting " + scalingCSV )
            #if ( not showDebuggingOutput ) : os.remove( targetDirectoryParent + scalingCSV )
                
    else:
        print( "no metadata found!" )

    print( "Script DONE!" )