#!/bin/bash
set -xe

echo "Install protobuf ..."
wget "https://github.com/protocolbuffers/protobuf/releases/download/v3.14.0/protoc-3.14.0-linux-x86_64.zip"
unzip protoc-3.14.0-linux-x86_64.zip -d $HOME/.local


go get github.com/golang/protobuf/protoc-gen-go@v1.3.2