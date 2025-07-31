### 1. Partitioning Schedule

- Launch a flux instance and schedule/launch compute and io-forwarding jobs on separate nodes
- **# Make sure the scheduler module will do node-exclusive scheduling**
- **FLUX_SCHED_OPTIONS="node-excl=true" flux start -s3**

- **flux submit --nnodes=2 --ntasks=4 --cores-per-task=2 ./compute.lua 120**

- **flux submit --nnodes=1 --ntasks=1 --cores-per-task=2 ./io-forwarding.lua 120**

- **flux wreck ls**

```
    ID NTASKS STATE                    START      RUNTIME    RANKS COMMAND
     2      1 running    2018-05-11T14:58:39       2.891s        2 io-forwarding
     1      4 running    2018-05-11T14:58:33       9.284s    [0-1] compute.lua
```

- **flux kvs get lwj.0.0.1.R_lite**

```json
[ { "node": "quartz32", "children": { "core": "0-3" }, "rank": 0 },
  { "node": "quartz33", "children": { "core": "0-3" }, "rank": 1 } ]
```

- **flux kvs get lwj.0.0.2.R_lite**

```json
[ { "node": "quartz34", "children": { "core": "0-1" }, "rank": 2 } ]
```

### 2. Overlapping Schedule

- Launch a flux instance and schedule/launch both compute and io-forwarding jobs across all nodes
- **FLUX_SCHED_OPTIONS="node-excl=false" flux start -s3**

- **flux submit --nnodes=3 --ntasks=6 --cores-per-task=2 ./compute.lua 120**

- **flux submit --nnodes=3 --ntasks=3 --cores-per-task=1 ./io-forwarding.lua 120**

- **flux wreck ls**

```
    ID NTASKS STATE                    START      RUNTIME    RANKS COMMAND
     2      3 running    2018-05-11T15:09:39       2.654s    [0-2] io-forwarding
     1      6 running    2018-05-11T15:09:23      17.956s    [0-2] compute.lua
```

- **flux kvs get lwj.0.0.1.R_lite**

```json
[ { "node": "quartz32", "children": { "core": "0-3" }, "rank": 0 },
  { "node": "quartz33", "children": { "core": "0-3" }, "rank": 1 },
  { "node": "quartz34", "children": { "core": "0-3" }, "rank": 2 } ]
```

- **flux kvs get lwj.0.0.2.R_lite**

```json
[ { "node": "quartz32", "children": { "core": "4" }, "rank": 0 },
  { "node": "quartz33", "children": { "core": "4" }, "rank": 1 },
  { "node": "quartz34", "children": { "core": "4" }, "rank": 2 } ]
```

