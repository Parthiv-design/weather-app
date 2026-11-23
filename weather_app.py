from flask import Flask, render_template, request, redirect, url_for, flash
from flask_cors import CORS
import requests
from datetime import datetime
import urllib.parse

app = Flask(__name__)
CORS(app)
app.secret_key = 'weather_app_secure_vault_key'

WMO_CODES = {
    0: "Clear sky ☀️", 1: "Mainly clear 🌤️", 2: "Partly cloudy ⛅", 3: "Overcast ☁️",
    45: "Foggy 🌫️", 48: "Depositing rime fog 🌫️",
    51: "Light drizzle 🌧️", 53: "Moderate drizzle 🌧️", 55: "Dense drizzle 🌧️",
    61: "Slight rain 🌧️", 63: "Moderate rain 🌧️", 65: "Heavy rain 🌧️",
    71: "Slight snow ❄️", 73: "Moderate snow ❄️", 75: "Heavy snow ❄️",
    80: "Light showers 🌦️", 81: "Mod. showers 🌦️", 82: "Violent showers 🌧️",
    85: "Slight snow shwrs 🌨️", 86: "Heavy snow shwrs 🌨️", 95: "Thunderstorm ⛈️"
}

def get_condition_type(wmo_code):
    try:
        code = int(wmo_code)
        if code in (0, 1, 2, 3):
            return "clear"
        elif code in (45, 48):
            return "fog"
        elif code in (51, 53, 55):
            return "drizzle"
        elif code in (61, 63, 65, 80, 81, 82):
            return "rain"
        elif code in (71, 73, 75, 85, 86):
            return "snow"
        elif code in (95,):
            return "thunderstorm"
        return "clear"
    except:
        return "clear"

def get_temp_class(celsius_val):
    try:
        val = float(celsius_val)
        if val >= 25:
            return "temp-hot"
        elif val >= 10:
            return "temp-warm"
        elif val >= 0:
            return "temp-cool"
        else:
            return "temp-cold"
    except:
        return "temp-cool"

def to_fahrenheit(celsius_val):
    try:
        return round((float(celsius_val) * 9 / 5) + 32)
    except:
        return 0

def format_day(date_str):
    return datetime.strptime(date_str, "%Y-%m-%d").strftime("%a, %b %d")

def format_hour(time_str):
    return datetime.strptime(time_str, "%Y-%m-%dT%H:%M").strftime("%I %p").lstrip('0')

@app.route('/')
def home():
    city_query = request.args.get('city', '').strip()
    headers = {"User-Agent": "MyWeatherApp/1.0", "Accept": "application/json"}
    
    # Establish absolute local defaults
    lat, long, display_name = 51.05, -114.07, "Calgary, Canada"
    # FIX: Added an explicit timezone tracking string to stabilize requests
    target_timezone = "America/Edmonton"

    # Scenario A: User executed an active search lookup
    if city_query:
        safe_query = urllib.parse.quote(city_query)
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={safe_query}&count=1&language=en&format=json"
        
        try:
            geo_res = requests.get(geo_url, headers=headers).json()
            if "results" in geo_res and len(geo_res["results"]) > 0:
                geo_data = geo_res["results"][0]
                lat, long = round(geo_data["latitude"], 2), round(geo_data["longitude"], 2)
                
                # Capture the explicit timezone key returned by the geocoder database
                target_timezone = geo_data.get('timezone', 'auto')
                
                state = geo_data.get('admin1', '')
                country = geo_data.get('country', '')
                if state and state != geo_data['name']:
                    display_name = f"{geo_data['name']}, {state}, {country}"
                else:
                    display_name = f"{geo_data['name']}, {country}"
            else:
                flash(f"Could not find any city matching '{city_query}'. Showing default location.")
                return redirect(url_for('home'))
        except Exception as e:
            flash("Geocoding validation timeout. Showing default location.")
            return redirect(url_for('home'))
            
    # Scenario B: No search parameters — detect location via client routing IP
    else:
        user_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        if user_ip == '127.0.0.1' or user_ip.startswith('192.168.') or user_ip.startswith('192.0.'):
            lat, long, display_name = 51.05, -114.07, "Calgary, Canada"
            target_timezone = "America/Edmonton"
        else:
            try:
                ip_url = f"http://ip-api.com/json/{user_ip}?fields=status,city,country,lat,lon,timezone"
                ip_res = requests.get(ip_url, timeout=3).json()
                if ip_res.get("status") == "success" and ip_res.get("country") != "":
                    lat = round(ip_res["lat"], 2)
                    long = round(ip_res["lon"], 2)
                    display_name = f"{ip_res['city']}, {ip_res['country']}"
                    target_timezone = ip_res.get('timezone', 'America/Edmonton')
            except:
                pass

    # FIX: Replaced &timezone=auto with the explicit, sanitized time zone name variable string
    weather_url = (
        f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={long}"
        f"&current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m"
        f"&hourly=temperature_2m,weather_code&daily=temperature_2m_max,temperature_2m_min,weather_code"
        f"&forecast_days=14&timezone={urllib.parse.quote(target_timezone)}"
    )
    
    try:
        response = requests.get(weather_url, headers=headers)
        data = response.json()
        
        if "current" in data:
            current = data["current"]
            units = data.get("current_units", {})
            h_unit = units.get("relative_humidity_2m", "%")
            w_unit = units.get("wind_speed_10m", " km/h")
            
            hourly_list = []
            for i in range(24):
                temp_raw = data["hourly"]["temperature_2m"][i]
                hourly_list.append({
                    "time": format_hour(data["hourly"]["time"][i]),
                    "temp": round(temp_raw),
                    "temp_f": to_fahrenheit(temp_raw),
                    "condition": WMO_CODES.get(data["hourly"]["weather_code"][i], "Clear sky ☀️").split()[-1]
                })

            daily_list = []
            for i in range(14):
                max_raw = data["daily"]["temperature_2m_max"][i]
                min_raw = data["daily"]["temperature_2m_min"][i]
                daily_list.append({
                    "day": format_day(data["daily"]["time"][i]),
                    "max": round(max_raw),
                    "min": round(min_raw),
                    "max_f": to_fahrenheit(max_raw),
                    "min_f": to_fahrenheit(min_raw),
                    "condition": WMO_CODES.get(data["daily"]["weather_code"][i], "Clear sky ☀️")
                })

            current_temp_raw = current["temperature_2m"]
            current_feels_raw = current["apparent_temperature"]

            weather_data = {
                "city": display_name, "lat": lat, "long": abs(long),
                "condition": WMO_CODES.get(current["weather_code"], "Unknown conditions 🤷"),
                "condition_type": get_condition_type(current["weather_code"]),
                "temp": f"{round(current_temp_raw, 1)}°C",
                "temp_f": f"{round((current_temp_raw * 9/5) + 32, 1)}°F",
                "temp_class": get_temp_class(current_temp_raw),
                "feels_like": f"{round(current_feels_raw, 1)}°C",
                "feels_like_f": f"{round((current_feels_raw * 9/5) + 32, 1)}°F",
                "humidity": f"{current['relative_humidity_2m']}{h_unit}",
                "wind": f"{current['wind_speed_10m']}{w_unit}",
                "hourly": hourly_list,
                "seven_day": daily_list[:7],
                "fourteen_day": daily_list
            }
            return render_template('index.html', weather=weather_data)
        else:
            return render_template('index.html', weather={"error": "Weather payload missing form structures. Server timezone rejection."})
    except Exception as e:
        return render_template('index.html', weather={"error": f"Connection Failure: {str(e)}"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
