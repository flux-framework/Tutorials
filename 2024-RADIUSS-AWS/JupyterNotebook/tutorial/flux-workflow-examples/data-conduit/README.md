# A Data Conduit Strategy

**Note that this module script does not compile and needs an update**


## Description: Use a data stream to send packets through

### Setup

If you haven't already, download the files and change your working directory:

```bash
$ cd flux-workflow-examples/data-conduit
```

### Execution

If you are using Slurm, allocate three nodes from a resource manager:

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
cp -R ./data-conduit /tmp/data-conduit
cd /tmp/data-conduit
make
```

3. `make`

4. Add the directory of the modules to `FLUX_MODULE_PATH`, if the module was built in the current directory:

`export FLUX_MODULE_PATH=${FLUX_MODULE_PATH}:$(pwd)`

5. Launch a Flux instance on the current allocation by running `flux start` once per node, redirecting log messages to the file `out` in the current directory:

`srun --pty --mpi=none -N3 flux start -o,-S,log-filename=out`

6. Submit the **datastore** script:

`flux submit -N 1 -n 1 ./datastore.py`

7. Submit and resubmit five **compute** scripts to send time data to **datastore**:

`flux submit -N 1 -n 1 ./compute.py 1`

`flux submit -N 1 -n 1 ./compute.py 1`

`flux submit -N 1 -n 1 ./compute.py 1`

`flux submit -N 1 -n 1 ./compute.py 1`

`flux submit -N 1 -n 1 ./compute.py 1`

8. Attach to the **datastore** job to see the data sent by the **compute.py** scripts:

`flux job attach 1900070043648`

```
Starting....
Module was loaded successfully...
finished initialize...
starting run()
Waiting for a packet
{u'test': 101}
Waiting for a packet
{u'test': 101, u'1578431137': u'os.time'}
Waiting for a packet
{u'test': 101, u'1578431137': u'os.time', u'1578431139': u'os.time'}
Waiting for a packet
{u'test': 101, u'1578431140': u'os.time', u'1578431137': u'os.time', u'1578431139': u'os.time'}
Waiting for a packet
{u'test': 101, u'1578431140': u'os.time', u'1578431137': u'os.time', u'1578431139': u'os.time', u'1578431141': u'os.time'}
Bye bye!
run finished...
```

---

### Notes

- `f = flux.Flux()` creates a new Flux handle which can be used to connect to and interact with a Flux instance.

- `kvs.put()` places the value of _udata_ under the key **"conduit"**. Once the key-value pair is put, the change must be committed with `kvs.commit()`. The value can then be retrieved with `kvs.get()`.

- `f.rpc()` creates a new RPC object consisting of a specified topic and payload (along with additional flags) that are exchanged with a Flux service.
