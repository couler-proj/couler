// Code generated by protoc-gen-go. DO NOT EDIT.
// source: couler.proto

package couler_v1

import (
	fmt "fmt"
	proto "github.com/golang/protobuf/proto"
	math "math"
)

// Reference imports to suppress errors if they are not otherwise used.
var _ = proto.Marshal
var _ = fmt.Errorf
var _ = math.Inf

// This is a compile-time assertion to ensure that this generated file
// is compatible with the proto package it is being compiled against.
// A compilation error at this line likely means your copy of the
// proto package needs to be updated.
const _ = proto.ProtoPackageIsVersion3 // please upgrade the proto package

type Parameter struct {
	Name                 string   `protobuf:"bytes,1,opt,name=name,proto3" json:"name,omitempty"`
	Value                string   `protobuf:"bytes,2,opt,name=value,proto3" json:"value,omitempty"`
	XXX_NoUnkeyedLiteral struct{} `json:"-"`
	XXX_unrecognized     []byte   `json:"-"`
	XXX_sizecache        int32    `json:"-"`
}

func (m *Parameter) Reset()         { *m = Parameter{} }
func (m *Parameter) String() string { return proto.CompactTextString(m) }
func (*Parameter) ProtoMessage()    {}
func (*Parameter) Descriptor() ([]byte, []int) {
	return fileDescriptor_dc28e41c19c684e1, []int{0}
}

func (m *Parameter) XXX_Unmarshal(b []byte) error {
	return xxx_messageInfo_Parameter.Unmarshal(m, b)
}
func (m *Parameter) XXX_Marshal(b []byte, deterministic bool) ([]byte, error) {
	return xxx_messageInfo_Parameter.Marshal(b, m, deterministic)
}
func (m *Parameter) XXX_Merge(src proto.Message) {
	xxx_messageInfo_Parameter.Merge(m, src)
}
func (m *Parameter) XXX_Size() int {
	return xxx_messageInfo_Parameter.Size(m)
}
func (m *Parameter) XXX_DiscardUnknown() {
	xxx_messageInfo_Parameter.DiscardUnknown(m)
}

var xxx_messageInfo_Parameter proto.InternalMessageInfo

func (m *Parameter) GetName() string {
	if m != nil {
		return m.Name
	}
	return ""
}

func (m *Parameter) GetValue() string {
	if m != nil {
		return m.Value
	}
	return ""
}

type Artifact struct {
	Name                 string   `protobuf:"bytes,1,opt,name=name,proto3" json:"name,omitempty"`
	Type                 string   `protobuf:"bytes,2,opt,name=type,proto3" json:"type,omitempty"`
	Value                string   `protobuf:"bytes,3,opt,name=value,proto3" json:"value,omitempty"`
	XXX_NoUnkeyedLiteral struct{} `json:"-"`
	XXX_unrecognized     []byte   `json:"-"`
	XXX_sizecache        int32    `json:"-"`
}

func (m *Artifact) Reset()         { *m = Artifact{} }
func (m *Artifact) String() string { return proto.CompactTextString(m) }
func (*Artifact) ProtoMessage()    {}
func (*Artifact) Descriptor() ([]byte, []int) {
	return fileDescriptor_dc28e41c19c684e1, []int{1}
}

func (m *Artifact) XXX_Unmarshal(b []byte) error {
	return xxx_messageInfo_Artifact.Unmarshal(m, b)
}
func (m *Artifact) XXX_Marshal(b []byte, deterministic bool) ([]byte, error) {
	return xxx_messageInfo_Artifact.Marshal(b, m, deterministic)
}
func (m *Artifact) XXX_Merge(src proto.Message) {
	xxx_messageInfo_Artifact.Merge(m, src)
}
func (m *Artifact) XXX_Size() int {
	return xxx_messageInfo_Artifact.Size(m)
}
func (m *Artifact) XXX_DiscardUnknown() {
	xxx_messageInfo_Artifact.DiscardUnknown(m)
}

var xxx_messageInfo_Artifact proto.InternalMessageInfo

func (m *Artifact) GetName() string {
	if m != nil {
		return m.Name
	}
	return ""
}

func (m *Artifact) GetType() string {
	if m != nil {
		return m.Type
	}
	return ""
}

func (m *Artifact) GetValue() string {
	if m != nil {
		return m.Value
	}
	return ""
}

type StepIO struct {
	Name   string `protobuf:"bytes,1,opt,name=name,proto3" json:"name,omitempty"`
	Source int32  `protobuf:"varint,2,opt,name=source,proto3" json:"source,omitempty"`
	// Types that are valid to be assigned to StepIo:
	//	*StepIO_Parameter
	//	*StepIO_Artifact
	StepIo               isStepIO_StepIo `protobuf_oneof:"step_io"`
	XXX_NoUnkeyedLiteral struct{}        `json:"-"`
	XXX_unrecognized     []byte          `json:"-"`
	XXX_sizecache        int32           `json:"-"`
}

func (m *StepIO) Reset()         { *m = StepIO{} }
func (m *StepIO) String() string { return proto.CompactTextString(m) }
func (*StepIO) ProtoMessage()    {}
func (*StepIO) Descriptor() ([]byte, []int) {
	return fileDescriptor_dc28e41c19c684e1, []int{2}
}

func (m *StepIO) XXX_Unmarshal(b []byte) error {
	return xxx_messageInfo_StepIO.Unmarshal(m, b)
}
func (m *StepIO) XXX_Marshal(b []byte, deterministic bool) ([]byte, error) {
	return xxx_messageInfo_StepIO.Marshal(b, m, deterministic)
}
func (m *StepIO) XXX_Merge(src proto.Message) {
	xxx_messageInfo_StepIO.Merge(m, src)
}
func (m *StepIO) XXX_Size() int {
	return xxx_messageInfo_StepIO.Size(m)
}
func (m *StepIO) XXX_DiscardUnknown() {
	xxx_messageInfo_StepIO.DiscardUnknown(m)
}

var xxx_messageInfo_StepIO proto.InternalMessageInfo

func (m *StepIO) GetName() string {
	if m != nil {
		return m.Name
	}
	return ""
}

func (m *StepIO) GetSource() int32 {
	if m != nil {
		return m.Source
	}
	return 0
}

type isStepIO_StepIo interface {
	isStepIO_StepIo()
}

type StepIO_Parameter struct {
	Parameter *Parameter `protobuf:"bytes,3,opt,name=parameter,proto3,oneof"`
}

type StepIO_Artifact struct {
	Artifact *Artifact `protobuf:"bytes,4,opt,name=artifact,proto3,oneof"`
}

func (*StepIO_Parameter) isStepIO_StepIo() {}

func (*StepIO_Artifact) isStepIO_StepIo() {}

func (m *StepIO) GetStepIo() isStepIO_StepIo {
	if m != nil {
		return m.StepIo
	}
	return nil
}

func (m *StepIO) GetParameter() *Parameter {
	if x, ok := m.GetStepIo().(*StepIO_Parameter); ok {
		return x.Parameter
	}
	return nil
}

func (m *StepIO) GetArtifact() *Artifact {
	if x, ok := m.GetStepIo().(*StepIO_Artifact); ok {
		return x.Artifact
	}
	return nil
}

// XXX_OneofWrappers is for the internal use of the proto package.
func (*StepIO) XXX_OneofWrappers() []interface{} {
	return []interface{}{
		(*StepIO_Parameter)(nil),
		(*StepIO_Artifact)(nil),
	}
}

type Step struct {
	Id                   int32     `protobuf:"varint,1,opt,name=id,proto3" json:"id,omitempty"`
	Name                 string    `protobuf:"bytes,2,opt,name=name,proto3" json:"name,omitempty"`
	Image                string    `protobuf:"bytes,3,opt,name=image,proto3" json:"image,omitempty"`
	Command              []string  `protobuf:"bytes,4,rep,name=command,proto3" json:"command,omitempty"`
	Inputs               []*StepIO `protobuf:"bytes,5,rep,name=inputs,proto3" json:"inputs,omitempty"`
	Outputs              []*StepIO `protobuf:"bytes,6,rep,name=outputs,proto3" json:"outputs,omitempty"`
	Dependencies         []int32   `protobuf:"varint,7,rep,packed,name=dependencies,proto3" json:"dependencies,omitempty"`
	XXX_NoUnkeyedLiteral struct{}  `json:"-"`
	XXX_unrecognized     []byte    `json:"-"`
	XXX_sizecache        int32     `json:"-"`
}

func (m *Step) Reset()         { *m = Step{} }
func (m *Step) String() string { return proto.CompactTextString(m) }
func (*Step) ProtoMessage()    {}
func (*Step) Descriptor() ([]byte, []int) {
	return fileDescriptor_dc28e41c19c684e1, []int{3}
}

func (m *Step) XXX_Unmarshal(b []byte) error {
	return xxx_messageInfo_Step.Unmarshal(m, b)
}
func (m *Step) XXX_Marshal(b []byte, deterministic bool) ([]byte, error) {
	return xxx_messageInfo_Step.Marshal(b, m, deterministic)
}
func (m *Step) XXX_Merge(src proto.Message) {
	xxx_messageInfo_Step.Merge(m, src)
}
func (m *Step) XXX_Size() int {
	return xxx_messageInfo_Step.Size(m)
}
func (m *Step) XXX_DiscardUnknown() {
	xxx_messageInfo_Step.DiscardUnknown(m)
}

var xxx_messageInfo_Step proto.InternalMessageInfo

func (m *Step) GetId() int32 {
	if m != nil {
		return m.Id
	}
	return 0
}

func (m *Step) GetName() string {
	if m != nil {
		return m.Name
	}
	return ""
}

func (m *Step) GetImage() string {
	if m != nil {
		return m.Image
	}
	return ""
}

func (m *Step) GetCommand() []string {
	if m != nil {
		return m.Command
	}
	return nil
}

func (m *Step) GetInputs() []*StepIO {
	if m != nil {
		return m.Inputs
	}
	return nil
}

func (m *Step) GetOutputs() []*StepIO {
	if m != nil {
		return m.Outputs
	}
	return nil
}

func (m *Step) GetDependencies() []int32 {
	if m != nil {
		return m.Dependencies
	}
	return nil
}

type Workflow struct {
	Steps                []*Step  `protobuf:"bytes,1,rep,name=steps,proto3" json:"steps,omitempty"`
	Parallelism          int32    `protobuf:"varint,2,opt,name=parallelism,proto3" json:"parallelism,omitempty"`
	Secret               string   `protobuf:"bytes,3,opt,name=secret,proto3" json:"secret,omitempty"`
	XXX_NoUnkeyedLiteral struct{} `json:"-"`
	XXX_unrecognized     []byte   `json:"-"`
	XXX_sizecache        int32    `json:"-"`
}

func (m *Workflow) Reset()         { *m = Workflow{} }
func (m *Workflow) String() string { return proto.CompactTextString(m) }
func (*Workflow) ProtoMessage()    {}
func (*Workflow) Descriptor() ([]byte, []int) {
	return fileDescriptor_dc28e41c19c684e1, []int{4}
}

func (m *Workflow) XXX_Unmarshal(b []byte) error {
	return xxx_messageInfo_Workflow.Unmarshal(m, b)
}
func (m *Workflow) XXX_Marshal(b []byte, deterministic bool) ([]byte, error) {
	return xxx_messageInfo_Workflow.Marshal(b, m, deterministic)
}
func (m *Workflow) XXX_Merge(src proto.Message) {
	xxx_messageInfo_Workflow.Merge(m, src)
}
func (m *Workflow) XXX_Size() int {
	return xxx_messageInfo_Workflow.Size(m)
}
func (m *Workflow) XXX_DiscardUnknown() {
	xxx_messageInfo_Workflow.DiscardUnknown(m)
}

var xxx_messageInfo_Workflow proto.InternalMessageInfo

func (m *Workflow) GetSteps() []*Step {
	if m != nil {
		return m.Steps
	}
	return nil
}

func (m *Workflow) GetParallelism() int32 {
	if m != nil {
		return m.Parallelism
	}
	return 0
}

func (m *Workflow) GetSecret() string {
	if m != nil {
		return m.Secret
	}
	return ""
}

func init() {
	proto.RegisterType((*Parameter)(nil), "couler.v1.Parameter")
	proto.RegisterType((*Artifact)(nil), "couler.v1.Artifact")
	proto.RegisterType((*StepIO)(nil), "couler.v1.StepIO")
	proto.RegisterType((*Step)(nil), "couler.v1.Step")
	proto.RegisterType((*Workflow)(nil), "couler.v1.Workflow")
}

func init() { proto.RegisterFile("couler.proto", fileDescriptor_dc28e41c19c684e1) }

var fileDescriptor_dc28e41c19c684e1 = []byte{
	// 354 bytes of a gzipped FileDescriptorProto
	0x1f, 0x8b, 0x08, 0x00, 0x00, 0x00, 0x00, 0x00, 0x02, 0xff, 0x74, 0x52, 0xdd, 0x4a, 0xc3, 0x30,
	0x18, 0x5d, 0xff, 0xd7, 0x6f, 0x43, 0x31, 0x0e, 0xc9, 0x65, 0x29, 0x08, 0x15, 0x61, 0xb0, 0xa9,
	0x0f, 0xa0, 0x57, 0xf3, 0x4a, 0x89, 0x17, 0x5e, 0x4a, 0x6c, 0x33, 0x09, 0x6b, 0x9b, 0x92, 0xa6,
	0x13, 0xdf, 0xc8, 0x27, 0xf2, 0x79, 0x64, 0x69, 0xda, 0x75, 0x32, 0xef, 0x72, 0xbe, 0x9e, 0xef,
	0x70, 0xce, 0xf9, 0x0a, 0xd3, 0x54, 0x34, 0x39, 0x93, 0xf3, 0x4a, 0x0a, 0x25, 0x50, 0x68, 0xd0,
	0x76, 0x11, 0xdf, 0x41, 0xf8, 0x4c, 0x25, 0x2d, 0x98, 0x62, 0x12, 0x21, 0x70, 0x4b, 0x5a, 0x30,
	0x6c, 0x45, 0x56, 0x12, 0x12, 0xfd, 0x46, 0x33, 0xf0, 0xb6, 0x34, 0x6f, 0x18, 0xb6, 0xf5, 0xb0,
	0x05, 0xf1, 0x0a, 0xc6, 0xf7, 0x52, 0xf1, 0x35, 0x4d, 0xd5, 0xd1, 0x2d, 0x04, 0xae, 0xfa, 0xaa,
	0xba, 0x25, 0xfd, 0xde, 0x2b, 0x39, 0x43, 0xa5, 0x6f, 0x0b, 0xfc, 0x17, 0xc5, 0xaa, 0xc7, 0xa7,
	0xa3, 0x42, 0x17, 0xe0, 0xd7, 0xa2, 0x91, 0x69, 0x2b, 0xe5, 0x11, 0x83, 0xd0, 0x2d, 0x84, 0x55,
	0xe7, 0x5b, 0x0b, 0x4e, 0x96, 0xb3, 0x79, 0x1f, 0x6b, 0xde, 0x67, 0x5a, 0x8d, 0xc8, 0x9e, 0x88,
	0x16, 0x30, 0xa6, 0xc6, 0x36, 0x76, 0xf5, 0xd2, 0xf9, 0x60, 0xa9, 0x4b, 0xb4, 0x1a, 0x91, 0x9e,
	0xf6, 0x10, 0x42, 0x50, 0x2b, 0x56, 0xbd, 0x71, 0x11, 0xff, 0x58, 0xe0, 0xee, 0xac, 0xa2, 0x13,
	0xb0, 0x79, 0xa6, 0x6d, 0x7a, 0xc4, 0xe6, 0x59, 0x6f, 0xdc, 0x3e, 0xec, 0x8d, 0x17, 0xf4, 0xa3,
	0x4f, 0xab, 0x01, 0xc2, 0x10, 0xa4, 0xa2, 0x28, 0x68, 0x99, 0x61, 0x37, 0x72, 0x92, 0x90, 0x74,
	0x10, 0x5d, 0x81, 0xcf, 0xcb, 0xaa, 0x51, 0x35, 0xf6, 0x22, 0x27, 0x99, 0x2c, 0xcf, 0x06, 0xc6,
	0xda, 0x7e, 0x88, 0x21, 0xa0, 0x6b, 0x08, 0x44, 0xa3, 0x34, 0xd7, 0xff, 0x8f, 0xdb, 0x31, 0x50,
	0x0c, 0xd3, 0x8c, 0x55, 0xac, 0xcc, 0x58, 0x99, 0x72, 0x56, 0xe3, 0x20, 0x72, 0x12, 0x8f, 0x1c,
	0xcc, 0xe2, 0x0d, 0x8c, 0x5f, 0x85, 0xdc, 0xac, 0x73, 0xf1, 0x89, 0x2e, 0xc1, 0xdb, 0xe5, 0xad,
	0xb1, 0xa5, 0xa5, 0x4f, 0xff, 0x48, 0x93, 0xf6, 0x2b, 0x8a, 0x60, 0xb2, 0xab, 0x35, 0xcf, 0x59,
	0xce, 0xeb, 0xc2, 0x1c, 0x67, 0x38, 0xd2, 0x97, 0x63, 0xa9, 0x64, 0xca, 0x34, 0x60, 0xd0, 0xbb,
	0xaf, 0xff, 0xc1, 0x9b, 0xdf, 0x00, 0x00, 0x00, 0xff, 0xff, 0xbd, 0xb0, 0x41, 0xdc, 0x93, 0x02,
	0x00, 0x00,
}