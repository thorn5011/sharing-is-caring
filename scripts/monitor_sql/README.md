# Monitor SQL with python

**Purpose**: Display pixel flags in a Raspberry Sense led lights, visualizing the attacking county based of honeypot data.

---

## Pre-requisites

- API token to use [IpInfo](https://ipinfo.io/). Set as env `IPINFOTOKEN`
- SQL DB credentials. Set password as env `COWRIE_DB_PASSWORD`
- Data from [Cowrie honeypot](https://cowrie.readthedocs.io/en/latest/sql/README.html)
- Install packages from the [requirements.txt](requirements.txt)

---

## How does it work?

1. Connects to SQL db and grabs the last X minutes of sessions.
2. Compare new sessions with [last_processed_ids.csv](last_processed_ids.csv) to make sure we are not processing previously seen items.
3. Parses data and if successful sign-in flashes tow different images on the led.
4. Uses IpInfo to geolocate all IPs.
5. Summarize the sessions count based off country
6. Print the flag of all attacking counties. Use [flags.json](flags.json) as a lookup for ISO 3166 strings.

---

## Logs

Sample run:
```sh
2024-09-16 19:15:01,443 - INFO - [i] Starting a new session
--------------------------------
2024-09-16 19:15:02,152 - INFO - [x] New session detected! ID: 5b687703aff0, IP: 212.113.100.4, Country: DE (Frankfurt am Main), ASN: AS210644 AEZA INTERNATIONAL LTD, Hostname: fond-bit.aeza.network
...<removed>
2024-09-16 19:15:04,321 - INFO - [x] New session detected! ID: 447080b33343, IP: 104.177.35.157, Country: US (San Jose), ASN: AS7018 AT&T Services, Inc., Hostname: 104-177-35-157.lightspeed.sntcca.sbcglobal.net
2024-09-16 19:15:04,321 - INFO - [i] Sessions: 140, Geolocated: 140
2024-09-16 19:15:04,321 - INFO - [.] Printing the flag for CN
2024-09-16 19:15:54,557 - INFO - [!] No flag for BG
2024-09-16 19:15:54,557 - INFO - [.] Printing the flag for BG
2024-09-16 19:16:05,866 - INFO - [!] No flag for LT
2024-09-16 19:16:17,175 - INFO - [.] Printing the flag for JP
2024-09-16 19:16:40,492 - INFO - [.] Printing the flag for US
```

### Grab countries without a flag

`grep "No flag" app*.log | awk '{print $10}'| sort | uniq -c | sort`

Example:
```sh
     13 VN
      2 ES
      2 UA
      6 BG
```
To get a new flag, add the name to the [flags.json](flags.json), along with the pixel placements.
**Note** that you might have to add a new color translation in the [monitor_sql.py](monitor_sql.py) script.

---

## Continuos display

Setup a crontab entry to keep displaying the most recent attacks whenever you want, e.g. hourly, daily etc.

Example:
```sh
15 */1 * * * . /PATH/.envs && . /PATH/monitor_sql/monitor_sql/bin/activate && cd /PATH/monitor_sql && python /PATH/monitor_sql/monitor_sql.py
```
The crontab loads envs, activates the virtual environment, change into the script directory and executes the script.