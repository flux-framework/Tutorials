#!/usr/bin/env lua

local amount = tonumber (arg[1]) or 120

local function sleep (n)
    os.execute ("sleep " .. n)
end

if #arg ~= 1 then
   print ("Usage: io-forward.lua seconds")
   print ("    Forward I/O requests for seconds")
   os.exit (1)
end

print ("Will forward IO requests for " .. amount .. " seconds")
sleep (amount) 

-- vi: ts=4 sw=4 expandtab
