#!/usr/bin/env python

import socket
import struct
import json
import sys
import os

sockdir = os.path.join("/tmp", os.environ['USER'])
sockname = os.path.join(sockdir, "mysock")

store = {}
sock = ""

def initialize ():
    global sock
    if not os.path.exists(sockdir):
        os.mkdir(sockdir)
    if os.path.exists (sockname):
        os.remove (sockname)
    sock = socket.socket (socket.AF_UNIX, socket.SOCK_STREAM)
    sock.bind (sockname)
    sock.listen (1)
    cmd = "flux module load ./conduit.so"
    os.system (cmd)

def run ():
    global sock
    global store
    connection, client_address = sock.accept()
    for x in range (5):
       print "Waiting for a packet"
       mybytes = bytearray (4)
       nbytes, address = connection.recvfrom_into (mybytes, 4)
       if nbytes == 0:
            break;
       size = mybytes[0]*1 + mybytes[1]*256 + mybytes[2]*65536 + mybytes[3]*16777216
       data = bytearray (size)
       nbytes, address = connection.recvfrom_into (data, size)
       dict_blob = json.loads (data.decode ("ascii"))

       if dict_blob is not None:
           store.update (dict_blob)
           print store
       else:
           print "Mallformed data, discarding"

    connection.close ()
    cmd = "flux module remove conduit"
    os.system (cmd)
    print "Bye bye!"

def main ():
    print "Starting...."
    initialize ()
    run ()

if __name__ == "__main__":
    main ()
