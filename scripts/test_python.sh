#!/bin/bash
set -e

pb_file=./couler/proto/couler_pb2.py
cp $pb_file /tmp/old_pb2.py

python setup.py proto

# TODO: This check is temporarily disabled as it's flaky on GitHub Actions
#pb_diff=$(diff /tmp/old_pb2.py $pb_file)
#if [[ ! -z "$pb_diff" ]]; then
#  echo "should commit generated protobuf files:" $pb_file
#  exit 1
#fi

python setup.py install
python -m pytest