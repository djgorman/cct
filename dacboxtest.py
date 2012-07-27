import ok
import time
from struct import Struct
xem = ok.FrontPanel()

xem.OpenBySerial("")

xem.GetDeviceID()

#This line load a configuration file into the FPGA#

xem.ConfigureFPGA("/home/cct/LabRAD/cct/okfpgaservers/pulser2/photon.bit")

# pos 1 = \x08
# set 1 = \x02
xem.WriteToBlockPipeIn(0x82,2,"\x00\x00\x00\x00")
xem.WriteToBlockPipeIn(0x82,2,"\x00\x00")
