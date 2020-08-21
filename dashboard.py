#!/usr/bin/env python
""" Print the grafana dashboard URL for a job on stdout.

    Usage:

        dashboard.py BASE_URL SLURM_JOB_ID
        dashboard.py BASE_URL START END [START] [END] [SLURM_NODELIST]
    
    where:
        BASE_URL: fixed part of dashboard URL (before `?`) to generate, e.g.:
                v5: http://128.232.224.87:3000/d/hS1VtkHGk/openhpc-2
                earlier: http://10.60.253.1:3000/dashboard/db/openhpc-compute
        SLURM_JOB_ID: get URL for a dashboard showing this job ID (an integer)
        START, END: define timerange of dashboard using any time/date format accepted by `time`
        SLURM_NODELIST: only show specific nodes, in slurm "hostlist" expression, e.g. "openhpc-compute-[12-13]"
            domain: str, domain name to add to hosts, or None if this is not required
            pre, post: int, number of seconds to pad timespan by

    To use this *within* a job, e.g. to generate an URL inside an sbatch script, the 2nd form must be used (as `sacct` will not have job endtime), e.g.:
    
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

def job_info(job_id):
    """ Get info about a completed Slurm job.

        Args:
            job_id: str, Slurm job ID
        
        Returns a sequence:
            NodeList, Start, End
    """
    COLUMNS = ('NodeList', 'Start' ,'End')
    cmd = ('sacct', '-j', job_id, '--parsable', '--noheader', '--format', ','.join(COLUMNS))
    info = subprocess.check_output(cmd, universal_newlines=True).strip('\n').split('\n')[0] # subsequent lines are job steps
    info = info.split('|')[:-1] # slice removes empty element from trailing |
    return info

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
    if len(sys.argv) < 3:
        exit('Wrong number of arguments. Usage\n%s' % __doc__)
    elif len(sys.argv) == 3:
        baseurl = sys.argv[1]
        nodelist, start, end = job_info(sys.argv[2])
        url = get_dashboard_url(baseurl, start, end, nodelist)
    else:
        url = get_dashboard_url(*sys.argv[1:])
    print(url)
    
    # tests (budget!)
    #assert get_dashboard_url("Wed Oct 30 11:55:13 GMT 2019" "Wed Oct 30 12:03:02 GMT 2019") == "http://10.60.253.1:3000/dashboard/db/openhpc-compute?refresh=30s&orgId=4&from=1572436483000&to=1572437012000"
