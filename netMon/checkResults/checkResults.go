package main

import (
	"encoding/json"
	"fmt"
	"os"
	"strings"
	"time"

	"github.com/thorn5011/models"
)

func getResults(dns_filename, ping_filename string) ([]models.DNSResults, []models.PingResults, error) {
	var ping []models.PingResults
	var dns []models.DNSResults
	// Get DNS results
	if strings.Contains(dns_filename, "dns") {
		fmt.Println("[i] Opening the DNS results file..")
		existingData, err := os.ReadFile(dns_filename)
		if err != nil {
			fmt.Printf("Failed to open file: %v\n", err)
			return nil, nil, err
		}
		err = json.Unmarshal(existingData, &dns)
		if err != nil {
			fmt.Printf("Failed to unmarshal JSON: %v\n", err)
			return nil, nil, err
		}
		fmt.Printf("[i] Length of dns results: %d\n", len(dns))

		// Get Ping results
	} else {
		panic("DNS filename is invalid")
	}
	if strings.Contains(ping_filename, "ping") {
		fmt.Println("[i] Opening the PING results file..")
		existingData, err := os.ReadFile(dns_filename)
		if err != nil {
			fmt.Printf("Failed to open file: %v\n", err)
			return nil, nil, err
		}
		err = json.Unmarshal(existingData, &ping)
		if err != nil {
			fmt.Printf("Failed to unmarshal JSON: %v\n", err)
			return nil, nil, err
		}
		fmt.Printf("[i] Length of ping results: %d\n", len(dns))
	} else {
		panic("PING filename is invalid")
	}
	return dns, ping, nil
}

// func calculateAverageResponseTime(dns []models.DNSResults, ping []models.PingResults) {
// 	// Calculate average response time for DNS
// 	var dns_total time.Duration
// 	for _, d := range dns {
// 		fmt.Println(d.GetResponseTime())
// 		dns_total += d.GetResponseTime()
// 	}
// 	fmt.Printf("[debug] Total DNS response time: %v\n", dns_total)
// 	fmt.Println(time.Duration(len(dns)))
// 	fmt.Print("")
// 	dns_average := dns_total / time.Duration(len(dns))
// 	fmt.Printf("[i] Average DNS response time: %v\n", dns_average)

// 	// Calculate average response time for Ping
// 	var ping_total time.Duration
// 	for _, p := range ping {
// 		fmt.Println(p.GetResponseTime())
// 		ping_total += p.GetResponseTime()
// 	}
// 	fmt.Printf("[debug] Total Ping response time: %v\n", ping_total)

// 	ping_average := ping_total / time.Duration(len(ping))
// 	fmt.Printf("[i] Average Ping response time: %v\n", ping_average)
// }

func calculateAverageResponseTimePing(ping []models.PingResults) {
	// Calculate average response time for Ping
	var ping_total time.Duration
	for _, p := range ping {
		// fmt.Println(p.GetResponseTime())
		ping_total += p.GetResponseTime()
	}
	fmt.Printf("[debug] Total Ping response time: %v\n", ping_total)

	ping_average := ping_total / time.Duration(len(ping))
	fmt.Printf("[i] Average Ping response time: %v\n", ping_average)
}

func calculateAverageResponseTimeDns(dns []models.DNSResults) {
	// Calculate average response time per server for DNS
	serverMap := make(map[string]time.Duration)
	serverCount := make(map[string]int)

	for _, d := range dns {
		server := d.GetServer()
		responseTime := d.GetResponseTime()

		serverMap[server] += responseTime
		serverCount[server]++
	}
	// fmt.Printf("[debug] ServerMap: %v\n", serverMap)
	// fmt.Printf("[debug] ServerCount: %v\n", serverCount)
	for server, totalResponseTime := range serverMap {
		averageResponseTime := totalResponseTime / time.Duration(serverCount[server])
		fmt.Printf("[i] Average DNS response time for %s: %v\n", server, averageResponseTime)
	}
}

// ---------------------------------------------------------
// ---------------------------------------------------------
func main() {
	fmt.Println("[i] Starting the analysis..")
	dns_filename := "../data/dns_results.json"
	ping_filename := "../data/ping_results.json"
	dns, ping, err := getResults(dns_filename, ping_filename)

	// fmt.Println(ping)
	// fmt.Printf("-----------------------\n")
	// fmt.Printf("-----------------------\n")
	// fmt.Println(dns)

	if err != nil {
		fmt.Printf("Failed to get results: %v\n", err)
	}
	// fmt.Println(dns)
	// fmt.Println(ping)
	calculateAverageResponseTimePing(ping)
	calculateAverageResponseTimeDns(dns)
	fmt.Println("[i] Analysis complete..")

}
