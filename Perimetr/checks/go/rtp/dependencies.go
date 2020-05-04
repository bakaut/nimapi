package rtp

import (
	"context"
)

type (
	StorageRTP interface {
		CreateRtpPacket(ctx context.Context, rtPacket storage.RtpPacket) error
	}
)
