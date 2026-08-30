-- oven-timer.lua : a Flux job shell plugin skeleton.
--
-- Run it against a single job without installing anything:
--
--     flux run -o userrc=plugin-workshop/oven-timer.lua -n2 hostname
--
-- Add -o verbose=2 to see the shell's own tracing alongside your output.
--
-- The structure below is complete. The behavior is yours to write.
-- See flux-shell-initrc(5) for the full API.

-- Somewhere to keep state between callbacks. Each shell rank gets its own copy.
local started = {}

plugin.register {
  name = "oven-timer",

  handlers = {
    {
      -- Fires in the parent process, just after each local task is forked.
      -- Available: task.info.rank, task.info.localid, task.info.pid
      topic = "task.fork",
      fn = function ()
        -- YOUR CODE HERE.
        -- The task just went into the oven. Record something about it in
        -- `started`, keyed on task.info.rank.
      end
    },

    {
      -- Fires once each local task has exited.
      -- Available: everything above, plus task.info.exitcode and
      -- task.info.signaled.
      topic = "task.exit",
      fn = function ()
        -- YOUR CODE HERE.
        -- The task came out. Report on it with shell.log(), or complain with
        -- shell.log_error() if it burned.
      end
    },

    {
      -- Fires once, after every local task has exited.
      -- Available: shell.info.rank, shell.info.size, shell.info.ntasks
      topic = "shell.finish",
      fn = function ()
        -- YOUR CODE HERE (optional).
        -- Summarize the whole order for this shell rank.
      end
    }
  }
}

-- Ideas, if you want them:
--
--   * Time each task with os.clock() and print the slowest one.
--   * Stamp every task with an environment variable in a "task.init" handler,
--     using task.setenv().
--   * Count tasks per shell rank and log the total in shell.finish.
--   * Register a handler on topic "*" and log every callback the shell makes,
--     to see the lifecycle for yourself.
