# Created by jabar.ali
#jali@mirantis.com
# Object of this script to fetch the cloud credential for confiuring configuration.ini 


import re
from fabric.api import run
from fabric.tasks import execute

import os

# Replace ip with the SRC-Contoller IP  of SRC Cloud
host1 = "root@10.30.0.4"

# Replace ip with the DST-Contoller IP  of DST Cloud
host2 = "root@10.20.0.3"

# Relace ip with the SRC-Contoller IP  of SRC cloud
# cmd1 = "scp find.sh root@CloudController:/root/" 

cmd1 = "scp find.sh root@10.30.0.4:/root/" 
cmd2 = "scp find.sh root@10.20.0.3:/root/" 

def taskA():
    #run('ls -lrt find.sh')
    run('chmod 777 find.sh ')
    #run('. openrc')
    run('./find.sh')
    run('rm find.sh  ')
    #run('ls -lrt  ')

def do_something():
    taskA()

if __name__ == "__main__":
    os.system(cmd1) 
    os.system(cmd2) 
    execute(do_something, hosts=[host1,host2])
