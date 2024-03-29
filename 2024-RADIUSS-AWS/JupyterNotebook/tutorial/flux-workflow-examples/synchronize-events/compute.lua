#!/usr/bin/env lua

local f, err = require 'flux' .new ()

local amount = tonumber (arg[1]) or 120

local function sleep (n)
    os.execute ("sleep " .. n)
end

if #arg ~= 1 then
   print ("Usage: compute.lua seconds")
   print ("    Compute for seconds")
   os.exit (1)
end

print ("Block until we hear go message from the an io forwarder")
f:subscribe ("app.iof.go")
local t, tag = f:recv_event ()
print ("Recv an event: " .. t.data )
print ("Will compute for " .. amount .. " seconds")
sleep (amount) 

