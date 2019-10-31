""" Print the grafana dashboard URL for a job on stdout.

    Use in an sbatch script which contains something like:
    
    job.sh:
        startstamp="$(date)"
        $CMD
        endstamp="$(date)"
        echo "dashboard url for this job:" $(python dashboard.py "$startstamp" "$endstamp")
       
    Works on python 2.7 and 3.7.4 at least.
"""

import time, os, sys, subprocess

def datestr_to_ns(s):
    """ Convert date string from `date` to ns since epoch.
    
        Requires `date` taking `+%s` to be available.
        
        Returns an int.
    """
    
    seconds_since_epoch = int(subprocess.check_output(('date', '+%s', '-d', s), universal_newlines=True).strip())
    return seconds_since_epoch * 1000
    

def get_dashboard_url(start, end, pre=30, post=30):
    """ Get the grafana dashboard url for a given time range.
    
        start, end: strs from `date` - tries to be broad in format it accepts
        pre, post: number of seconds to pad timespan by
        
        Returns a str.
    """
    start_ns = datestr_to_ns(start) - pre *1000
    end_ns = datestr_to_ns(end) + post * 1000
    
    url = 'http://10.60.253.1:3000/dashboard/db/openhpc-compute?refresh=30s&orgId=4&from={start}&to={end}'.format(start=start_ns, end=end_ns)
    return url
   
if __name__ == '__main__':
    print(get_dashboard_url(*sys.argv[1:]))
    
    # tests (budget!)
    #assert get_dashboard_url("Wed Oct 30 11:55:13 GMT 2019" "Wed Oct 30 12:03:02 GMT 2019") == "http://10.60.253.1:3000/dashboard/db/openhpc-compute?refresh=30s&orgId=4&from=1572436483000&to=1572437012000"