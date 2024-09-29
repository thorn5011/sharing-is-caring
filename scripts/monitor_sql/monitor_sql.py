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
cached_geolocation_data = []
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

# Database connection details
db_config = {
    "user": "cowrie",
    "password": os.getenv("COWRIE_DB_PASSWORD"),
    "host": "localhost",
    "database": "cowrie",
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


def check_cached_session_geo_data(ip: str) -> Union[dict | None]:
    for e in cached_geolocation_data:
        if e.ip == ip:
            return e
    return None


# def update_geodata_to_db(geo:GeolocationData) -> None:
#     # data = {"ip": "1.1.1.1", "hostname": "one.one.one.one", "anycast": True, "city": "Jakarta", "region": "Jakarta", "country": "ID", "loc": "-6.2146,106.8451", "org": "AS13335 Cloudflare, Inc.", "timezone": "Asia/Jakarta"}
#     logging.debug("[i] Updating geolocation data to the database")
    # insert_geodata_to_db(geo)


def insert_geodata_to_db(geo: GeolocationData) -> None:
    logging.debug("[i] Inserting geolocation data to the database")
    # not working, timezone, region, org
    connection = connect_to_db()
    cursor = connection.cursor()
    query = "INSERT INTO geoloc (ip, hostname, org, city, region, country, timezone, anycast) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
    try:
        cursor.execute(query, (geo.ip, geo.hostname, geo.org, geo.city, geo.region, geo.country, geo.timezone, geo.anycast))
        connection.commit()
    except mysql.IntegrityError:
        logging.error(f"[x] Duplicate entry or some other error. Failed to insert: {geo.ip}")
    finally:
        cursor.close()
        connection.close()


def get_geodata_from_db(ip:str) -> list:
    logging.debug(f"[i] Fetching geolocation data from the database, IP: {ip}")
    connection = connect_to_db()
    cursor = connection.cursor(dictionary=True)
    query = "SELECT ip, hostname, org, city, region, country, timezone, anycast, date_added FROM geoloc WHERE ip = %s"
    cursor.execute(query, (ip,))
    rows = cursor.fetchall()
    cursor.close()
    connection.close()
    logging.debug(f"[i] Geolocation data fetched from the database: {rows}" )
    return rows


def get_ip_geolocation(ip_address: str) -> Union[GeolocationData, None]:
    # Check if the geolocation data is already been seen this session, else get from SQL
    cached_geo_data = check_cached_session_geo_data(ip_address)
    if cached_geo_data:
        logging.debug("[i] Using geo data from session cache")
        return cached_geo_data
    
    sql_geo_data = get_geodata_from_db(ip_address)
    if len(sql_geo_data) > 1:
        logging.error(f"[!] Multiple entries found for IP: {ip_address}")
        return None
    else:
        sql_geo_data = sql_geo_data[0] if sql_geo_data else None
    if sql_geo_data:
        if sql_geo_data.get("date_added") < datetime.datetime.now() - datetime.timedelta(days=90):
            logging.debug("[i] Geolocation data is older than 90 days. Updating the data.")
        else:
            logging.debug("[i] Using geo data from SQL")
            geo = GeolocationData(
                sql_geo_data.get("ip"),
                sql_geo_data.get("hostname"),
                sql_geo_data.get("anycast"),
                sql_geo_data.get("city"),
                sql_geo_data.get("region"),
                sql_geo_data.get("country"),
                sql_geo_data.get("loc"),
                sql_geo_data.get("org"),
                sql_geo_data.get("timezone"),
                sql_geo_data.get("date_added"),
            )
            return sql_geo_data
    logging.debug("[i] Geolocation data not found in the cache or SQL. Fetching from the API")
    api_url = f"https://ipinfo.io/{ip_address}/json?token={IPINFOTOKEN}"

    try:
        # Sending the request to the API
        logging.debug(f"[i] Sending a request to the API for IP: {ip_address}")
        response = requests.get(api_url)
        # Check if the request was successful
        if response.status_code == 200:
            # Parse the JSON response
            geolocation_data = response.json()
            geo = GeolocationData(
                geolocation_data.get("ip"),
                geolocation_data.get("hostname", "N/A"),
                geolocation_data.get("anycast", False),
                geolocation_data.get("city", "N/A"),
                geolocation_data.get("region", "N/A"),
                geolocation_data.get("country", "N/A"),
                geolocation_data.get("loc", "N/A"),
                geolocation_data.get("org", "N/A"),
                geolocation_data.get("timezone", "N/A"),
            )
            cached_geolocation_data.append(geo)
            insert_geodata_to_db(geo)
            return geo
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
                logging.info(
                    f"[x] New session detected! ID: {session_id}, IP: {ip}, Country: {location.country} ({location.city}), Org: {location.org}, Hostname: {location.hostname}"
                )
                actors.append(
                    {
                        "session_id": session_id,
                        "ip": ip,
                        "country": location.country,
                        "city": location.city,
                        "org": location.org,
                        "hostname": location.hostname,
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
    new_rows = get_sessions_from_db()
    if new_rows:
        actors = process_sessions(new_rows)
    else:
        logging.debug("[i] No new sessions detected.")
    flag_summary(actors)
    sense.clear()


############################################################################################################
if __name__ == "__main__":
    logging.info("--------------------------------")
    logging.info("[i] Starting a new session")
    logging.info("--------------------------------")
    # send_flag("NO")
    monitor_sessions()
