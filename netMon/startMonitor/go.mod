module github.com/thorn5011/netMon

go 1.23.0

require (
	github.com/go-sql-driver/mysql v1.8.1
	github.com/prometheus-community/pro-bing v0.4.1
	github.com/thorn5011/models v0.0.0-00010101000000-000000000000
)

require (
	filippo.io/edwards25519 v1.1.0 // indirect
	github.com/google/uuid v1.6.0 // indirect
	golang.org/x/net v0.27.0 // indirect
	golang.org/x/sync v0.7.0 // indirect
	golang.org/x/sys v0.22.0 // indirect
)

replace github.com/thorn5011/models => ../models
