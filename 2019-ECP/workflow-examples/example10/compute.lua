#!/usr/bin/env lua

local f = assert (require 'flux' .new ())
local amount = tonumber (arg[1]) or 120

local function sleep (n)
    os.execute ("sleep " .. n)
end

if #arg ~= 1 then
   print ("Usage: compute.lua seconds")
   print ("    Compute for seconds")
   os.exit (1)
end

-- conduit is the KVS key that conduit module puts to publishing 
-- the rank in which it is loaded
cr = f:kvs_get ("conduit") or -1

if cr == -1 then
    print ("conduit key is not available")
    os.exit (1)
end

payload = '{"' .. os.time () .. '": "os.time"}'
print ("Sending " .. payload)

-- this data is ultimately flowed into the data store
local rc, err = f:send ("conduit.put", { data  = payload }, cr)
if rc < 0 then
    print ("error sending a conduit.put request")
    os.exit (1)
end

print ("Will compute for " .. amount .. " seconds")
sleep (amount) 

-- vi: ts=4 sw=4 expandtab
