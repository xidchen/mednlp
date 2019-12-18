#!/bin/bash
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

core=

if [ $# -lt 3 ]
then
    echo "missing argument"
    echo "post.sh host:ip core file"
    exit 1
else
	solr_host_port="$1"
    core="$2"
fi

url=http://$solr_host_port/solr/$core/update

shift 2

if [ "$1" = "" ]
then
    echo "missing xml file"
    exit 2
fi

FILES=$*

for f in $FILES; do
  echo Posting file $f to $url
  curl $url --data-binary @$f -H 'Content-type:application/xml; charset=utf-8'
  echo
done

#send the commit command to make sure all the changes are flushed and visible
curl $url --data-binary '<commit/>' -H 'Content-type:application/xml'
echo
