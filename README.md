# svimove
Moves SVIs between Meraki MS stacks

This is a script to move layer 3 switched virtual interfaces (SVIs) from a list of servers to a second list of servers.
The script will read and compare the SVIs between the target switches and ensure they are identical.  Any errors or
deviations will be printed to console.  Once the errors are clear, the SVIs will be created on the destination
switches.

This script moves a list of SVIs from a source switch to a destination switch.  This script will not configure
full DHCP Servers.  It will copy DHCP disabled and DHCP relays ONLY.

Authored by Brian Buxton
This is created under the Cisco Sample Code License v1.1.  See LICENSE file for terms.
