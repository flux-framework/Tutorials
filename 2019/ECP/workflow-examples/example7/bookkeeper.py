#!/usr/bin/env python

import json
import os
import flux
from flux import jsc
import argparse

def get_environment():
    env = dict()
    for key in os.environ:
        env[key] = os.environ[key]
    return env

# Compute job spec
compute_jobreq = {
    'nnodes' : 3,
    'ntasks' : 6,
    'ncores' : 12,
    'cmdline' : ["./compute.py", "5"],
    'environ' : get_environment (),
    'cwd' : os.getcwd (),
    'walltime' : 0,
    'ngpus' : 0,
    'options': {'nokz': False},
}

# IO forward job spec
io_jobreq = {
    'nnodes' : 3,
    'ntasks' : 3,
    'ncores' : 3,
    'cmdline' : ["./io-forwarding.py", "5"],
    'environ' : get_environment (),
    'cwd' : os.getcwd (),
    'walltime' : 0,
    'ngpus' : 0,
    'options': {'nokz': False},
}

njobs = 0

# Get called everytime a job changes its state
def jsc_cb (jcbstr, arg, errnum):
    global njobs   
    (f, N) = arg 
    jcb = json.loads (jcbstr)
    jobid = jcb['jobid']
    state = jsc.job_num2state (jcb[jsc.JSC_STATE_PAIR][jsc.JSC_STATE_PAIR_NSTATE])
    #print "flux.jsc: job", jobid, "changed its state to ", state
    if state == "complete":
        print "Job {} completed".format(jobid)
        njobs += 1
    if njobs == N:
        f.reactor_stop (f.get_reactor ())

# Submit bundles of jobs using flux submit RPC
def submit_bundles (f, N):
    for i in range (0, N):
         payload = json.dumps (compute_jobreq)
         resp = f.rpc_send ("job.submit", payload)
         if resp is None:
              raise RuntimeError ("flux.rpc: compute_jobreq")

         payload = json.dumps (io_jobreq)
         resp = f.rpc_send ("job.submit", payload)
         if resp is None:
              raise RuntimeError ("flux.rpc: io_jobreq")
    print "bookkeeper: all jobs submited"

# Main
def main ():
    parser = argparse.ArgumentParser (description=
                 'submit and wait for the completion of '
                 'N bundles, each consisting of compute '
                 'and io-forwarding jobs')
    parser.add_argument ('integer', metavar='N', type=int,
                         help='the number of bundles to submit and wait')
    args = parser.parse_args ()

    f = flux.Flux ()
    jsc.notify_status (f, jsc_cb, (f, args.integer * 2)) 
    submit_bundles (f, args.integer)
    print "bookkeeper: waiting until all jobs complete"
    f.reactor_run (f.get_reactor (), 0)
    print "bookkeeper: all jobs completed"
    cmd = "flux wreck ls -n " + str (args.integer * 2)
    os.system (cmd)

main ()

# vi: ts=4 sw=4 expandtab
