#!/bin/bash

usage()
{
    echo "$0 project_dir version"
    echo "e.g. $0 facebook-pmd 1.0.1"
    echo "e.g. $0 facebook-pmd 1.0.2"
}

if [ $# != 2 ]; then
    usage
    exit 1
fi

version=$2

property_files=$(cd $1/env; ls)
property_files=${property_files//.properties/}
for property in $property_files
do
    echo "test $property"
    ./gen_conf.sh facebook-pmd $property $version
    ./gen_conf.sh -p facebook-pmd $property $version
    rm heat_${property}_$version.json
done

echo "DONE"

