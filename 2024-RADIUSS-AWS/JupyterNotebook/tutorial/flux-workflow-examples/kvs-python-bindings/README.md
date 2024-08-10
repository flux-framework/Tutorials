# KVS Python Binding Example

## Description: Use the KVS Python interface to store user data into KVS

If you haven't already, download the files and change your working directory:

```console
$ cd flux-workflow-examples/kvs-python-bindings
```

1. Launch a Flux instance by running `flux start`, redirecting log messages to the file `out` in the current directory:

```bash
flux start -s 1 -o,-S,log-filename=out
```

2. Submit the Python script:

```bash
flux submit -N 1 -n 1 ./kvsput-usrdata.py
```
```console
6705031151616
```

3. Attach to the job and view output:

```bash
flux job attach $(flux job last)
```
```console
hello world
hello world again
```

4. Each job is run within a KVS namespace. `FLUX_KVS_NAMESPACE` is set, which is automatically read and used by the KVS operations in the handle. To take a look at the job's KVS, convert its job ID to KVS:

```bash
flux job id --to=kvs $(flux job last)
```
```console
job.0000.0619.2300.0000
```

5. The keys for this job will be put at the root of the namespace, which is mounted under "guest". To get the value stored under the first key "usrdata":

```bash
flux kvs get job.0000.0619.2300.0000.guest.usrdata
```
```bash
"hello world"
```

6. Get the value stored under the second key "usrdata2":

```bash
flux kvs get job.0000.0619.2300.0000.guest.usrdata2
```
```console
"hello world again"
```

### Notes

- `f = flux.Flux()` creates a new Flux handle which can be used to connect to and interact with a Flux instance.

- `kvs.put()` places the value of _udata_ under the key **"usrdata"**. Once the key-value pair is put, the change must be committed with `kvs.commit()`. The value can then be retrieved with `kvs.get()`

- `kvs.get()` on a directory will return a KVSDir object which supports the `with` compound statement. `with` guarantees a commit is called on the directory.
