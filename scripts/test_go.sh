#!/bin/bash
pb_file=./go/couler/proto/couler/v1/couler.pb.go
cp $pb_file /tmp/old.pb.go

go generate ./...

pb_diff=$(diff /tmp/old.pb.go $pb_file)
if [[ ! -z "$pb_diff" ]]; then
  echo "should commit generated protobuf files:" $pb_file
  exit 1
fi

go test ./... -v