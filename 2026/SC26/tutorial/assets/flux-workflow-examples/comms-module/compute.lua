#!/usr/bin/env lua

local f, err = require 'flux' .new ()
local amount = tonumber (arg[1]) or 120
local rank = tonumber (os.getenv('FLUX_TASK_RANK')) or 0
local frank = tonumber (os.getenv('FLUX_LOCAL_RANKS')) or 0
io.stdout:setvbuf ("no")

local function sleep (n)
    os.execute ("sleep " .. n)
end

if #arg ~= 1 then
   print ("Usage: compute.lua seconds")
   print ("    Compute for seconds")
   os.exit (1)
end

-- subscribe  app.io.go event
local rc, err = f:subscribe ("app.io.go")
if not rc then
    print ("Failed to subscribe an event, %s", err)
    os.exit (1)
end

-- the leader rank of compute job installs app module
if rank == 0 then
    os.execute ("flux module load -r " .. 0 .. " capp")
    os.execute ("flux module list")
end

-- wait for an event sent from the leader of io-forwarding job to sync
-- between io job's installing the app module and sending a request later
print ("Block until we hear go message from the an io forwarder")
local rc, err = f:recv_event ()
if not rc then
    print ("Failed to receive an event, %s", err)
    os.exit (1)
end

if rank == 0 then
    local rc, err = f:sendevent ({ data = "please proceed" }, "app.comp.go")
    if not rc then error (err) end
    print ("Sent a go event")
end

local resp, err = f:rpc ("ioapp.io", { data = rank })
if not resp then
    if err == "Function not implemented" then
        print ("ioapp.io request handler isn't loaded")
    else
        print (err)
    end
else
    print ("Count so far: " .. resp.count)
end

print ("Will compute for " .. amount .. " seconds")
sleep (amount)
f:unsubscribe ("app.io.go")

-- vi: ts=4 sw=4 expandtab
