package main

import (
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"net"
	"os"
	"strings"
	"sync"
	"time"

	"database/sql"
	"log"

	_ "github.com/go-sql-driver/mysql"
	"github.com/thorn5011/models"

	probing "github.com/prometheus-community/pro-bing"
)

var verbose bool

func main() {
	var err error
	var dnsServersInput string
	var hostnamesInput string
	var pingIpsInput string
	var pingTest bool
	var saveToFile bool
	var saveToSql bool
	var dnsTest bool
	flag.StringVar(&dnsServersInput, "servers", "1.1.1.1", "DNS Servers to use (comma separated)")
	flag.StringVar(&hostnamesInput, "hostnames", "google.com", "Hostnames to resolve (comma separated)")
	flag.StringVar(&pingIpsInput, "ips", "1.1.1.1", "IP to ping (one IP)")
	flag.BoolVar(&saveToFile, "save_to_file", false, "Save results to file (bool)")
	flag.BoolVar(&pingTest, "ping_test", false, "Perform ping test (bool)")
	flag.BoolVar(&dnsTest, "dns_test", false, "Perform DNS test (bool)")
	flag.BoolVar(&saveToSql, "save_to_sql", false, "Save results to SQL database (bool)")
	flag.BoolVar(&verbose, "verbose", false, "Verbose logging (bool)")
	fmt.Println("🚀 Starting network monitor...")
	flag.Usage = func() {
		fmt.Println("ℹ️ Usage: go run netMon.go [flags]")
		fmt.Println("-----")
		flag.PrintDefaults()
	}
	flag.Parse()
	if verbose {
		fmt.Println("ℹ️ Verbose logging enabled")
	}

	if !dnsTest && !pingTest {
		fmt.Println("⚠️ No tests selected. Exiting...")
		return
	}

	if dnsTest {
		// DNS test
		if verbose {
			fmt.Println("ℹ️ [DNS] Starting DNS test...")
		}
		dnsServers := strings.Split(dnsServersInput, ",")
		hostnames := strings.Split(hostnamesInput, ",")
		results := make([]models.DNSResults, 0)
		for _, dnsServer := range dnsServers {
			for _, hostname := range hostnames {
				duration, err := measureResponseTime(hostname, dnsServer)
				if err != nil {
					fmt.Println(err)
					continue
				}
				fmt.Printf("✅ [DNS] %-20s %-20s %s\n", dnsServer, hostname, duration)
				results = append(results, models.DNSResults{
					Server:       dnsServer,
					Hostname:     hostname,
					ResponseTime: duration,
					Timestamp:    time.Now(),
				})
			}

		}
		if saveToFile {
			filename := "../data/dns_results.json"
			err = appendToJSONFile(results, filename)
			if err != nil {
				fmt.Printf("⚠️ Failed to append to file: %v\n", err)
			}
		}
		if saveToSql {
			err = storeResultsInSQLTable(results)
			if err != nil {
				fmt.Printf("⚠️ Failed to save to SQL: %v\n", err)
			}
		}
	}

	if pingTest {
		var gatewayIP string = "192.168.0.1" // Replace with your gateway IP

		// Ping the gateway and a public IP
		pingResults := make([]models.PingResults, 0)

		var wg sync.WaitGroup
		wg.Add(2)
		go func() {
			host := pingIpsInput
			response_time, err := pingHost(host)
			if err != nil {
				fmt.Println(err)
			}
			pingResults = append(pingResults, models.PingResults{
				Host:         host,
				ResponseTime: response_time,
				Timestamp:    time.Now(),
			})
			wg.Done()
		}()
		go func() {
			host := gatewayIP
			response_time, err := pingHost(host)
			if err != nil {
				fmt.Println(err)
			}
			pingResults = append(pingResults, models.PingResults{
				Host:         host,
				ResponseTime: response_time,
				Timestamp:    time.Now(),
			})
			wg.Done()
		}()
		wg.Wait()

		if saveToFile {
			filename := "../data/ping_results.json"
			err = appendToJSONFile(pingResults, filename)
			if err != nil {
				fmt.Printf("⚠️ Failed to append to file: %v\n", err)
			}
		}
	}
}

func appendToJSONFile[T any](data []T, filename string) error {
	fmt.Println("ℹ️ [JSON] Appending to", filename)
	err := checkFile(filename)
	if err != nil {
		fmt.Printf("⚠️ Failed to create file: %v\n", err)
	}
	existingData, err := os.ReadFile(filename)
	if err != nil {
		fmt.Printf("⚠️ Failed to open file: %v\n", err)
	}
	// Unmarshal existing data into a slice of structs
	var existingSlice []T
	err = json.Unmarshal(existingData, &existingSlice)
	if err != nil {
		return err
	}
	existingSlice = append(existingSlice, data...)

	// Marshal the updated slice
	updatedData, err := json.MarshalIndent(existingSlice, "", "  ")
	if err != nil {
		return err
	}
	// Write the updated data to the file
	return os.WriteFile(filename, updatedData, 0644)
}

func storeResultsInSQLTable(results []models.DNSResults) error {
	if verbose {
		fmt.Println("ℹ️ [SQL] Storing results in SQL table")
	}
	// Open a connection to the database
	hostname, port, database := "192.168.0.187", "3306", "netMon"
	db, err := sql.Open("mysql", fmt.Sprintf("%s:%s@tcp(%s:%s)/%s", os.Getenv("NETMON_DB_USERNAME"), os.Getenv("NETMON_DB_PASSWORD"), hostname, port, database))
	if err != nil {
		return err
	}
	defer db.Close()

	// Create the table if it doesn't exist
	createTableQuery := `
		CREATE TABLE IF NOT EXISTS dns_results (
			id INT AUTO_INCREMENT PRIMARY KEY,
			server VARCHAR(255),
			hostname VARCHAR(255),
			response_time INT,
			timestamp DATETIME
		)
	`
	_, err = db.Exec(createTableQuery)
	if err != nil {
		return err
	}

	// Prepare the insert statement
	insertQuery := `
		INSERT INTO dns_results (server, hostname, response_time, timestamp)
		VALUES (?, ?, ?, ?)
	`
	stmt, err := db.Prepare(insertQuery)
	if err != nil {
		return err
	}
	defer stmt.Close()

	// Insert each result into the table
	for _, result := range results {
		// fmt.Println("[SQL] Inserting", result.ResponseTime.Milliseconds())
		_, err := stmt.Exec(result.Server, result.Hostname, result.ResponseTime.Milliseconds(), result.Timestamp)
		if err != nil {
			log.Println(err)
		}
	}
	return nil
}

func checkFile(filename string) error {
	_, err := os.Stat(filename)
	if os.IsNotExist(err) {
		_, err := os.Create(filename)
		if err != nil {
			return err
		}
	}
	return nil
}

func pingHost(ip string) (time.Duration, error) {
	if verbose {
		fmt.Println("ℹ️ [ICMP] Pinging", ip)
	}
	pinger, err := probing.NewPinger(ip)
	pinger.SetPrivileged(true)
	if err != nil {
		panic(err)
	}
	pinger.Count = 3
	err = pinger.Run() // Blocks until finished.
	if err != nil {
		panic(err)
	}
	stats := pinger.Statistics() // get send/receive/duplicate/rtt stats
	response_time := stats.AvgRtt
	fmt.Println("✅ [ICMP] Pinged", ip, "with an average response time of", response_time)
	return response_time, nil
}

func measureResponseTime(hostname, server string) (time.Duration, error) {
	if verbose {
		fmt.Printf("ℹ️ [DNS] Resolving '%s' using '%s'\n", hostname, server)
	}
	start := time.Now()
	resolver := &net.Resolver{
		PreferGo: true,
		// Dial: func(_, _ string) (net.Conn, error) {
		Dial: func(ctx context.Context, network, address string) (net.Conn, error) {
			return net.Dial("udp", server+":53")
		},
	}

	ip, err := resolver.LookupHost(context.Background(), hostname)
	if err != nil {
		return 0, err
	}
	if verbose {
		fmt.Printf("ℹ️ [DNS] Resolved '%s' to '%s'\n", hostname, ip)
	}
	return time.Since(start), nil
}
