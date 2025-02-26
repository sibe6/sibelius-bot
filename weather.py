import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

server_url = "http://opendata.fmi.fi/wfs"

async def get_weather(location, timestep=None):
    if timestep is None:
        timestep = 180

    params = {
        "service": "WFS",
        "version": "2.0.0",
        "request": "GetFeature",
        "storedquery_id": "fmi::forecast::harmonie::surface::point::timevaluepair",
        "place": location,
        "timestep": timestep,
    }

    response = requests.get(server_url, params=params)

    root = ET.fromstring(response.text)

    namespaces = {
        'wfs': 'http://www.opengis.net/wfs/2.0',
        'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
        'xlink': 'http://www.w3.org/1999/xlink',
        'om': 'http://www.opengis.net/om/2.0',
        'omso': 'http://inspire.ec.europa.eu/schemas/omso/3.0',
        'ompr': 'http://inspire.ec.europa.eu/schemas/ompr/3.0',
        'gml': 'http://www.opengis.net/gml/3.2',
        'gmd': 'http://www.isotc211.org/2005/gmd',
        'gco': 'http://www.isotc211.org/2005/gco',
        'swe': 'http://www.opengis.net/swe/2.0',
        'gmlcov': 'http://www.opengis.net/gmlcov/1.0',
        'sam': 'http://www.opengis.net/sampling/2.0',
        'sams': 'http://www.opengis.net/samplingSpatial/2.0',
        'wml2': 'http://www.opengis.net/waterml/2.0',
        'target': 'http://xml.fmi.fi/namespace/om/atmosphericfeatures/1.1',
        'ns0': 'http://www.opengis.net/om/2.0',
        'ns1': 'http://www.opengis.net/waterml/2.0',
        'ns2': 'http://www.opengis.net/gml/3.2'
    }

    members = root.findall('.//wfs:member', namespaces)

    if len(members) >= 3:
        third_member = members[2]

        result = third_member.find('.//om:result', namespaces)

        points = result.findall('.//ns1:point', namespaces)

        time_values = []
        temperature_values = []

        for point in points:
            time_element = point.find('.//ns1:time', namespaces)
            value_element = point.find('.//ns1:value', namespaces)

            if time_element is not None and value_element is not None:
                time_values.append(time_element.text)
                temperature_values.append(float(value_element.text))

        day_forecasts = {}
        for time, temperature in zip(time_values, temperature_values):
            day = convert_to_finnish_time(time).split()[0]
            if day not in day_forecasts:
                day_forecasts[day] = []
            day_forecasts[day].append((time, temperature))

        message = ""

        for day, forecasts in day_forecasts.items():
            message += f"**{day}**\n"
            for time, temperature in forecasts:
                message += f"\t{convert_to_finnish_time(time).split()[1]}: {temperature}°C\n"

        return message

def convert_to_finnish_time(utc_time_str):
    utc_time = datetime.fromisoformat(utc_time_str.replace('Z', '+00:00'))

    summer_timezone = timezone(timedelta(hours=3)) # EEST (UTC+3)
    winter_timezone = timezone(timedelta(hours=2)) # EET (UTC+2)

    summer_start = datetime(utc_time.year, 3, 31, tzinfo=summer_timezone) - timedelta(days=datetime(utc_time.year, 3, 31).weekday() + 1)
    summer_end = datetime(utc_time.year, 10, 31, tzinfo=summer_timezone) - timedelta(days=datetime(utc_time.year, 10, 31).weekday() + 1)
    if summer_start <= utc_time < summer_end:
        localized_time = utc_time.astimezone(summer_timezone)
        return localized_time.strftime("%A %H:%M")

    localized_time = utc_time.astimezone(winter_timezone)
    return localized_time.strftime("%A %H:%M")
