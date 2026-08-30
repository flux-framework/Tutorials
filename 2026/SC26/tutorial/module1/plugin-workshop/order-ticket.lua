-- order-ticket.lua : a complete Flux job shell plugin, for reference.
--
--     flux run -o userrc=plugin-workshop/order-ticket.lua -n4 env
--
-- Stamps each task with a PIZZA_TICKET environment variable holding its global
-- rank, then reports on each task as it exits.

local tickets = 0

plugin.register {
  name = "order-ticket",

  handlers = {
    {
      topic = "task.init",
      fn = function ()
        task.setenv ("PIZZA_TICKET", tostring (task.info.rank))
        tickets = tickets + 1
      end
    },

    {
      topic = "task.exit",
      fn = function ()
        local info = task.info
        if info.exitcode and info.exitcode ~= 0 then
          shell.log_error (string.format ("ticket %d burned (exit %d)",
                                          info.rank, info.exitcode))
        elseif info.signaled then
          shell.log_error (string.format ("ticket %d was dropped (signal %d)",
                                          info.rank, info.signaled))
        else
          shell.log (string.format ("ticket %d is up", info.rank))
        end
      end
    },

    {
      topic = "shell.finish",
      fn = function ()
        shell.log (string.format ("shell rank %d served %d ticket(s)",
                                  shell.info.rank, tickets))
      end
    }
  }
}
