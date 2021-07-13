# MFM Image Reader
This repository contains code intended to assist in the conversion from MFM scans to raw data for artificial spin ice. This folder includes the base code for extracting island data from several different lattice times, as well as some example testing images.
\
For anyone working on this code in the future, please feel free to email me (Grant Fitez) at grant.fitez@yale.edu or grantfitez@gmail.com with any questions.

## Setup
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
## Using the Program
The exact controls and functionality of the program can vary between each lattice implementation and the guide here may not be completely accurate for every single program. However, this section should serve as a general overview of how these MFM reader programs are used.
### The Grid
The program will produce a new window which should show the MFM scan image with a grid over top of it. The four corners of this grid can be moved to align it with the area of interest in the MFM image.
### Adding reference points
One of the primary challenges that this program is meant to solve is that slight distortions and stretching in the scans mean that island color cannot be determined simply by sampling at periodic intervals. To solve this, right-clicking at any vertex will create a "reference point" in that location
## Structure
The premise of this program is that a movable, stretchable grid can be aligned over top of an MFM phase image in order to sample the image at the correct island locations. All code relating the implementation of this "adjustable grid" is contained in the abstract `NodeNetwork` class inside <span>nodeNetwork.py</span>. `NodeNetwork` is also responsible for determining the island color at each sample point. <br><br>
Each lattice-specific implementation needs to import <span>nodeNetwork.py</span> and declare a new class which inherits from `NodeNetwork`. From here, the program should implement several methods inside the which relate to that specific lattice. See the next section for more details.



## Technical Stuff
### <span>nodeNetwork.py</span>
### Modification for a different lattice design


