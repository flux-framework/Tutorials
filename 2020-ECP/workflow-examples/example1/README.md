### Example 1(a) - Partitioning Schedule

#### Description: Launch a flux instance and schedule/launch compute and io-forwarding jobs on separate nodes

1. `flux start --size=3 -o,-S,log-filename=out`

2. `flux mini submit --nodes=2 --ntasks=4 --cores-per-task=2 ./compute.lua 120`

3. `flux mini submit --nodes=1 --ntasks=1 --cores-per-task=2 ./io-forwarding.lua 120`

4. List running jobs:

`flux job list`

```  
JOBID		       STATE	  USERID   PRI     T_SUBMIT
640671547392	   R	      58985	   16	   2019-10-22T16:27:02Z
1045388328960	   R	      58985	   16	   2019-10-22T16:27:26Z
```

5. Get information about job:

`flux job info 640671547392 R`

```
{"version":1,"execution":{"R_lite":[{"rank":"0-1","children":{"core":"0-3"}}]}}
```

`flux job info 1045388328960 R`

```
{"version":1,"execution":{"R_lite":[{"rank":"2","children":{"core":"0-1"}}]}}
```

### Example 1(b) - Overlapping Schedule

#### Description: Launch a flux instance and schedule/launch both compute and io-forwarding jobs across all nodes

1. `flux start --size=3 -o,-S,log-filename=out`

2. `flux mini submit --nodes=3 --ntasks=6 --cores-per-task=2 ./compute.lua 120`

3. `flux mini submit --nodes=3 --ntasks=3 --cores-per-task=1 ./io-forwarding.lua 120`

4. List jobs in KVS:

`flux job list`

```
JOBID		       STATE	  USERID   PRI     T_SUBMIT
2098158632960	   R	      58985	   16	   2019-10-22T16:35:25Z
2331043168256	   R	      58985	   16	   2019-10-22T16:35:39Z

```

5. Get information about job:

`flux job info 2098158632960 R`

```
{"version":1,"execution":{"R_lite":[{"rank":"2","children":{"core":"2-5"}},{"rank":"0-1","children":{"core":"4-7"}}]}}
```

`flux job info 2331043168256 R`

```
{"version":1,"execution":{"R_lite":[{"rank":"2","children":{"core":"6-7"}},{"rank":"0","children":{"core":"8"}}]}}
```
