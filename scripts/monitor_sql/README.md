# Monitor SQL with python

**Purpose**: Display pixel flags in a Raspberry Sense led lights, visualizing the attacking county based of honeypot data.

## Pre-requisites

- API token to use [IpInfo](https://ipinfo.io/). Set as env `IPINFOTOKEN`
- SQL DB credentials. Set password as env `COWRIE_DB_PASSWORD`
- Data from [Cowrie honeypot](https://cowrie.readthedocs.io/en/latest/sql/README.html)
- Install packages from the [requirements.txt](requirements.txt)


## How does it work?

1. Connects to SQL db and grabs the last X minutes of sessions.
2. Compare new sessions with [last_processed_ids.csv](last_processed_ids.csv) to make sure we are not processing previously seen items.
3. Parses data and if successful sign-in flashes tow different images on the led.
4. Uses IpInfo to geolocate all IPs.
5. Summarize the sessions count based off country
6. Print the flag of all attacking counties. Use [flags.json](flags.json) as a lookup for ISO 3166 strings.


