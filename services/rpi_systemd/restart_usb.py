from usb.core import find as finddev
finddev(idVendor=0x2752).reset()
