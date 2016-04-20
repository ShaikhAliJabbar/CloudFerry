getCloudCredentials
==========

# Overview
Objective of this feature is  to get the source and destination Cloud  credentials which is required to update configuration.ini


# Usage

## Overview
These are set of scripts which fetch source and destination Cloud credentials.

## Configuration
 Configure password less ssh to source and destination Cloud controller node
 open cloud_conf.py file and update IP of source and destinaiton Cloud Controller IP and update. 
  ```
 Replace ip with the SRC-Contoller IP  of SRC Cloud
 host1 = "root@10.30.0.4"

 Replace ip with the DST-Contoller IP  of DST Cloud
 host2 = "root@10.20.0.3"
 Replace ip with the SRC-Contoller IP  of SRC cloud
 cmd1 = "scp find.sh root@CloudController:/root/"
 cmd1 = "scp find.sh root@10.30.0.4:/root/"
 cmd2 = "scp find.sh root@10.20.0.3:/root/"

  ```
## Execution
 ./get_conf.sh
  it will cteate a txt file where we can get credentials of source and destinaiton clouds



