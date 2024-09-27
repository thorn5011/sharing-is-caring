import mysql.connector
import time
import csv
import datetime
import requests
import logging
import os
import json

from typing import Union
from sense_hat import SenseHat


# Configure logging
logging.basicConfig(
    filename="app.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
sense = SenseHat()
sense.low_light = True
sense.set_rotation(180)
geolocation = []
IPINFOTOKEN = os.getenv("IPINFOTOKEN")

colors = {
    "r": (255, 0, 0),
    "o": (255, 127, 0),
    "y": (255, 255, 0),
    "g": (0, 255, 0),
    "dg": (0, 106, 78), # dark green
    "bl": (0, 0, 0),
    "i": (75, 0, 130),
    "v": (159, 0, 255),
    "b": (0, 0, 255),
    "db": (0, 0, 139),  # dark blue
    "lb": (122, 197, 205),  # light blue
    "rb": (0, 43, 127),  # royal blue
    "w": (255, 255, 255),  # White
}


class GeolocationData:
    def __init__(self, ip, hostname, anycast, city, region, country, loc, org, timezone):
        self.ip = ip
        self.hostname = hostname
        self.anycast = anycast
        self.city = city
        self.region = region
        self.country = country
        self.loc = loc
        self.org = org
        self.timezone = timezone


def check_geo_data(ip: str) -> Union[dict | None]:
    for e in geolocation:
        if e["ip"] == ip:
            return e
    return None


def update_geodata_to_db(data:dict) -> None:
    data = {
    "ip": "1.1.1.1",
    "hostname": "one.one.one.one",
    "anycast": True,
    "city": "Jakarta",
    "region": "Jakarta",
    "country": "ID",
    "loc": "-6.2146,106.8451",
    "org": "AS13335 Cloudflare, Inc.",
    "timezone": "Asia/Jakarta"
    }
    # {'ip': '154.213.184.15', 'country': 'NL', 'city': 'Kerkrade', 'asn': 'AS51396 Pfcloud UG', 'hostname': 'N/A'}
    logging.debug("[i] Updating geolocation data to the database")
    geo = GeolocationData(
        data.get("ip"),
        data.get("hostname", None),
        data.get("anycast", None),
        data.get("city", None),
        data.get("region", None),
        data.get("country", None),
        data.get("loc", None),
        data.get("org", None),
        data.get("timezone", None)
    )
    row = get_geodata_from_db(geo.ip)
    if not row:
        insert_geodata_to_db(geo.ip, geo.hostname, geo.org, geo.city, geo.country, geo.timezone, geo.anycast)
    else:
        logging.debug(f"[i] Geolocation data already exists in the database, data: {row}", )
        if len(row) > 1:
            logging.error("[x] Multiple entries found for the same IP address. This should not happen.")
        elif row[0].get("date_added") < datetime.datetime.now() - datetime.timedelta(days=90):
            logging.debug("[i] Geolocation data is older than 90 days. Updating the data.")
            update_geodata_to_db(geo.ip)
        else:
            logging.debug("[i] Geolocation data has been updated recently or is not older than 90 days. Skipping the update.")


def insert_geodata_to_db(ip: str, hostname: str, org: str, city: str, region: str, country: str, timezone: str, anycast: str) -> None:
    connection = connect_to_db()
    cursor = connection.cursor()
    query = "INSERT INTO geoloc (ip, hostname, org, city, region, country, timezone, anycast) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
    try:
        cursor.execute(query, (ip, hostname, org, city, region, country, timezone, anycast))
        connection.commit()
    except mysql.IntegrityError:
        logging.error("[x] Duplicate entry or some other error. Failed to insert: ", ip)
    finally:
        cursor.close()
        connection.close()


def get_ip_geolocation(ip_address: str) -> dict:
    geo_data = check_geo_data(ip_address)
    if geo_data:
        logging.debug("[i] Using cached geo data")
        return geo_data
    # API endpoint for ipinfo.io
    api_url = f"https://ipinfo.io/{ip_address}/json?token={IPINFOTOKEN}"

    try:
        # Sending the request to the API
        response = requests.get(api_url)
        # Check if the request was successful
        if response.status_code == 200:
            # Parse the JSON response
            geolocation_data = response.json()
            # Extract relevant fields: country, city, and ASN (if available)
            country = geolocation_data.get("country", "N/A")
            city = geolocation_data.get("city", "N/A")
            asn_info = geolocation_data.get("org", "N/A")
            hostname = geolocation_data.get("hostname", "N/A")
            res = {
                "ip": ip_address,
                "country": country,
                "city": city,
                "asn": asn_info,
                "hostname": hostname,
            }
            geolocation.append(res)
            return res
        else:
            # Free usage of our API is limited to 50,000 API requests per month
            # https://ipinfo.io/developers#rate-limits
            logging.error(
                f"[!] Failed to get geolocation for IP {ip_address}: {response.status_code}"
            )
            return None
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return None


def get_flag(flag: str) -> list:
    with open("flags.json") as f:
        d = json.load(f)
        return d.get(flag)


def send_flag(flag_code: str) -> None:
    flag = get_flag(flag_code)
    if not flag:
        flag = get_flag("QUESTIONMARK")
        logging.info(f"[!] No flag for {flag_code}")

    new = []
    logging.info(f"[.] Printing the flag for {flag_code}")
    for pixels in flag:
        new.append(colors.get(pixels))
    sense.set_pixels(new)
    time.sleep(5)
    sense.clear()


# Database connection details
db_config = {
    "user": "cowrie",
    "password": os.getenv("COWRIE_DB_PASSWORD"),
    "host": "localhost",
    "database": "cowrie",
}


# Connect to the database
def connect_to_db() -> mysql.connector.connection.MySQLConnection:
    connection = mysql.connector.connect(**db_config)
    return connection


# Get the last processed session IDs to avoid reprocessing old records
def get_last_processed_sessions() -> Union[int, list]:
    try:
        with open("last_processed_ids.csv", "r") as file:
            data = list(csv.reader(file, delimiter=","))
            if not data:
                return []
            for row in data:
                if len(row) > 1000:
                    print("[i] A lot of data, stripping old entries")
                    return row[500:]
                else:
                    return row
    except FileNotFoundError:
        return 0


# Save the last processed session ID
def save_last_processed_id(old_ids: list, new_ids: list) -> None:
    with open("last_processed_ids.csv", "w") as file:
        write = csv.writer(file)
        combined = [*old_ids, *new_ids]
        write.writerow(combined)


def flag_summary(actors: list) -> None:
    # summary = {"BR": 1, "US": 3, "CN": 10, "UNKNOWN": 3}
    summary = {}
    for actor in actors:
        if actor.get("country") in summary.keys():
            summary[actor.get("country")] = summary[actor.get("country")] + 1
        else:
            summary[actor.get("country")] = 1
    print(f"[i] Country stats: {summary}")

    summary = {k: v for k, v in sorted(summary.items(), key=lambda item: item[1])}
    for country, count in summary.items():
        send_flag(country)
        red = (255, 0, 0)
        sense.show_message(f"{count}", text_colour=red, scroll_speed=0.35)   # The bigger the number, the lower the speed.


def process_sessions(sessions:list) -> list:
    actors = []
    last_processed_sessions = get_last_processed_sessions()
    last_processed_sessions = last_processed_sessions if last_processed_sessions else []
    rows = (
        [row for row in sessions if row["id"] not in last_processed_sessions]
        if last_processed_sessions
        else sessions
    )
    ids = [row["id"] for row in rows]
    save_last_processed_id(last_processed_sessions, ids)
    if rows:
        for row in rows:
            session_id = row["id"]
            ip = row["ip"]
            success = row["success"]
            username = row["username"]
            password = row["password"]
            if success == 1:
                logging.critical(f"[!] Successful sign-in by ID: {session_id}, IP: {ip} ({username} / {password})")
                for i in range(100):
                    color_code = get_flag("BLACK") if i % 2 else get_flag("EXCLAMATION")
                    rbg_code = []
                    for pixels in color_code:
                        rbg_code.append(colors.get(pixels))
                    sense.set_pixels(rbg_code)
                    time.sleep(0.2)
            location = get_ip_geolocation(ip)
            if location:
                update_geodata_to_db(location)
                logging.info(
                    f"[x] New session detected! ID: {session_id}, IP: {ip}, Country: {location.get('country')} ({location.get('city')}), ASN: {location.get('asn')}, Hostname: {location.get('hostname')}"
                )
                actors.append(
                    {
                        "session_id": session_id,
                        "ip": ip,
                        "country": location.get("country"),
                        "city": location.get("city"),
                        "asn": location.get("asn"),
                        "hostname": location.get("hostname"),
                    }
                )
            else:
                logging.info(
                    f"[x] New session detected! ID: {session_id}, IP: {ip}, No geo data due to error or rate limits"
                )
    else:
        logging.debug("[i] No new sessions detected.")
    logging.info(f"[i] Sessions: {len(rows)}, Geolocated: {len(actors)}")
    return actors


def get_geodata_from_db(ip:str) -> list:
    logging.debug(f"[i] Fetching geolocation data from the database, IP: {ip}")
    connection = connect_to_db()
    cursor = connection.cursor(dictionary=True)
    query = "SELECT ip, hostname, org, city, region, country, timezone, anycast, data_added FROM geoloc WHERE ip = %s"
    cursor.execute(query, (ip,))
    rows = cursor.fetchall()
    cursor.close()
    connection.close()
    logging.debug("[i] Geolocation data fetched from the database: ", rows)
    return rows


def get_sessions_from_db() -> list:
    connection = connect_to_db()
    cursor = connection.cursor(dictionary=True)
    minutes_ago = 120
    # query = "SELECT id, ip FROM sessions WHERE starttime > %s ORDER BY starttime ASC"
    query = "SELECT sessions.id, sessions.ip, auth.username, auth.password, auth.success FROM sessions JOIN auth ON sessions.id = auth.session WHERE starttime > %s ORDER BY starttime ASC"
    last_minutes = datetime.datetime.now() - datetime.timedelta(minutes=minutes_ago)
    cursor.execute(query, (last_minutes,))
    new_rows = cursor.fetchall()
    cursor.close()
    connection.close()
    return new_rows


# Monitor the sessions table for new inserts
def monitor_sessions():
    actors = []
    update_geodata_to_db({"asd": "asd"})
    import sys
    sys.exit(0)
    new_rows = get_sessions_from_db()
    if new_rows:
        actors = process_sessions(new_rows)
    else:
        logging.debug("[i] No new sessions detected.")
    flag_summary(actors)
    sense.clear()


if __name__ == "__main__":
    logging.info("--------------------------------")
    logging.info("[i] Starting a new session")
    logging.info("--------------------------------")
    # send_flag("NO")
    monitor_sessions()

# todo: store the ipinfo into the DB for a while, e.g. 30 days