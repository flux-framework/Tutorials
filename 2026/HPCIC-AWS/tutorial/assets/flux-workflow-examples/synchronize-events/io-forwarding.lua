#!/usr/bin/env lua

local flux = require 'flux'
local f = flux.new ()
local amount = tonumber (arg[1]) or 120

local function sleep (n)
    os.execute ("sleep " .. n)
end

if #arg ~= 1 then
   print ("Usage: io-forward.lua seconds")
   print ("    Forward I/O requests for seconds")
   os.exit (1)
end

local rc, err = f:sendevent ({ data = "please proceed" }, "app.iof.go")
if not rc then error (err) end
print ("Sent a go event")

print ("Will forward IO requests for " .. amount .. " seconds")
sleep (amount) 

