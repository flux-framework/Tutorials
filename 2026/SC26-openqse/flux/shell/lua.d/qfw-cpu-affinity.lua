-- Default the job shell's cpu-affinity plugin to off.
--
-- R for this cluster comes from the [[resource.config]] tables in
-- flux/conf.d/system.toml and is loaded with noverify, so the core ids
-- Fluxion grants a job are synthetic: `cores = "0-3"` says how many cores a
-- node has, not which hwloc cores the container can see. Docker's cpuset 0-3 is host CPUs 0-3, and on a host with SMT that
-- is two cores with two threads each, so a job granted core 3 makes the
-- affinity plugin fail with "core 3 not found in node topology" and print an
-- ERROR line before disabling itself, on every job.
--
-- Pinning is meaningless in this virtual cluster anyway, so turn the plugin
-- off up front. A job that wants it can still pass -o cpu-affinity=per-task
-- (or map:...), which takes precedence over this default.
--
-- Installed under /etc/flux/shell/lua.d, which the default initrc sources
-- for every job shell.

if shell.options["cpu-affinity"] == nil then
    shell.options["cpu-affinity"] = "off"
end

-- vi:ts=4 sw=4 expandtab
