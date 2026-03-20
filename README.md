# meshtastic-sat-station

This project was created for (Hack Club Stasis)[stasis.hackclub.com].

I created this project because I noticed weather stations are common in urban lora meshes, but don't provide a lot of data. My project solves this issue by receiving global weather data on demand from mesh users, and works fully off grid. It is designed in the form of a deployable kit that SAR teams or civillians can set up quickly and leave for a few days, and it can run completely self-sufficient with no outside power source (for a few days).

BOM link: (here)[https://docs.google.com/spreadsheets/d/1USlBK-dkPbo43bPHNxUITIbZjwFQk0WdP9H-Rfz2vz8/edit?usp=sharing]


## Design

I did lots of research on this project, and here is what I came up with:


### Antenna 1

I am using a 3D printed helical antenna tuned for 1692.7 MHz, which is the frequency that GOES EMWIN East communicates on. I chose a 3d printed approach to save space in the casing, and costs in the BOM.

-

### Antenna 2

For communicating on the mesh, I chose a generic 915MHz fiberglass antenna. This should be reliable enough for multi-day high density operation, and at 5.8dbm plenty powerful.

-

### Mesh Node

I am using the RAKWireless nRF52 based node with the RAK19007 base board

-
 
### Case

The case is a bit special. I chose a generic 8x11x5in pelican case, which will have holes drilled in it for:
 - The solar gland
 - Multiple screw/bolt holes
 - SMA bulkheads
 - Antenna mount
 - 3d print mounting holes

The left side will be taken up by a 3d printed box housing the electronics, and the right side will be for storage of deployable components.

-
