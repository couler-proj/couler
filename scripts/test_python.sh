#!/bin/bash
set -e
set -v

pb_file=./couler/proto/couler_pb2.py
cp $pb_file /tmp/old_pb2.py

python setup.py proto

pb_diff=$(diff /tmp/old_pb2.py $pb_file)
if [[ ! -z "$pb_diff" ]]; then
  echo "should commit generated protobuf files:" $pb_file
  echo "found the following diff: $pb_diff"
  exit 1
fi

python setup.py install
python -m pytest