#! /bin/bash
export PATH=/sbin:/usr/sbin:/usr/local/sbin:/usr/local/bin:/usr/bin:/bin

out_dir=$(pwd)

export WORKDIR=$( cd ` dirname $0 ` && pwd )
cd "$WORKDIR" || exit 1

usage()
{
    echo "$0 [-p] [-o out_dir] project_dir env"
    echo "e.g. $0 facebook-pmd aws_sig"
    echo "e.g. $0 facebook-pmd local_122_cd"
    echo "e.g. $0 -p facebook-pmd local_122_cd"
}

# read conf file
replace()
{
    local business_dir=$1
    local deploy_env=$2
    local dir=$3
    local TMP_CONF=/tmp/${ENV}.${RANDOM}.conf

    rm -rf $dir
    mkdir -p $dir
    cp ${business_dir}/*.json $dir
    cp ${business_dir}/env/* ${dir}

    cp ${business_dir}/env/${deploy_env}.properties ${TMP_CONF}

    cat ${TMP_CONF} | while read line
    do
        key=${line%%=*}
        value=${line#*=}

        if [[ "$key"x != ""x && $key != \#* ]]; then
            value=$(echo $value | sed 's/\\/\\\\/g')
            value=$(echo $value | sed 's/\//\\\//g')
            value=$(echo $value | sed 's/\&/\\\&/g')
            sed -i "s/$key/$value/g" $dir/*
        fi
    done
    sed -i "s%\$PATH%$dir%g" $dir/*
    rm -f ${TMP_CONF}
}

#
# Parse arguments
#
while getopts "po:" option
do
    case ${option} in
        p ) gen_flags="-p";;
        o ) out_dir=${OPTARG};;
        ? ) usage && exit
    esac
done
shift $((OPTIND-1))

if [[ $# != 2 ]]; then
    usage && exit
fi

BUSINESS_DIR=$1
ENV=$2
TAR_DIR=$out_dir/"${ENV}__"


if [ ! -d ${BUSINESS_DIR} ]; then
    echo "ERROR: The specified dir <${BUSINESS_DIR}> does not exist."
    exit 1
fi

if [ ! -e ${BUSINESS_DIR}/env/${ENV}.properties ]; then
    echo "ERROR: The specified env <${ENV}> does not exist."
    exit 1
fi

if [ ! -d $out_dir ]; then
    mkdir $out_dir || exit
fi

replace ${BUSINESS_DIR} ${ENV} ${TAR_DIR}

# replace k8s conf file path in heat.json by contents
if [[ "$ENV"x == "aws_sig"x ]]; then
    FILTER_FLAG="--filter-walle-web" 
    SPLIT_FLAG="--split-walle-java"
else
    FILTER_FLAG=""
    SPLIT_FLAG=""
fi

# replace k8s conf file path in heat.json by contents
python generator.py $gen_flags -i $TAR_DIR/heat.json -o $out_dir/heat_${ENV}.json $FILTER_FLAG $SPLIT_FLAG

# Convert heat.json to v1 format.
# If all json files have been fixed, the following lines are not necessary.
sed -i "s/v1beta3/v1/g" "$out_dir/heat_${ENV}.json"
sed -i "s/publicIPs/deprecatedPublicIPs/g" "$out_dir/heat_${ENV}.json"

# remove temp dir
rm -r $TAR_DIR

