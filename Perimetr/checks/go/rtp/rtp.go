package rtp

type RTP struct {
	Storage StorageRTP
}

type rtpPacket struct {
	DstPort        uint16
	SrcPort        uint16
	DstIp          string
	SrcIp          string
	SequenceNumber uint16
	Timestamp      uint32
	Marker         bool
	SSRC           uint32
}

func (r *RTP) Start(device string) error {
	if handle, err := pcap.OpenLive(device, 1600, true, pcap.BlockForever); err != nil {
		return err
	} else {
		packetSource := gopacket.NewPacketSource(handle, handle.LinkType())
		for packet := range packetSource.Packets() {
			tcp := packet.Layer(layers.LayerTypeTCP)
			udp := packet.Layer(layers.LayerTypeUDP)
			ipv4l := packet.Layer(layers.LayerTypeIPv4)
			ipv6l := packet.Layer(layers.LayerTypeIPv6)
			var ipv4 *layers.IPv4
			var ipv6 *layers.IPv6
			if ipv4l != nil {
				ipv4 = ipv4l.(*layers.IPv4)
			}

			if ipv6l != nil {
				ipv6 = ipv6l.(*layers.IPv6)
			}

			if tcp != nil {
				err := r.handleLayer(tcp, ipv4, ipv6)
				if err != nil {
					return err
				}
			} else if udp != nil {
				err := r.handleLayer(udp, ipv4, ipv6)
				if err != nil {
					return err
				}
			}
		}
	}
	return nil
}

func (r *RTP) handleLayer(layer gopacket.Layer, ipv4 *layers.IPv4, ipv6 *layers.IPv6) error {
	p := &rtp.Packet{}

	if err := p.Unmarshal([]byte{}); err == nil {
		fmt.Println(err)
	}

	if err := p.Unmarshal(layer.LayerPayload()); err != nil {
		fmt.Println(err)
	}

	if p.Version == 2 && p.PayloadType >= 96 && p.PayloadType <= 100 {
		rtpp := &rtpPacket{}
		err := rtpp.UnmarshalTransport(layer)
		if err != nil {
			return err
		}

		err = rtpp.UnmarshalNetwork(ipv4, ipv6)
		if err != nil {
			return err
		}

		rtpp.SequenceNumber = p.SequenceNumber
		rtpp.Timestamp = p.Timestamp
		rtpp.Marker = p.Marker
		rtpp.SSRC = p.SSRC

		pack := storage.RtpPacket{
			Id:             uuid.New().String(),
			DstPort:        rtpp.DstPort,
			SrcPort:        rtpp.SrcPort,
			DstIp:          rtpp.DstIp,
			SrcIp:          rtpp.SrcIp,
			SequenceNumber: rtpp.SequenceNumber,
			Timestamp:      rtpp.Timestamp,
			Marker:         rtpp.Marker,
			Ssrc:           rtpp.SSRC,
			StandardTime: storage.StandardTime{
				CreatedAt: time.Now(),
				UpdatedAt: time.Now(),
			},
		}

		err = r.Storage.CreateRtpPacket(context.Background(), pack)
		if err != nil {
			return err
		}
	}
	return nil
}

func (r *rtpPacket) UnmarshalNetwork(ipv4 *layers.IPv4, ipv6 *layers.IPv6) error {
	if ipv4 != nil {
		r.SrcIp = ipv4.SrcIP.String()
		r.DstIp = ipv4.DstIP.String()
	}

	if ipv6 != nil {
		r.SrcIp = ipv6.SrcIP.String()
		r.DstIp = ipv6.DstIP.String()
	}
	return nil
}

func (r *rtpPacket) UnmarshalTransport(layer gopacket.Layer) error {
	var udp *layers.UDP
	var isUDP bool
	tcp, isTCP := layer.(*layers.TCP)
	if !isTCP {
		udp, isUDP = layer.(*layers.UDP)
		if !isUDP {
			return nil
		}
	}
	if tcp != nil {
		port, err := strconv.Atoi(tcp.DstPort.String())
		if err != nil {
			return err
		}
		r.DstPort = uint16(port)
		port, err = strconv.Atoi(tcp.SrcPort.String())
		if err != nil {
			return err
		}
		r.SrcPort = uint16(port)
	} else if udp != nil {
		port, err := strconv.Atoi(udp.DstPort.String())
		if err != nil {
			return err
		}
		r.DstPort = uint16(port)
		port, err = strconv.Atoi(udp.SrcPort.String())
		if err != nil {
			return err
		}
		r.SrcPort = uint16(port)
	} else {
		return nil
	}

	return nil
}
