README
======

The Kubernetes plugins for Openstack HEAT (Juno).

There are two new resource types are introduced:

'GoogleInc::Kubernetes::ReplicationController'
'GoogleInc::Kubernetes::Service'

Besides, following individual tools also be used
================================================

generator.py
------------
Description:

Generating the topology file for heat deploying purpose, which will go through properties of each resources to load the given kubernetes definitions (replication controller and service), and then generating the new topology file which will be used for final heat deployment.

Usage:

generator.py <json_file_path>

Output:
A new json file which will be named by using ".replaced" as the post-fix of the given <json_file_path>

Example:
./generator.py heat.json
The file "heat.json.replaced" will be generated
