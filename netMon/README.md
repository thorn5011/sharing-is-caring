
*This code was used to learn some `go` scripting and connect it together with a SQL DB*

# Monitor the network by DNS

1. Monitor the network by looping through few DNS servers and hostnames.
2. Store the response time as results in a SQL DB
3. ???
4. PROFIT

Run the script by `go run startMonitor/netMon.go -h` for get help.

**Examples**:
```sh
# Resolve 1 domain on 2 servers
go run .\netMon.go -dns_test -hostnames pi.hole -servers 192.168.0.187,8.8.4.4

# Resolve 2 domains, save to SQL and enable verbose logging
go run .\netMon.go -dns_test -hostnames pi.hole,nwt.se -servers 192.168.0.187 -save_to_sql -verbose

# Ping specific IP
go run .\netMon.go -ping_test -ips 1.1.1.1
```
## Output

You can output results to JSON or SQL (only supports DNS results). To export SQL, configure server IP, port and environment variables as needed. 

### Environment variables

Set variables in Windows:
```bat
setx NETMON_DB_USERNAME netMon_user /m
setx NETMON_DB_PASSWORD KEY /m
```

In Linux:
```sh
export NETMON_DB_USERNAME=netMon_user
export NETMON_DB_PASSWORD=KEY
```

---
# Set up SQL for persistent storage

Grab your favorite DB, I am using MariaDB, and get that new shining server up and running!

## Structure and permission
```sql
CREATE DATABASE netMon;
CREATE USER 'netMon_user'@'192.168.0.187' IDENTIFIED BY 'KEY';
GRANT CREATE, SELECT, INSERT ON netMon.* TO 'netMon_user'@'192.168.0.187';
-- show permissions
SHOW GRANTS FOR 'netMon_user'@'192.168.0.187';
-- revoke grants if needed
-- REVOKE SELECT, INSERT, CREATE ON netMon.* FROM netMon_user@127.0.0.1;
```

---
# Regular monitoring with crontab

This is how I currently execute the script, with crontab:
```sh
*/5 * * * * . /root/.envs && cd PATH/net_mon/startMonitor && /usr/local/go/bin/go run /PATH/netMon/startMonitor/netMon.go >> PATH/netMon/startMonitor/app.log
```

`. /root/.envs` is for the crontab to be able to access the credentials. 
