#!/usr/bin/env lua

local flux = require 'flux'
local f = flux.new ()
local amount = tonumber (arg[1]) or 120
local rank = tonumber (os.getenv('FLUX_TASK_RANK')) or 0
local frank = tonumber (os.getenv('FLUX_LOCAL_RANKS')) or 0
io.stdout:setvbuf ("no")

local function sleep (n)
    os.execute ("sleep " .. n)
end

if #arg ~= 1 then
   print ("Usage: io-forward.lua seconds")
   print ("    Forward I/O requests for seconds")
   os.exit (1)
end

-- subscribe  app.comp.go event
local rc, err = f:subscribe ("app.comp.go")
if not rc then
    print ("Failed to subscribe an event, %s", err)
    os.exit (1)
end

if rank == 0 then
    os.execute ("flux module load -r " .. 0 .. " ioapp")
    os.execute ("flux module list")
    local rc, err = f:sendevent ({ data = "please proceed" }, "app.io.go")
    if not rc then error (err) end
    print ("Sent a go event")
end

-- Wait for an event sent from the leader of compute job to sync
-- between compute job's installing the app module and sending a request later
print ("Block until we hear go message from the a leader compute process")
local rc, err = f:recv_event ()
if not rc then
    print ("Failed to receive an, %s", err)
    os.exit (1)
end

local resp, err = f:rpc ("capp.comp", { data = rank })
if not resp then
    if err == "Function not implemented" then
        print ("capp.comp request handler isn't loaded")
    else
        print (err)
    end
end

print ("Will forward IO requests for " .. amount .. " seconds")
sleep (amount)
f:unsubscribe ("app.comp.go")

-- vi: ts=4 sw=4 expandtab
