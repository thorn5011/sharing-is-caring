package models

import "time"

type DNSResults struct {
	Server       string        `json:"Server"`
	Hostname     string        `json:"Hostname"`
	ResponseTime time.Duration `json:"ResponseTime"`
	Timestamp    time.Time     `json:"Timestamp"`
}

func (d *DNSResults) GetResponseTime() time.Duration {
	return d.ResponseTime
}

func (d *DNSResults) GetTimestamp() time.Time {
	return d.Timestamp
}

func (d *DNSResults) GetServer() string {
	if d.Server == "1.1.1.1:53" {
		return "Cloudflare"
	} else if d.Server == "8.8.8.8:53" {
		return "Google"
	} else if d.Server == "192.168.0.1:53" {
		return "Local"
	}
	return "Unknown"
}

type PingResults struct {
	Host         string        `json:"Host"`
	ResponseTime time.Duration `json:"ResponseTime"`
	Timestamp    time.Time     `json:"Timestamp"`
}

func (p *PingResults) GetResponseTime() time.Duration {
	return p.ResponseTime
}

func (p *PingResults) GetTimestamp() time.Time {
	return p.Timestamp
}
