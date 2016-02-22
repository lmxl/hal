#!/bin/sh

# Expects a config with a list of named HDFS paths.  The config should be of the form
# <name of data 1> <path to data 1>
# ...
# <name of data n> <path to data n>
# dodMembers /jobs/contenth/digest_of_digest/master/dod/dodMembers
#
#
# It should be invoked with
# getSchemas.sh <path to config> <path to write avro files to>

WHICH_CLI=$(which hdfs-avro)

if [[ $WHICH_CLI != *"hdfs-avro"* ]]; then
  echo "Installing HDFS CLI, this is a one time operation."
  curl -Lks go/gethdfscli | bash -s
fi

while read -r line || [[ -n $line ]]; do
  #parse command line args
  stringarray=($line)
  filename=${stringarray[0]}
  hdfspath=${stringarray[1]}

  #call hdfs-avro. See http://mmonsch-ld1.linkedin.biz/public/doc/hdfscli for documentation
  hdfs-avro --schema $hdfspath > $2/$filename.tmp

  #rename namespaces and type declarations to avoid compilation collisions. NOTE: this solution is not fool proof.
  #you may need to manually edit the fetched schemas to avoid some edge case collisions
  cat $2/$filename.tmp | sed s/"\"namespace\":.*"/"\"namespace\": \"com.linkedin.data.$filename\","/ > $2/$filename.tmp2
  cat $2/$filename.tmp2 | sed s/"\"type\": \"com\..*\."/"\"type\": \"com.linkedin.data.$filename."/ > $2/$filename.avsc
  rm $2/$filename.tmp*
done < $1
