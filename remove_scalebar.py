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


def getBaseSettings():
    settings = {
        "showDebuggingOutput" : False,
        "home_dir"            : os.path.dirname(os.path.realpath(__file__)),
        "workingDirectory"    : "",
        "outputDirectory"     : "cut",
        "addScaleBarImage"    : 0,
        "createResultCSV"     : False,
        "sortByPixelSize"     : 1
    }
    return settings

#### process given command line arguments
def processArguments():
    settings = getBaseSettings()
    argv = sys.argv[1:]
    usage = sys.argv[0] + " [-h] [-o] [-s] [-d]"
    try:
        opts, args = getopt.getopt(argv,"hso:d",[])
    except getopt.GetoptError:
        print( usage )
    for opt, arg in opts:
        if opt == '-h':
            print( 'usage: ' + usage )
            print( '-h,                  : show this help' )
            print( '-o,                  : setting output directory name [{}]'.format(settings["outputDirectory"]) )
            print( '-s,                  : sort output by pixel size [{}/1.234nm/]'.format(settings["outputDirectory"] ))
            #print( '-p,                  : remove scale bar using PIL (no ImageJ processing, -b is not doing anything)' )
            #print( '-b,                  : create a jpg image with an included scale bar [{}]'.format(settings["addScaleBarImage"] )
            #print( '                       scale bar size: 1 = small, 2 = medium, 3 = large' )
            print( '-d                   : show debug output' )
            print( '' )
            sys.exit()
        elif opt in ("-o"):
            settings["outputDirectory"] = arg
            print( 'changed output directory to ' + settings["outputDirectory"] )
        elif opt in ("-s"):
            settings["sortByPixelSize"] = 1
            print( 'sorting output by pixel size' )
        #elif opt in ("-p"):
        #    noImageJProcessing = True
        #    print( 'remove scale bar using PIL (faster but no scaling for ImageJ)' )
        elif opt in ("-b"):
            settings["addScaleBarImage"] = int( arg )
            if ( settings["addScaleBarImage"] == 3 ):
                print( 'Will create an image including a large scalebar' )
            if ( settings["addScaleBarImage"] == 2 ):
                print( 'Will create an image including a medium scalebar' )
            else:
                print( 'Will create an image including a small scalebar' )
        elif opt in ("-d"):
            print( 'show debugging output' )
            settings["showDebuggingOutput"] = True
    print( '' )
    return settings

#### searching for a set pixel scale in the metadata of the TIFF
def getPixelSizeFromMetaData( directory, filename, verbose=False ):
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
            if ( verbose ) : print( "  detected image scale: {} nm / px".format(pixelSize) )
    return pixelSize

#### determining the height of the info / scale bar in the TIFF
def getInfoBarHeightFromMetaData( directory, filename, verbose=False ):
    contentHeight = 0
    infoBarHeight = 63
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
        ## calculate the difference, which is the info bar height
        infoBarHeight = int( height - contentHeight )
        if verbose: print( "  detected info bar height: {} px".format(infoBarHeight) )# + str( height ) + '|' + str(contentHeight))
    else:
        if verbose: print( "  info bar height not detected" )
    return infoBarHeight

#### check if the expected metadata in the first file of a directory is present
def scaleInMetaData( directory ):
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

def removeScaleBarPIL( directory, filename, targetDirectory, infoBarHeight=False, scaling=False, verbose=False ):
    if infoBarHeight==False: infoBarHeight = getInfoBarHeightFromMetaData( directory, filename, verbose=verbose )

    ## create output directory if it does not exist
    if not os.path.exists( targetDirectory ):
        os.makedirs( targetDirectory )

    im = Image.open( directory + os.sep + filename )
    width, height = im.size

    # Setting the points for cropped image
    left = 0
    top = 0
    right = width
    bottom = height-infoBarHeight

    im1 = im.crop((left, top, right, bottom))
    if scaling == False:
        im1.convert('L').save( targetDirectory + filename , "TIFF")
    else:
        im1.convert('L').save( targetDirectory + filename , "TIFF", tiffinfo = ts.setImageJScaling( scaling ))
    im.close()
    im1.close()
    return 

def extendCSVTable(infoBarHeight=63):
    global metricScale
    global resultCSVTable

    resultCSVTable += filename + ',' + str( metricScale ) + ',' + str( infoBarHeight ) + "\n"

### actual program start
if __name__ == '__main__':
    #remove root windows
    root = tk.Tk()
    root.withdraw()

    #### global var definitions
    metricScale = 0
    pixelScale  = 0
    resultCSVTable = ""

    programInfo()

    settings = processArguments()
    if settings["showDebuggingOutput"]: print( "I am living in '{}'".format(settings["home_dir"]) )
    settings["workingDirectory"]  = filedialog.askdirectory(title='Please select the image / working directory')
    if settings["showDebuggingOutput"]: print( "Selected working directory: " + settings["workingDirectory"]  )

    if scaleInMetaData( settings["workingDirectory"]  ) :
        count = 0
        position = 0
        ## count files
        if os.path.isdir( settings["workingDirectory"]  ) :
            for file in os.listdir(settings["workingDirectory"] ):
                if ( file.endswith(".tif") or file.endswith(".TIF")):
                    count = count + 1
        print( "{} Tiffs found!".format(count) )
        ## run actual code
        if os.path.isdir( settings["workingDirectory"]  ) :
            targetDirectory = settings["workingDirectory"] + os.sep + settings["outputDirectory"] + os.sep
            ## processing files
            for file in os.listdir(settings["workingDirectory"] ):
                if ( file.endswith(".tif") or file.endswith(".TIF")):
                    filename = os.fsdecode(file)
                    position = position + 1
                    print( " Analysing {} ({}/{}) :".format(filename, position, count) )
                    infoBarHeight = getInfoBarHeightFromMetaData( settings["workingDirectory"], filename, verbose=settings["showDebuggingOutput"] )
                    scale = getPixelSizeFromMetaData( settings["workingDirectory"] , filename )
                    scaling = { 'x' : scale, 'y' : scale, 'unit' : 'nm'}
                    removeScaleBarPIL( settings["workingDirectory"], filename, targetDirectory, infoBarHeight, scaling )
                    if settings["createResultCSV"]: extendCSVTable(infoBarHeight)            

            if settings["createResultCSV"]:
                scalingCSV = "scaling.csv"
                if settings["showDebuggingOutput"]: print( ' writing result CSV: ' + scalingCSV )
                csv_result_file = open( targetDirectory + scalingCSV, 'w' )
                csv_result_file.write( resultCSVTable )
                csv_result_file.close()
                #setImageJScale( workingDirectory )

            if ( settings["sortByPixelSize"] == 1 ):
                print( " Moving files to their target directories..." )
                for file in os.listdir(settings["workingDirectory"]):
                    if ( file.endswith(".tif") or file.endswith(".TIF")):
                        filename = os.fsdecode(file)
                        getPixelSizeFromMetaData( settings["workingDirectory"], filename )

                        srcFile = targetDirectory + filename
                        targetDirectoryPerScale = targetDirectory + str( metricScale ) + "nm" + os.sep
                        
                        ## create output directory if it does not exist
                        if not os.path.exists( targetDirectoryPerScale ):
                            os.makedirs( targetDirectoryPerScale )
                        
                        if ( os.path.isfile( targetDirectoryPerScale + filename ) ) : 
                            if settings["showDebuggingOutput"]: print( "  overwriting file" )
                            os.remove( targetDirectoryPerScale + filename )

                        os.rename(srcFile, targetDirectoryPerScale + filename )
                        if settings["showDebuggingOutput"]: print( "  moved " + filename )
               
    else:
        print( "no metadata found!" )

    print( "Script DONE!" )