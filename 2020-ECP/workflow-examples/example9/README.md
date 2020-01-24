### Example 9 - A Data Conduit Strategy

#### Description: Use a data stream to send packets through

1. Point to `flux-core`'s `pkgconfig` directory:

| Shell     | Command                                                      |
| -----     | ----------                                                   |
| tcsh      | `setenv PKG_CONFIG_PATH /usr/local/lib/pkgconfig`   |
| bash/zsh  | `export PKG_CONFIG_PATH='/usr/local/lib/pkgconfig'` |

2. `make`

3. Add the directory of the modules to `FLUX_MODULE_PATH`; if the module was built in the current dir:

`export FLUX_MODULE_PATH=${FLUX_MODULE_PATH}:$(pwd)`

4. Launch a Flux instance emulating a 3 node cluster, redirecting log messages to the file `out` in the current directory:

`flux start --size=3 -o,-S,log-filename=out`

5. Submit the **datastore** script:

`flux submit -N 1 -n 1 ./datastore.py`

6. Submit and resubmit five **compute** scripts to send time data to **datastore**:

`flux submit -N 1 -n 1 ./compute.py 1`

`flux submit -N 1 -n 1 ./compute.py 1`

`flux submit -N 1 -n 1 ./compute.py 1`

`flux submit -N 1 -n 1 ./compute.py 1`

`flux submit -N 1 -n 1 ./compute.py 1`

7. Attach to the **datastore** job to see the data sent by the **compute.py** scripts:

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

##### Notes

- `f = flux.Flux()` creates a new Flux handle which can be used to connect to and interact with a Flux instance.

- `kvs.put()` places the value of _udata_ under the key **"conduit"**. Once the key-value pair is put, the change must be committed with `kvs.commit()`. The value can then be retrieved with `kvs.get()`.

- `f.rpc()` creates a new RPC object consisting of a specified topic and payload (along with additional flags) that are exchanged with a Flux service.
