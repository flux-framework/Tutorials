### Example 1(a) - Partitioning Schedule

#### Description: Launch a flux instance and schedule/launch compute and io-forwarding jobs on separate nodes

1. `flux start --size=3 -o,-S,log-filename=out`

2. `flux mini submit --nodes=2 --ntasks=4 --cores-per-task=2 ./compute.lua 120`

3. `flux mini submit --nodes=1 --ntasks=1 --cores-per-task=2 ./io-forwarding.lua 120`

4. List running jobs:

`flux jobs`

```
             JOBID USER     NAME       STATE    NTASKS RUNTIME
      825757794304 ubuntu   io-forward RUN           1 5.535s
      735798362112 ubuntu   compute.lu RUN           4 11s
```

5. Information about jobs, such as the submitted job specification, an eventlog, and the resource description format **R** are stored in the KVS. The data can be queried via the `job-info` module via the `flux job info` command. For example, to fetch **R** for a job which has been allocated resources:

`flux job info 735798362112 R`

```
{"version":1,"execution":{"R_lite":[{"rank":"0-1","children":{"core":"0-3"}}]}}
```

`flux job info 825757794304 R`

```
{"version":1,"execution":{"R_lite":[{"rank":"2","children":{"core":"0-1"}}]}}
```

### Example 1(b) - Overlapping Schedule

#### Description: Launch a flux instance and schedule/launch both compute and io-forwarding jobs across all nodes

1. `flux start --size=3 -o,-S,log-filename=out`

2. `flux mini submit --nodes=3 --ntasks=6 --cores-per-task=2 ./compute.lua 120`

3. `flux mini submit --nodes=3 --ntasks=3 --cores-per-task=1 ./io-forwarding.lua 120`

4. List jobs in KVS:

`flux jobs`

```
             JOBID USER     NAME       STATE    NTASKS RUNTIME
      282779975680 ubuntu   io-forward RUN           3 12s
       98348040192 ubuntu   compute.lu RUN           6 23s
```

5. Get information about job:

`flux job info 98348040192 R`

```
{"version":1,"execution":{"R_lite":[{"rank":"2","children":{"core":"2-5"}},{"rank":"0-1","children":{"core":"4-7"}}]}}
```

`flux job info 282779975680 R`

```
{"version":1,"execution":{"R_lite":[{"rank":"2","children":{"core":"6-7"}},{"rank":"0","children":{"core":"8"}}]}}
```
