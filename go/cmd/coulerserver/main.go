package main

import (
	"flag"
	"fmt"
	"log"
	"net"

	pb "ant-aii/couler/go/couler/proto/couler_v1"
	"ant-aii/couler/go/couler/server"

	"google.golang.org/grpc"
)

var (
	port = flag.Int("port", 50051, "The server port")
)

func main() {
	flag.Parse()
	lis, e := net.Listen("tcp", fmt.Sprintf(":%d", *port))
	if e != nil {
		log.Fatalf("failed to listen on %d", port)
	}

	grpcServer := grpc.NewServer()
	pb.RegisterWorkflowServiceServer(grpcServer, server.New())
	log.Printf("Couler server started at: %d", *port)
	grpcServer.Serve(lis)
}
