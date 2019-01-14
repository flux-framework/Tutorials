### A data conduit strategy

- **make**

- **# Make sure the scheduler module will do node-exclusive scheduling**
- **FLUX_SCHED_OPTIONS="node-excl=true" flux start -s3**

- **flux submit -N 1 -n 1 ./datastore.py**

- **flux submit -N 1 -n 1 ./compute.lua 1**
- **flux submit -N 1 -n 1 ./compute.lua 1**
- **flux submit -N 1 -n 1 ./compute.lua 1**
- **flux submit -N 1 -n 1 ./compute.lua 1**

- **flux wreck attach 1**
```
Starting....
Waiting for a packet
{u'test': 101}
Waiting for a packet
{u'test': 101, u'1527743330': u'os.time'}
Waiting for a packet
{u'test': 101, u'1527743331': u'os.time', u'1527743330': u'os.time'}
Waiting for a packet
{u'test': 101, u'1527743331': u'os.time', u'1527743330': u'os.time'}
Waiting for a packet
{u'test': 101, u'1527743332': u'os.time', u'1527743331': u'os.time', u'1527743330': u'os.time'}
Waiting for a packet
{u'test': 101, u'1527743333': u'os.time', u'1527743332': u'os.time', u'1527743331': u'os.time', u'1527743330': u'os.time'}
Waiting for a packet
Bye bye!
```
