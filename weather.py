# =============================================================================
# PARIS WEATHER  ->  GMAIL  (single-file Python automation)
# =============================================================================
# What this script does, step by step:
#   1. Asks the Open-Meteo API for the CURRENT weather in Paris
#   2. Turns the numeric weather code into readable text (e.g. 3 -> "Overcast")
#   3. Prints a summary in the console
#   4. Emails the same report to you through Gmail SMTP
#
# Before running, replace the THREE values in the "YOUR SETTINGS" section below.
# =============================================================================

import requests
import smtplib

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


# =============================================================================
# YOUR SETTINGS  (replace these three values manually)
# =============================================================================

SENDER_EMAIL = "thahrinah05@gmail.com"                       # Gmail account that SENDS the email
SENDER_PASSWORD = "cwjp dkou chbq vlqj"     # Google App Password (16 characters, no spaces)
RECEIVER_EMAIL = "yoga162006@gmail.com"                       # Address that RECEIVES the email


# =============================================================================
# FIXED SETTINGS  (you normally do not need to change these)
# =============================================================================

# --- Location: Paris, France ---
LOCATION_NAME = "Paris, France"
LATITUDE = 48.8566
LONGITUDE = 2.3522
TIMEZONE = "Europe/Paris"

# --- Weather API (Open-Meteo, free, no API key needed) ---
WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast"

# --- Gmail SMTP ---
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# --- Email subject ---
EMAIL_SUBJECT = "Daily Weather Update - Paris, France"

# --- Weather code -> readable text ---
# Open-Meteo returns a number (weather_code). This dictionary translates it.
WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


# =============================================================================
# STEP 1: GET THE WEATHER
# =============================================================================

def get_weather():
    """
    Calls the Open-Meteo API and returns a dictionary with the weather data.
    Returns None if anything goes wrong (an error message is printed).
    """

    # These are the "query parameters" added to the URL
    # (the final URL looks like ...forecast?latitude=48.8566&longitude=2.3522&...)
    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "current": "temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m",
        "timezone": TIMEZONE,
    }

    try:
        # Send the GET request. timeout=10 means "give up after 10 seconds".
        response = requests.get(WEATHER_API_URL, params=params, timeout=10)

        # Check the HTTP response BEFORE reading the JSON.
        # Status code 200 means "OK". Anything else is a problem.
        if response.status_code != 200:
            print(f"Weather API error: server replied with HTTP status {response.status_code}")
            return None

        # Convert the response text into a Python dictionary
        data = response.json()

        # The weather values live inside a "current" section
        current = data.get("current")
        if not current:
            print("Weather API error: invalid API response (no 'current' weather data found)")
            return None

        # Pull out each value we need. If one is missing, KeyError is raised below.
        weather = {
            "time": current["time"],                            # e.g. "2026-09-19T14:30"
            "temperature": current["temperature_2m"],           # degrees Celsius
            "feels_like": current["apparent_temperature"],      # degrees Celsius
            "humidity": current["relative_humidity_2m"],        # percent
            "wind_speed": current["wind_speed_10m"],            # km/h
            "weather_code": current["weather_code"],            # number, translated below
        }

        # Translate the code into text. Unknown codes get a default message.
        weather["description"] = WEATHER_CODES.get(
            weather["weather_code"], "Unknown weather condition"
        )

        # Make the timestamp easier to read: "2026-09-19T14:30" -> "2026-09-19 14:30"
        weather["time"] = str(weather["time"]).replace("T", " ")

        print("Weather information retrieved successfully")
        return weather

    except requests.exceptions.ConnectionError:
        print("Internet connection error: could not reach the weather service. Check your connection.")
    except requests.exceptions.Timeout:
        print("Weather API error: the request timed out. Please try again.")
    except requests.exceptions.RequestException as error:
        print(f"Weather API error: {error}")
    except ValueError:
        print("Weather API error: the response was not valid JSON")
    except KeyError as error:
        print(f"Weather API error: invalid API response (missing field {error})")
    except Exception as error:
        print(f"Unexpected error while getting weather: {error}")

    return None


# =============================================================================
# STEP 2: SHOW THE WEATHER IN THE CONSOLE
# =============================================================================

def print_weather(weather):
    """Prints a neat weather summary in the console."""
    print()
    print("================================")
    print("PARIS WEATHER")
    print("================================")
    print()
    print(f"Location: {LOCATION_NAME}")
    print(f"Temperature: {weather['temperature']} °C")
    print(f"Feels Like: {weather['feels_like']} °C")
    print(f"Weather: {weather['description']}")
    print(f"Humidity: {weather['humidity']}%")
    print(f"Wind Speed: {weather['wind_speed']} km/h")
    print()


# =============================================================================
# STEP 3: BUILD THE EMAIL TEXT
# =============================================================================

def build_email_body(weather):
    """Creates the plain-text body of the email from the weather data."""
    body = f"""Hello,

Here is your current weather update for {LOCATION_NAME}.

================================
       PARIS WEATHER UPDATE
================================

Location: {LOCATION_NAME}
Updated At: {weather['time']} ({TIMEZONE})

Temperature: {weather['temperature']} °C
Feels Like: {weather['feels_like']} °C
Weather: {weather['description']}
Humidity: {weather['humidity']}%
Wind Speed: {weather['wind_speed']} km/h

================================

This weather update was automatically generated using Python.

Have a great day!
"""
    return body


# =============================================================================
# STEP 4: SEND THE EMAIL THROUGH GMAIL
# =============================================================================

def send_email(body):
    """
    Sends the email using Gmail SMTP with STARTTLS encryption.
    Returns True if the email was sent, otherwise False.
    """

    # Create the email container and fill in the header fields
    message = MIMEMultipart()
    message["From"] = SENDER_EMAIL
    message["To"] = RECEIVER_EMAIL
    message["Subject"] = EMAIL_SUBJECT

    # Attach the weather text. "utf-8" makes sure the ° symbol displays correctly.
    message.attach(MIMEText(body, "plain", "utf-8"))

    try:
        # Connect to Gmail's server (timeout=30 seconds)
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=30) as server:
            server.starttls()                            # switch to an encrypted connection
            server.login(SENDER_EMAIL, SENDER_PASSWORD)  # log in to Gmail
            server.send_message(message)                 # send the email

        print("Email sent successfully!")
        return True

    except smtplib.SMTPAuthenticationError:
        print("Email authentication failed.")
        print("  -> Check SENDER_EMAIL and SENDER_PASSWORD.")
        print("  -> Gmail usually requires a Google App Password, not your normal password.")
    except smtplib.SMTPConnectError:
        print("SMTP connection error: could not connect to the Gmail server.")
    except smtplib.SMTPServerDisconnected:
        print("SMTP connection error: the Gmail server closed the connection unexpectedly.")
    except smtplib.SMTPRecipientsRefused:
        print("Email error: the receiver address was refused. Check RECEIVER_EMAIL.")
    except smtplib.SMTPException as error:
        print(f"SMTP error: {error}")
    except OSError as error:
        # Covers network problems such as no internet / DNS failure / timeout
        print(f"SMTP connection error (network problem): {error}")
    except Exception as error:
        print(f"Unexpected error while sending email: {error}")

    return False


# =============================================================================
# MAIN PROGRAM: runs the steps in order
# =============================================================================

def main():
    # Step 1: get the weather
    weather = get_weather()
    if weather is None:
        print("Stopping: no weather data, so no email was sent.")
        return

    # Step 2: show it in the console
    print_weather(weather)

    # Step 3: build the email text
    body = build_email_body(weather)

    # Step 4: send it
    send_email(body)


# Run the program
main()