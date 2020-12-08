package server

import (
	pb "ant-aii/couler/go/couler/proto/couler_v1"
	"context"
	"fmt"
)

// CoulerService provides operators for a workflow,
// e.g. submit, pause, stop and delete.
type CoulerService struct {
}

// Submit a workflow
func (s *CoulerService) Submit(ctx context.Context, r *pb.Request) (*pb.Response, error) {
	return nil, fmt.Errorf("should implement Submit interface")
}

// Pause a workflow
func (s *CoulerService) Pause(ctx context.Context, r *pb.Request) (*pb.Response, error) {
	return nil, fmt.Errorf("should implement Pause interface")
}

// Resume a workflow
func (s *CoulerService) Resume(ctx context.Context, r *pb.Request) (*pb.Response, error) {
	return nil, fmt.Errorf("should implement Resume interface")
}

// Stop a workflow
func (s *CoulerService) Stop(ctx context.Context, r *pb.Request) (*pb.Response, error) {
	return nil, fmt.Errorf("should implement Stop interface")
}

// Delete a workflow
func (s *CoulerService) Delete(ctx context.Context, r *pb.Request) (*pb.Response, error) {
	return nil, fmt.Errorf("should implement Delete interface")
}

// New returns a CoulerService instance
func New() *CoulerService {
	return &CoulerService{}
}
