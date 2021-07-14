# MFM Image Reader
This repository contains code intended to assist in the conversion from MFM scans to raw data for artificial spin ice. This folder includes the base code for extracting island data from several different lattice times, as well as some example testing images.
\
For anyone working on this code in the future, please feel free to email me (Grant Fitez) at grant.fitez@yale.edu or grantfitez@gmail.com with any questions.

# Setup
**These instructions are primarily intended for linux. If you are using a different operating system, the exact commands may vary but the overall process should look similar.**
1. Clone or download the repository
2. In your terminal navigate into the outermost folder (the one that this README.md file is in).

3. Start the virtual enviroment:
`sudo python3 -m venv env` <br> 
*Note: If you do not wish to use a virtual enviroment skip steps 3 and 4*

4. Activate the virtual enviroment:
`source env/bin/activate`

5. Install the requirements:
`pip install -r requirements.txt`

6. Confirm the program is working by running one (or more) of the example programs
    - `python PerpendicularKagome-Reader.py TestImages/PerpendicularKagome.bmp`
    - `python SantaFe-Reader.py TestImages/SantaFe_Phase.jpg`
    - `python Square-Reader.py TestImages/Square.jpg`
    - `python YShape-Reader.py TestImages/YShape_Phase.jpg`
# Using the Program
The exact controls and functionality of the program can vary between each lattice implementation and the guide here may not be completely accurate for every single program. However, this section should serve as a general overview of how these MFM reader programs are used.

## Overview 
### The Grid
The program will produce a new window which should show the MFM scan image with a grid over top of it. The four corners of this grid can be moved to align it with the area of interest in the MFM image (or the entire image).

### Adding reference points
One of the primary challenges that this program is meant to solve is that slight distortions and stretching in the scans mean that island color cannot be determined simply by sampling at periodic intervals. To solve this, right-clicking at any vertex will create a "reference point" in that location. This point can be drug around to distort the grid in order to 
conform to the geometry of the sample

### Adjusting rows and columns
<span>nodeNetwork.py</span> has built in functionality to add and remove rows and columns to the grid. In all the example implementations, pressing r/e will add/remove a row and c/x will add/remove a column.

### Reference Image
In lattice types with complicated or hard to read geometries (e.g. Santa Fe, Y-shape) it is convenient to provide a secondary reference image to help align the points. In most cases this will be the height image from the MFM scan. This allows the user to align the grid with an easier to read image before switching back to the phase image. Adding a reference image does not have an impact on the program output. Usually it can be toggled by pressing "a".

### Sample Points
Depending on the implementation, you will see a pattern of "sample points" overlayed onto the image. These points are intended align above areas of the image which describe the island layout. Blue points indicate a black sample and red points indicate a white sample. In most lattices with a simple island shape, there will be two sample points on an island: 1 for the black side, 1 for the white side. As a user, it should be your goal to make adjustments to the grid so that all islands are read correctly.

### Errors
For some lattice geometries, it is possible to detect errors automatically. For example, most islands will have a black side and white side so reading 2 white or 2 black means that an error has occured. This will result in a green circle being draw on or near the offending island. Errors do not effect the output of the program; they are merely used as a tool to make sure everything is aligned.

### Manual corrections
Lastly, it is possible for the user to make manual corrections to the sample points before saving. In most implementations shift/ctrl clicking on a sample point will toggle its color between red, blue, and green. Green indicates that the point is unreadable.<br>
**Note: All manually corrections will be reset if the grid is adjusted later. Make sure that manual corrections are the last thing you do before saving the image.**


## Step-by-step guide

1. run `python [yourProgamName].py [mfmImage].jpg`<br>You can optionally add more arguments such as `-a [heightImage].jpg`
2. Align the grid over the area you want to read.<br>
<img src="docs/size_grid.png" width=300/>
3. Add rows and columns until you have the same number of squares and areas you want to sample. Don't worry about exact alignment at this point.<br>
<img src="docs/align_rows+cols.png" width=300/>
4. In areas where the grid is misaligned, add additional reference points and drag them to adjust the location of the sample points.<br>
<img src="docs/align_reference_points.png" width=300/>
*Note that reference points were added in the area with a lot of green circles and moved slightly to reduce the number of errors.*
5. After the majority of points have been aligned correctly, manually correct errors and mark points as unreadable if necessary.
6. Close the program (usually by hitting "Enter"). The data should save automatically.


## Structure
The premise of this program is that a movable, stretchable grid can be aligned over top of an MFM phase image in order to sample the image at the correct island locations. All code relating the implementation of this "adjustable grid" is contained in the abstract `NodeNetwork` class inside <span>nodeNetwork.py</span>. `NodeNetwork` is also responsible for determining the island color at each sample point. <br><br>
Each lattice-specific implementation needs to import <span>nodeNetwork.py</span> and declare a new class which inherits from `NodeNetwork`. From here, the program should implement several methods inside the which relate to that specific lattice. See the next section for more details.


## TODO
- Put a border around the images to make dragging points easier
- Add buttons controls
- Save manual corrections, even after grid is adjusted


## Technical Stuff
### <span>nodeNetwork.py</span>
### Modification for a different lattice design


