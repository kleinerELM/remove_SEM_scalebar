// Macro for ImageJ 1.52d for Windows
// written by Florian Kleiner 2019
// run from command line as follows
// ImageJ-win64.exe -macro "C:\path\to\remove_scalebar.ijm" "D:\path\to\data\|infoBarheight|metricScale|pixelScale|addScaleBarImage"

macro "remove_SEMScaleBar" {
	// check if an external argument is given or define the options
	arg = getArgument();
	if ( arg == "" ) {
		dir = getDirectory("Choose a Directory");
		//define number of slices for uniformity analysis
		infoBarHeight	= 63; // height of the info bar at the bottom of SEM images
		metricScale		= 0; // size for the scale bar in nm
		pixelScale		= 0; // size for the scale bar in px
		addScaleBarImage = 0;
		outputDirName	= "cut";
	} else {
		print("arguments found: " + arg);
		arg_split = split(getArgument(),"|");
		dir				= arg_split[0];
		outputDirName	= arg_split[1];
		infoBarHeight	= parseInt(arg_split[2]);
		metricScale		= parseFloat(arg_split[3]);
		pixelScale		= parseInt(arg_split[4]);
		addScaleBarImage = parseInt(arg_split[5]);
	}
	//directory handling
	if ( outputDirName != "-" ) {
		outputDir_Cut = dir + "/" + outputDirName + "/";
		File.makeDirectory(outputDir_Cut);
	} else {
		outputDir_Cut = dir ;
	}
	foundScalingCSV = File.exists( dir + "/scaling.csv" );
	print("Starting process using the following arguments...");
	print("  Directory: " + dir );
	print("  outputDirName: " + outputDirName );
	print("  argument based image-scale: " + pixelScale + " px / " + metricScale + " nm");
    if ( addScaleBarImage > 0 ) {
		if ( addScaleBarImage == 2 ) {
			print( "  jpg image including a medium scalebar will be created" );
		} else if ( addScaleBarImage == 3 ) {
			print( "  jpg image including a large scalebar will be created" );
		} else {
			print( "  jpg image including a small scalebar will be created" );
		}
    } else {
        print( "  no jpg image including a scalebar will be created" );
    }
	if ( foundScalingCSV ) {
		print("  Found CSV for image scaling!");
	} else {
		if ( metricScale == 0 || pixelScale == 0 ) {
			do_scaling = false;
			print("  No image-scaling set! Calculation only pixel values!");
		} else {
			do_scaling = true;
			scaleX = metricScale/pixelScale;
			print( "  Set scale 1 px = " + scaleX + " nm" );
		}
	}
	print("  Info bar height: " + infoBarHeight + " px");
	print("------------");
	print("");
	
	list = getFileList(dir);
	
	if ( foundScalingCSV ) {
        lineseparator = "\n";
        cellseparator = ",";

        // copies the whole RT to an array of lines
        lines = split( File.openAsString( dir + "/scaling.csv" ), lineseparator );
        
        scalingArrayFileName = newArray();
        scalingArrayScale = newArray(); 
        scalingArrayIBH = newArray();
        // recreates the columns headers
        for ( j=0; j<lines.length; j++ ) {
            value = split( lines[j], cellseparator );
            scalingArrayFileName = Array.concat( scalingArrayFileName, value[0] );
            scalingArrayScale = Array.concat( scalingArrayScale, value[1] );
            scalingArrayIBH = Array.concat( scalingArrayIBH, value[2] );
        }
	}
	
	// running main loop
	setBatchMode(true);
	for ( i = 0; i < list.length; i++ ) { // list.length
		path = dir+list[i];
		// get all files
		showProgress(i, list.length);
		// select only images
		if (!endsWith(path,"/") && ( endsWith(path,".tif") || endsWith(path,".jpg") || endsWith(path,".JPG") ) ) {
			open(path);
			imageId = getImageID();
			// get image id to be able to close the main image
			if (nImages>=1) {
				//////////////////////
				// name definitions
				//////////////////////
				filename = getTitle();
				print( filename );
				baseName		= substring( filename, 0, lengthOf( filename ) - 4 );
				cutName			= baseName + "-cut.tif";
				scaleName		= baseName + "-scale.jpg";
				scaleEnhName		= baseName + "-enh-scale.jpg";
				
				//////////////////////
				// read out scaling from CSV
				//////////////////////
				if ( foundScalingCSV ) {
					do_scaling = false;
					for (j=0; j<scalingArrayFileName.length; j++) {
						if ( scalingArrayFileName[j] == filename ) {
							do_scaling = true;
							print( "  scaling found!" );
							pixelScale = 1;
							metricScale = parseFloat( scalingArrayScale[j] );
                            infoBarHeight = parseInt( scalingArrayIBH[j] );
							// overwrite existing files!
							cutName = filename;
                            scaleName = baseName + ".jpg";
						}
					}
				}
				
				//////////////////////
				// image constants
				//////////////////////
				width			= getWidth();
				height			= getHeight();
				if ( do_scaling ) {
					unit = "nm";
					scaledImageWidth = width * metricScale;
					
					if ( scaledImageWidth > 1500000  ) { // to mm
						metricScale = metricScale / 1000000;
						unit = "mm";
					} else if ( scaledImageWidth > 1500 ) { // to micrometer
						mu = fromCharCode(181);
						metricScale = metricScale / 1000;
						unit = mu + "m";
					}
					scaledImageWidth = width * metricScale;
					print( "  Set Scale to " + metricScale + " " + unit + "/px " );
					run("Set Scale...", "distance=" + pixelScale + " known=" + metricScale + " pixel=1 unit=" + unit);
				}
				
				//////////////////////
				// processing
				//////////////////////
				if ( infoBarHeight > 0 ) {
					print( "  cropping image bar (height: " + infoBarHeight + " px)" );
					makeRectangle(0, 0, width, height-infoBarHeight); // remove info bar
					print( "  saving file as " + cutName + " ..." );
					run("Crop");
					run("8-bit"); // convert to 8-bit-grayscale
				}
				saveAs("Tiff", outputDir_Cut + cutName );

				//////////////////////
				// add scalebar jpg
				//////////////////////
				if ( addScaleBarImage > 0 && do_scaling ) {
					scaleWidth = 1;
					if ( scaledImageWidth > 700 ){
						scaleWidth = 500; //nm
					} else if ( scaledImageWidth > 300 ){
						scaleWidth = 250; //nm
					} else if ( scaledImageWidth > 120 ){
						scaleWidth = 100; //nm
					} else if ( scaledImageWidth > 120 ){
						scaleWidth = 100; //nm
					} else if ( scaledImageWidth > 12 ){
						scaleWidth = 10; //nm
					} else if ( scaledImageWidth >= 6 ) {
						scaleWidth = 5; //nm
					} 
					scaleHeight = round( addScaleBarImage * 0.007 * height );
					fontSize = 4 * scaleHeight;
					run("Scale Bar...", "width=" + scaleWidth + " height=" + scaleHeight + " font=" + fontSize + " color=White background=None location=[Lower Right] bold overlay");
					saveAs("Jpeg", outputDir_Cut + scaleName );
					run("Enhance Contrast...", "saturated=0.3 normalize");
					saveAs("Jpeg", outputDir_Cut + scaleEnhName );
				}

				//////////////////////
				// close this file
				//////////////////////
				print( "  closing file ..." );
				selectImage(imageId);
				close();
				print( "" );
			}
		}
	}
	// exit script
	print("Done!");
	if ( arg != "" ) {
		run("Quit");
	}
}
