# Using a Flux Comms Module

## Description: Use a Flux comms module to communicate with job elements

### Setup

If you haven't already, download the files and change your working directory:

```bash
$ cd flux-workflow-examples/comms-module
```

### Execution

If you need to get an allocation on Slurm:

```bash
salloc -N3 -ppdebug
```

Point to `flux-core`'s `pkgconfig` directory:

| Shell     | Command                                                      |
| -----     | ----------                                                   |
| tcsh      | `setenv PKG_CONFIG_PATH <FLUX_INSTALL_PATH>/lib/pkgconfig`   |
| bash/zsh  | `export PKG_CONFIG_PATH='<FLUX_INSTALL_PATH>/lib/pkgconfig'` |

This might look like this in the container:

```bash
export PKG_CONFIG_PATH=/usr/lib/pkgconfig
```

Then build the module (if you don't have permission, copy to /tmp)

```bash
cp -R ./comms-module /tmp/comms-module
cd /tmp/comms-module
make
```

Add the directory of the modules to `FLUX_MODULE_PATH`; if the module was
built in the current dir:

```bash
flux module load ioapp.so
flux module load capp.so
export FLUX_MODULE_PATH=${FLUX_MODULE_PATH}:$(pwd)
```

Now let's try it! If you need to run flux start under Slurm:

```bash
srun --pty --mpi=none -N3 flux start -o,-S,log-filename=out
```

Try running flux with the module on the path.

```bash
flux run -N 1 -n 2 ./compute.lua 120
flux run -N 1 -n 2 ./io-forwarding.lua 120
```
Notice that the module is loaded (at the bottom):

```console
Try `flux-module load --help' for more information.
Module                   Idle  S Sendq Recvq Service
heartbeat                   1  R     0     0 
resource                    0  R     0     0 
job-ingest                  0  R     0     0 
kvs-watch                   0  R     0     0 
sched-fluxion-resource      0  R     0     0 
cron                     idle  R     0     0 
barrier                  idle  R     0     0 
job-exec                    0  R     0     0 
job-list                 idle  R     0     0 
kvs                         0  R     0     0 
content-sqlite              0  R     0     0 content-backing
job-info                    0  R     0     0 
job-manager                 0  R     0     0 
sched-fluxion-qmanager      0  R     0     0 sched
content                     0  R     0     0 
connector-local             0  R     0     0 1002-shell-f3Lv2Zd3tj,1002-shell-f3N2WmZB5H
ioapp                      83  R     0     0 
Block until we hear go message from the an io forwarder
```

If you run them together, they work together:

```bash
flux submit -N 1 -n 2 ./compute.lua 120
flux run -N 1 -n 2 ./io-forwarding.lua 120
```
