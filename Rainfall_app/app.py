from flask import Flask, render_template, request, url_for
import requests
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)

API_KEY = "391afc0642b04b79b00183702252603"

# Emoji-based icons for simple weather representation
weather_icons = {
    'Sunny': '☀️',
    'Clear': '🌕',
    'Partly cloudy': '⛅',
    'Cloudy': '☁️',
    'Overcast': '☁️',
    'Mist': '🌫️',
    'Patchy rain possible': '🌦️',
    'Light rain': '🌧️',
    'Moderate rain': '🌧️',
    'Heavy rain': '🌧️',
    'Thunderstorm': '⛈️'
}

def get_weather_data(location):
    url = f"https://api.weatherapi.com/v1/forecast.json?key={API_KEY}&q={location}&days=1"
    response = requests.get(url).json()

    try:
        forecast = response['forecast']['forecastday'][0]['day']['totalprecip_mm']
        current = response['current']
        location_data = response['location']

        condition = current['condition']['text']
        icon = weather_icons.get(condition, '❓')

        return {
            'location': location,
            'rainfall': forecast,
            'temperature': current['temp_c'],
            'humidity': current['humidity'],
            'wind_speed': current['wind_kph'],
            'condition': condition,
            'lat': location_data['lat'],
            'lon': location_data['lon'],
            'icon': icon
        }
    except KeyError:
        return None

def generate_runoff_plot(locations_data):
    area = 100  # hectares
    C = 0.8     # runoff coefficient

    cities = [d['location'] for d in locations_data]
    rainfall = [d['rainfall'] for d in locations_data]
    runoff = [C * r * area for r in rainfall]

    plt.figure(figsize=(10, 5))
    bars = plt.bar(cities, runoff, color='teal', alpha=0.8, width=0.4)

    plt.title("Runoff Analysis (Relative)")
    plt.ylabel("Runoff (mm * hectare)")
    plt.xlabel("City")
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.xticks(rotation=30, ha='right')
    plt.tight_layout()

    for bar in bars:
        height = bar.get_height()
        plt.annotate(f'{height:.1f}',
                     xy=(bar.get_x() + bar.get_width() / 2, height),
                     xytext=(0, 5),
                     textcoords='offset points',
                     ha='center', va='bottom',
                     fontsize=9)

    img = io.BytesIO()
    plt.savefig(img, format='png')
    plt.close()
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()

    return plot_url

def get_rainfall(location):
    url = f"https://api.weatherapi.com/v1/forecast.json?key={API_KEY}&q={location}&days=1"
    response = requests.get(url).json()

    try:
        rainfall = response['forecast']['forecastday'][0]['day']['totalprecip_mm']
        return rainfall
    except KeyError:
        return None

@app.route('/', methods=['GET', 'POST'])
def index():
    results = []
    error = None
    map_points = []
    runoff_plot = None

    if request.method == 'POST':
        area_input = request.form.get('areas')
        lang = request.form.get('language', 'en')

        if not area_input:
            error = "Please enter one or more locations separated by commas."
        else:
            locations = [a.strip() for a in area_input.split(',') if a.strip()]

            for loc in locations:
                data = get_weather_data(loc)
                if data:
                    results.append(data)
                    map_points.append({
                        'lat': data['lat'],
                        'lon': data['lon'],
                        'location': data['location'],
                        'rainfall': data['rainfall'],
                        'condition': data['condition'],
                        'icon': data['icon']
                    })
                else:
                    results.append({'location': loc, 'error': True})

            valid_data = [d for d in results if not d.get('error')]
            if valid_data:
                runoff_plot = generate_runoff_plot(valid_data)

    return render_template('index.html', results=results, error=error,
                           map_points=map_points, runoff_plot=runoff_plot)

@app.route('/about', methods=['GET', 'POST'])
def about():
    res = ''
    if request.method == 'POST':
        area = request.form['area']
        lang = request.form['language']
        rainfall = get_rainfall(area)

        if rainfall is None:
            messages = {
                'en': f"No data for {area}.",
                'kn': f"{area} ಗೆ ಡೇಟಾ ಇಲ್ಲ.",
                'hi': f"{area} के लिए डेटा नहीं मिला।"
            }
        else:
            messages = {
                'en': f"The total rainfall in {area} today is {rainfall} mm.",
                'kn': f"{area} ನಲ್ಲಿ ಇವತ್ತು ಒಟ್ಟು ಮಳೆ {rainfall} ಮಿಮೀ ಆಗಿದೆ.",
                'hi': f"{area} में आज कुल वर्षा {rainfall} मिमी है।"
            }

        res = messages.get(lang, messages['en'])

    return render_template('about.html', res=res)

@app.route('/us')
def us():
    return render_template('us.html')

if __name__ == '__main__':
    app.run(debug=True)
