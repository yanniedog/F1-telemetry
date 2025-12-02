# F1 Dataset - API Examples and Usage Guide

This document provides working code examples for accessing F1 data from various sources.

## Table of Contents

1. [Ergast API](#ergast-api)
2. [OpenF1 API](#openf1-api)
3. [FastF1 Library](#fastf1-library)
4. [StatsF1 Scraping](#statsf1-scraping)
5. [FIA PDFs](#fia-pdfs)
6. [F1.com](#f1com)

## Ergast API

### Base URL
```
http://ergast.com/api/f1
```

### Example: Fetch All Seasons

```python
import requests

url = "http://ergast.com/api/f1/seasons.json"
response = requests.get(url)
data = response.json()

seasons = data['MRData']['SeasonTable']['Seasons']
for season in seasons:
    print(f"Year: {season['season']}")
```

### Example: Fetch Races for a Season

```python
import requests

year = 2023
url = f"http://ergast.com/api/f1/{year}/races.json"
response = requests.get(url)
data = response.json()

races = data['MRData']['RaceTable']['Races']
for race in races:
    print(f"Round {race['round']}: {race['raceName']} at {race['Circuit']['circuitName']}")
```

### Example: Fetch Race Results

```python
import requests

year = 2023
round_num = 1
url = f"http://ergast.com/api/f1/{year}/{round_num}/results.json"
response = requests.get(url)
data = response.json()

race = data['MRData']['RaceTable']['Races'][0]
results = race['Results']

for result in results:
    driver = result['Driver']
    print(f"P{result['position']}: {driver['givenName']} {driver['familyName']} - {result['points']} points")
```

### Example: Fetch Lap Times

```python
import requests

year = 2023
round_num = 1
url = f"http://ergast.com/api/f1/{year}/{round_num}/laps.json?limit=1000"
response = requests.get(url)
data = response.json()

race = data['MRData']['RaceTable']['Races'][0]
laps = race['Laps']

for lap_data in laps:
    lap_num = lap_data['number']
    for timing in lap_data['Timings']:
        driver = timing['driverId']
        time = timing['time']
        print(f"Lap {lap_num}, Driver {driver}: {time}")
```

### Example: Fetch Pit Stops

```python
import requests

year = 2023
round_num = 1
url = f"http://ergast.com/api/f1/{year}/{round_num}/pitstops.json"
response = requests.get(url)
data = response.json()

race = data['MRData']['RaceTable']['Races'][0]
pit_stops = race['PitStops']

for pit_stop in pit_stops:
    driver = pit_stop['driverId']
    lap = pit_stop['lap']
    duration = pit_stop['duration']
    print(f"Driver {driver}: Pit stop on lap {lap}, duration {duration}s")
```

### Rate Limiting
- Ergast API: ~200 requests per minute
- Use caching to avoid redundant requests
- Implement retry logic for failed requests

## OpenF1 API

### Base URL
```
https://api.openf1.org/v1
```

### Example: Fetch Sessions

```python
import requests

url = "https://api.openf1.org/v1/sessions"
params = {
    'year': 2023,
    'session_name': 'Race'
}
response = requests.get(url, params=params)
sessions = response.json()

for session in sessions:
    print(f"Session {session['session_key']}: {session['session_name']} at {session['location']}")
```

### Example: Fetch Telemetry Data

```python
import requests

session_key = 9161  # Example session key
driver_number = 63  # Example driver number

url = "https://api.openf1.org/v1/car_data"
params = {
    'session_key': session_key,
    'driver_number': driver_number
}
response = requests.get(url, params=params)
telemetry = response.json()

for data_point in telemetry[:10]:  # First 10 points
    print(f"Time: {data_point['date']}, Speed: {data_point.get('speed', 'N/A')} km/h, "
          f"Throttle: {data_point.get('throttle', 'N/A')}, Brake: {data_point.get('brake', 'N/A')}")
```

### Example: Fetch GPS Position Data

```python
import requests

session_key = 9161
driver_number = 63

url = "https://api.openf1.org/v1/position"
params = {
    'session_key': session_key,
    'driver_number': driver_number
}
response = requests.get(url, params=params)
positions = response.json()

for pos in positions[:10]:
    print(f"Time: {pos['date']}, X: {pos['x']}, Y: {pos['y']}")
```

### Example: Fetch Track Status

```python
import requests

session_key = 9161

url = "https://api.openf1.org/v1/track_status"
params = {'session_key': session_key}
response = requests.get(url, params=params)
status_changes = response.json()

for status in status_changes:
    print(f"Time: {status['date']}, Status: {status['status']}, Message: {status.get('message', 'N/A')}")
```

### Example: Fetch Laps

```python
import requests

session_key = 9161
driver_number = 63

url = "https://api.openf1.org/v1/laps"
params = {
    'session_key': session_key,
    'driver_number': driver_number
}
response = requests.get(url, params=params)
laps = response.json()

for lap in laps:
    print(f"Lap {lap['lap_number']}: {lap.get('lap_duration', 'N/A')}s, "
          f"Position: {lap.get('driver_position', 'N/A')}")
```

### Rate Limiting
- OpenF1 API: ~100 requests per minute
- No authentication required for historical data
- Real-time data may require authentication

## FastF1 Library

### Installation
```bash
pip install fastf1
```

### Example: Load Session

```python
import fastf1

# Enable cache
fastf1.Cache.enable_cache('cache/fastf1')

# Load session
session = fastf1.get_session(2023, 'Monza', 'R')  # Race session
session.load()

print(f"Session: {session.session_info['Name']}")
print(f"Date: {session.date}")
```

### Example: Fetch Laps

```python
import fastf1

session = fastf1.get_session(2023, 'Monza', 'R')
session.load()

laps = session.laps
print(f"Total laps: {len(laps)}")

# Get fastest lap
fastest_lap = laps.pick_fastest()
print(f"Fastest lap: {fastest_lap['LapTime']} by {fastest_lap['Driver']}")

# Get laps for specific driver
hamilton_laps = laps.pick_driver('HAM')
print(f"Hamilton completed {len(hamilton_laps)} laps")
```

### Example: Fetch Sector Times

```python
import fastf1

session = fastf1.get_session(2023, 'Monza', 'Q')  # Qualifying
session.load()

laps = session.laps

# Get sector times for fastest lap
fastest_lap = laps.pick_fastest()
print(f"Sector 1: {fastest_lap['Sector1Time']}")
print(f"Sector 2: {fastest_lap['Sector2Time']}")
print(f"Sector 3: {fastest_lap['Sector3Time']}")
```

### Example: Fetch Telemetry

```python
import fastf1

session = fastf1.get_session(2023, 'Monza', 'R')
session.load()

# Get telemetry for fastest lap
fastest_lap = session.laps.pick_fastest()
telemetry = fastest_lap.get_car_data()

print(f"Speed: {telemetry['Speed'].max()} km/h")
print(f"Throttle: {telemetry['Throttle'].max()}%")
print(f"Brake: {telemetry['Brake'].sum() > 0}")  # Any braking
```

### Example: Fetch Weather Data

```python
import fastf1

session = fastf1.get_session(2023, 'Monza', 'R')
session.load()

weather = session.weather_data
if weather is not None and len(weather) > 0:
    print(f"Air temperature: {weather['AirTemp'].mean():.1f}°C")
    print(f"Track temperature: {weather['TrackTemp'].mean():.1f}°C")
    print(f"Humidity: {weather['Humidity'].mean():.1f}%")
```

### Example: Fetch Tyre Compounds

```python
import fastf1

session = fastf1.get_session(2023, 'Monza', 'R')
session.load()

laps = session.laps

# Get tyre compound usage
tyre_data = laps[['Driver', 'LapNumber', 'Compound', 'Stint']].dropna()
print(tyre_data.groupby(['Driver', 'Compound']).size())
```

### Caching
- FastF1 caches session data locally
- First load downloads data, subsequent loads use cache
- Cache directory: `~/.fastf1/cache` by default

## StatsF1 Scraping

### Example: Scrape Safety Car Periods

```python
import requests
from bs4 import BeautifulSoup

url = "https://www.statsf1.com/en/statistiques/pilote/voiture-securite.aspx"
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, 'html.parser')

# Parse table (structure may vary)
table = soup.find('table')
if table:
    rows = table.find_all('tr')[1:]  # Skip header
    for row in rows:
        cols = row.find_all('td')
        if len(cols) >= 4:
            year = cols[0].text.strip()
            race = cols[1].text.strip()
            lap = cols[2].text.strip()
            duration = cols[3].text.strip()
            print(f"{year} {race}: SC on lap {lap}, duration {duration}")
```

### Rate Limiting
- Be respectful: ~30 requests per minute
- Use caching to avoid redundant requests
- Respect robots.txt

## FIA PDFs

### Example: Download and Parse PDF

```python
import requests
import pdfplumber

# Find PDF URL (varies by year/round)
pdf_url = "https://www.fia.com/sites/default/files/race_classification_2023_01.pdf"

# Download PDF
response = requests.get(pdf_url, stream=True)
with open('race_classification.pdf', 'wb') as f:
    for chunk in response.iter_content(chunk_size=8192):
        f.write(chunk)

# Parse PDF
with pdfplumber.open('race_classification.pdf') as pdf:
    for page in pdf.pages:
        text = page.extract_text()
        print(text)
        
        # Extract tables
        tables = page.extract_tables()
        for table in tables:
            # Process table data
            for row in table:
                print(row)
```

## F1.com

### Example: Scrape Race Results

```python
import requests
from bs4 import BeautifulSoup

url = "https://www.formula1.com/en/results.html/2023/races/1124/monaco/race-result.html"
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, 'html.parser')

# Find results table
table = soup.find('table', class_='resultsarchive-table')
if table:
    rows = table.find_all('tr')[1:]  # Skip header
    for row in rows:
        cols = row.find_all('td')
        if len(cols) >= 5:
            position = cols[0].text.strip()
            driver = cols[1].text.strip()
            constructor = cols[2].text.strip()
            time = cols[3].text.strip()
            points = cols[4].text.strip()
            print(f"P{position}: {driver} ({constructor}) - {time} - {points} points")
```

## Best Practices

1. **Always use caching** to avoid redundant API calls
2. **Implement rate limiting** to respect API limits
3. **Handle errors gracefully** with retry logic
4. **Cache responses locally** for offline processing
5. **Use appropriate timeouts** for network requests
6. **Respect robots.txt** for web scraping
7. **Be respectful** with request frequency

## Error Handling

```python
import requests
from time import sleep

def fetch_with_retry(url, max_retries=3, delay=1):
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                sleep(delay * (2 ** attempt))  # Exponential backoff
            else:
                raise
```

