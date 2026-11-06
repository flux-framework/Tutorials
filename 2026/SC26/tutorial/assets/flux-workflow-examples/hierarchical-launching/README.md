# Hierarchical Launching

## Description: Launch an ensemble of sleep 0 tasks

### Setup

If you haven't already, download the files and change your working directory:

```bash
$ cd flux-workflow-examples/hierarchical-launching
```

### Execution

If you need to start flux on a Slurm cluster:

```bash
salloc -N3 -ppdebug
srun --pty --mpi=none -N3 flux start -o,-S,log-filename=out
```

Start the parent instance

```bash
./parent.sh
```
```console
Mon Nov 18 15:31:08 PST 2019
13363018989568
13365166473216
13367095853056
First Level Done
Mon Nov 18 15:34:13 PST 2019
```

### Notes

- You can increase the number of jobs by increasing `NCORES` in `parent.sh` and
`NJOBS` in `ensemble.sh`.
