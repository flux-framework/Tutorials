#!/usr/bin/env python

import argparse
import time
import os
import re
import flux
import json
from flux import kvs
from flux.message import Message

parser = argparse.ArgumentParser(description="compute for seconds")
parser.add_argument(
    "integer",
    metavar="S",
    type=int,
    help="an integer for the number of seconds to compute",
)

args = parser.parse_args()

f = flux.Flux()
udata = "conduit"
kvs.put(f, "conduit", udata)
kvs.commit(f)

cr = kvs.get(f, "conduit")
print(cr)

os_time = int(time.time())
payload = {str(os_time): "os.time"}
new_payload = {"data": json.dumps(payload)}
print("Sending ", json.dumps(new_payload))

# this data is ultimately flowed into the data store
f.rpc("conduit.put", new_payload, 0)


time.sleep(args.integer)
