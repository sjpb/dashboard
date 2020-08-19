#!/usr/bin/env python
""" Print the grafana dashboard URL for a job on stdout.

    Can be used from the command-line, e.g. in an sbatch script which contains something like:
    
    job.sh:
        startstamp="$(date)"
        <run my commands here>
        endstamp="$(date)"
        BASEURL=<base dashboard url>
        echo "dashboard url for this job:" $(python dashboard.py $BASEURL $startstamp $endstamp $SLURM_JOB_NODELIST)
            
    Works on python 2.7 and 3.7.4 at least.
"""
from __future__ import print_function
import time, os, sys, subprocess

def datestr_to_ns(s):
    """ Convert date string from `date` to ns since epoch.
    
        Requires `date` taking `+%s` to be available.
        
        Returns an int.
    """
    
    seconds_since_epoch = int(subprocess.check_output(('date', '+%s', '-d', s), universal_newlines=True).strip())
    return seconds_since_epoch * 1000

def expand_hosts(hostlist):
    """ Expand a slurm hostlist like "openhpc-compute-[12-13]" into a list of strs.
    
        Requires `scontrol` to be available.
    """
    hostnames = subprocess.check_output(('scontrol', 'show', 'hostnames', hostlist), universal_newlines=True).strip('\n').split('\n')
    return hostnames

def get_dashboard_url(baseurl, start=None, end=None, hostlist=None, domain=None, pre=30, post=30):
    """ Get the grafana dashboard url for a given time range.
    
        Args:
            baseurl: str, fixed part of dashboard URL (before `?`), e.g. 
                v5: http://128.232.224.87:3000/d/hS1VtkHGk/openhpc-2
                earlier: http://10.60.253.1:3000/dashboard/db/openhpc-compute
            start, end: strs from `date` - tries to be broad in format it accepts, or None for default
            hostlist: str, slurm "hostlist" expression, e.g. "openhpc-compute-[12-13]", or None for all
            domain: str, domain name to add to hosts, or None if this is not required
            pre, post: int, number of seconds to pad timespan by
        
        Returns a str.
    """
    
    url = []
    if start:
        start_ns = datestr_to_ns(start) - pre *1000
        url.append('from=%s' % start_ns)
    if end:
        end_ns = datestr_to_ns(end) + post * 1000
        url.append('to=%s' % end_ns)
    if hostlist:
        hostnames = expand_hosts(hostlist)
        for host in hostnames:
            hostparam = 'var-hostname=%s' % host
            if domain:
                hostparam += '.' + domain
            url.append(hostparam)

    return baseurl + '?' + '&'.join(url)
    
if __name__ == '__main__':
    print(get_dashboard_url(*sys.argv[1:]))
    
    # tests (budget!)
    #assert get_dashboard_url("Wed Oct 30 11:55:13 GMT 2019" "Wed Oct 30 12:03:02 GMT 2019") == "http://10.60.253.1:3000/dashboard/db/openhpc-compute?refresh=30s&orgId=4&from=1572436483000&to=1572437012000"
