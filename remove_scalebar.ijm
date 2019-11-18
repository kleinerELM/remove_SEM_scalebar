// Macro for ImageJ 1.52d for Windows
// written by Florian Kleiner 2019
// run from command line as follows
// ImageJ-win64.exe -macro "C:\path\to\remove_scalebar.ijm" "D:\path\to\data\|infoBarheight|metricScale|pixelScale"

macro "remove_SEMScaleBar" {
	// check if an external argument is given or define the options
	arg = getArgument();
	if ( arg == "" ) {
		dir = getDirectory("Choose a Directory");
		//define number of slices for uniformity analysis
		infoBarHeight	= 63; // height of the info bar at the bottom of SEM images
		metricScale		= 0; // size for the scale bar in nm
		pixelScale		= 0; // size for the scale bar in px
	} else {
		print("arguments found");
		arg_split = split(getArgument(),"|");
		dir				= arg_split[0];
		infoBarHeight	= parseInt(arg_split[1]);
		metricScale		= parseFloat(arg_split[2]);
		pixelScale		= parseInt(arg_split[3]);
	}
	print("Starting process using the following arguments...");
	print("  Directory: " + dir);
	print("  argument based image-scale: " + pixelScale + " px / " + metricScale + " nm");
	if ( metricScale == 0 || pixelScale == 0 ) {
		do_scaling = false;
		print("  No image-scaling set! Calculation only pixel values!");
	} else {
		do_scaling = true;
		scaleX = metricScale/pixelScale;
		print( "  Set scale 1 px = " + scaleX + " nm" );
	}
	print("Info bar height: " + infoBarHeight + " px");
	print("------------");
	
	//directory handling
	outputDir_Cut = dir + "/cut/";
	File.makeDirectory(outputDir_Cut);
	list = getFileList(dir);
	
	// running main loop
	setBatchMode(true);
	for (i=0; i<list.length; i++) {
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
				baseName		= substring(filename, 0, lengthOf(filename)-4);
				cutName			= baseName + "-cut.tif";
				scaleName		= baseName + "-scale.jpg";
				
				//////////////////////
				// image constants
				//////////////////////
				width			= getWidth();
				height			= getHeight();
				if ( do_scaling ) {
					run("Set Scale...", "distance=" + pixelScale + " known=" + metricScale + " pixel=1 unit=nm");
				}
				
				//////////////////////
				// processing
				//////////////////////
				print( "  removing bar ..." );
				makeRectangle(0, 0, width, height-infoBarHeight); // remove info bar
				run("Crop");
				run("8-bit"); // convert to 8-bit-grayscale
				saveAs("Tiff", outputDir_Cut + cutName );

				//////////////////////
				// add scalebar jpg
				//////////////////////
				scaleWidth = 500; //nm
				scaleHeight = round( 0.007 * height );
				run("Scale Bar...", "width=" + scaleWidth + " height=" + scaleHeight + " font=25 color=White background=None location=[Lower Right] bold overlay");
				saveAs("Jpeg", outputDir_Cut + scaleName );

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
