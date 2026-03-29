import QtQuick
import QtTest

Item {
    id: root

    QtObject {
        id: weatherServiceLogic

        property string locationCoordinates: ""

        readonly property var weatherIconMap: ({
            "0": "clear_day",
            "1": "clear_day",
            "2": "partly_cloudy_day",
            "3": "cloud",
            "45": "foggy",
            "48": "foggy",
            "51": "rainy",
            "53": "rainy",
            "55": "rainy",
            "56": "rainy",
            "57": "rainy",
            "61": "rainy",
            "63": "rainy",
            "65": "rainy",
            "66": "rainy",
            "67": "rainy",
            "71": "cloudy_snowing",
            "73": "cloudy_snowing",
            "75": "snowing_heavy",
            "77": "cloudy_snowing",
            "80": "rainy",
            "81": "rainy",
            "82": "rainy",
            "85": "cloudy_snowing",
            "86": "snowing_heavy",
            "95": "thunderstorm",
            "96": "thunderstorm",
            "99": "thunderstorm"
        })

        readonly property var weatherConditionMap: ({
            "0": "Clear",
            "1": "Clear",
            "2": "Partly cloudy",
            "3": "Overcast",
            "45": "Fog",
            "48": "Fog",
            "51": "Drizzle",
            "53": "Drizzle",
            "55": "Drizzle",
            "56": "Freezing drizzle",
            "57": "Freezing drizzle",
            "61": "Light rain",
            "63": "Rain",
            "65": "Heavy rain",
            "66": "Light rain",
            "67": "Heavy rain",
            "71": "Light snow",
            "73": "Snow",
            "75": "Heavy snow",
            "77": "Snow",
            "80": "Light rain",
            "81": "Rain",
            "82": "Heavy rain",
            "85": "Light snow showers",
            "86": "Heavy snow showers",
            "95": "Thunderstorm",
            "96": "Thunderstorm with hail",
            "99": "Thunderstorm with hail"
        })

        function getWeatherIcon(code) {
            if (weatherIconMap.hasOwnProperty(code))
                return weatherIconMap[code];
            return "air";
        }

        function getWeatherCondition(code) {
            return weatherConditionMap[code] || "Unknown";
        }

        function celsiusToFahrenheit(celsius) {
            return celsius * 9 / 5 + 32;
        }

        function buildWeatherApiUrl() {
            if (!locationCoordinates || locationCoordinates.indexOf(",") === -1)
                return "";

            var parts = locationCoordinates.split(",");
            var latitude = parts[0];
            var longitude = parts[1];
            var baseUrl = "https://api.open-meteo.com/v1/forecast";
            var queryParams = [
                "latitude=" + latitude,
                "longitude=" + longitude,
                "daily=weather_code,temperature_2m_max,temperature_2m_min,sunrise,sunset",
                "current=temperature_2m,relative_humidity_2m,apparent_temperature,is_day,weather_code,wind_speed_10m",
                "timezone=auto",
                "forecast_days=7"
            ];

            return baseUrl + "?" + queryParams.join("&");
        }

        property var currentConditions: null
        property var forecast: []

        function parseWeatherResponse(responseText) {
            var json = JSON.parse(responseText);
            if (!json.current || !json.daily)
                return;

            currentConditions = {
                weatherCode: json.current.weather_code,
                weatherDesc: getWeatherCondition(json.current.weather_code),
                tempC: Math.round(json.current.temperature_2m),
                tempF: Math.round(celsiusToFahrenheit(json.current.temperature_2m)),
                feelsLikeC: Math.round(json.current.apparent_temperature),
                feelsLikeF: Math.round(celsiusToFahrenheit(json.current.apparent_temperature)),
                humidity: json.current.relative_humidity_2m,
                windSpeed: json.current.wind_speed_10m,
                isDay: json.current.is_day,
                sunrise: json.daily.sunrise[0],
                sunset: json.daily.sunset[0]
            };

            var forecastList = [];
            for (var i = 0; i < json.daily.time.length; i++)
                forecastList.push({
                    date: json.daily.time[i],
                    maxTempC: Math.round(json.daily.temperature_2m_max[i]),
                    maxTempF: Math.round(celsiusToFahrenheit(json.daily.temperature_2m_max[i])),
                    minTempC: Math.round(json.daily.temperature_2m_min[i]),
                    minTempF: Math.round(celsiusToFahrenheit(json.daily.temperature_2m_min[i])),
                    weatherCode: json.daily.weather_code[i],
                    icon: getWeatherIcon(json.daily.weather_code[i])
                });
            forecast = forecastList;
        }
    }

    TestCase {
        name: "WeatherServiceGetWeatherIcon"

        function test_clear_sky_returns_clear_day() {
            compare(weatherServiceLogic.getWeatherIcon("0"), "clear_day");
        }

        function test_mainly_clear_returns_clear_day() {
            compare(weatherServiceLogic.getWeatherIcon("1"), "clear_day");
        }

        function test_partly_cloudy() {
            compare(weatherServiceLogic.getWeatherIcon("2"), "partly_cloudy_day");
        }

        function test_overcast() {
            compare(weatherServiceLogic.getWeatherIcon("3"), "cloud");
        }

        function test_fog() {
            compare(weatherServiceLogic.getWeatherIcon("45"), "foggy");
        }

        function test_rime_fog() {
            compare(weatherServiceLogic.getWeatherIcon("48"), "foggy");
        }

        function test_rain_codes() {
            var rainCodes = ["51", "53", "55", "56", "57", "61", "63", "65", "66", "67", "80", "81", "82"];
            for (var i = 0; i < rainCodes.length; i++)
                compare(weatherServiceLogic.getWeatherIcon(rainCodes[i]), "rainy");
        }

        function test_snow_codes() {
            compare(weatherServiceLogic.getWeatherIcon("71"), "cloudy_snowing");
            compare(weatherServiceLogic.getWeatherIcon("73"), "cloudy_snowing");
            compare(weatherServiceLogic.getWeatherIcon("77"), "cloudy_snowing");
            compare(weatherServiceLogic.getWeatherIcon("85"), "cloudy_snowing");
        }

        function test_heavy_snow_codes() {
            compare(weatherServiceLogic.getWeatherIcon("75"), "snowing_heavy");
            compare(weatherServiceLogic.getWeatherIcon("86"), "snowing_heavy");
        }

        function test_thunderstorm_codes() {
            compare(weatherServiceLogic.getWeatherIcon("95"), "thunderstorm");
            compare(weatherServiceLogic.getWeatherIcon("96"), "thunderstorm");
            compare(weatherServiceLogic.getWeatherIcon("99"), "thunderstorm");
        }

        function test_unknown_code_returns_air() {
            compare(weatherServiceLogic.getWeatherIcon("999"), "air");
        }

        function test_empty_string_code_returns_air() {
            compare(weatherServiceLogic.getWeatherIcon(""), "air");
        }

        function test_numeric_zero_as_string() {
            compare(weatherServiceLogic.getWeatherIcon(0), "clear_day");
        }
    }

    TestCase {
        name: "WeatherServiceGetWeatherCondition"

        function test_clear() {
            compare(weatherServiceLogic.getWeatherCondition("0"), "Clear");
        }

        function test_overcast() {
            compare(weatherServiceLogic.getWeatherCondition("3"), "Overcast");
        }

        function test_fog() {
            compare(weatherServiceLogic.getWeatherCondition("45"), "Fog");
        }

        function test_drizzle() {
            compare(weatherServiceLogic.getWeatherCondition("51"), "Drizzle");
        }

        function test_freezing_drizzle() {
            compare(weatherServiceLogic.getWeatherCondition("56"), "Freezing drizzle");
        }

        function test_heavy_rain() {
            compare(weatherServiceLogic.getWeatherCondition("65"), "Heavy rain");
        }

        function test_heavy_snow() {
            compare(weatherServiceLogic.getWeatherCondition("75"), "Heavy snow");
        }

        function test_thunderstorm_with_hail() {
            compare(weatherServiceLogic.getWeatherCondition("99"), "Thunderstorm with hail");
        }

        function test_unknown_code_returns_unknown() {
            compare(weatherServiceLogic.getWeatherCondition("999"), "Unknown");
        }

        function test_empty_code_returns_unknown() {
            compare(weatherServiceLogic.getWeatherCondition(""), "Unknown");
        }
    }

    TestCase {
        name: "WeatherServiceCelsiusToFahrenheit"

        function test_freezing_point() {
            fuzzyCompare(weatherServiceLogic.celsiusToFahrenheit(0), 32.0, 0.01);
        }

        function test_boiling_point() {
            fuzzyCompare(weatherServiceLogic.celsiusToFahrenheit(100), 212.0, 0.01);
        }

        function test_body_temperature() {
            fuzzyCompare(weatherServiceLogic.celsiusToFahrenheit(37), 98.6, 0.01);
        }

        function test_negative_temperature() {
            fuzzyCompare(weatherServiceLogic.celsiusToFahrenheit(-40), -40.0, 0.01);
        }

        function test_room_temperature() {
            fuzzyCompare(weatherServiceLogic.celsiusToFahrenheit(20), 68.0, 0.01);
        }

        function test_absolute_zero_celsius() {
            fuzzyCompare(weatherServiceLogic.celsiusToFahrenheit(-273.15), -459.67, 0.01);
        }
    }

    TestCase {
        name: "WeatherServiceBuildWeatherApiUrl"

        function test_builds_url_with_valid_coordinates() {
            weatherServiceLogic.locationCoordinates = "52.52,13.41";
            var url = weatherServiceLogic.buildWeatherApiUrl();
            verify(url.indexOf("https://api.open-meteo.com/v1/forecast?") === 0);
            verify(url.indexOf("latitude=52.52") !== -1);
            verify(url.indexOf("longitude=13.41") !== -1);
            verify(url.indexOf("forecast_days=7") !== -1);
            verify(url.indexOf("timezone=auto") !== -1);
        }

        function test_returns_empty_for_empty_coordinates() {
            weatherServiceLogic.locationCoordinates = "";
            compare(weatherServiceLogic.buildWeatherApiUrl(), "");
        }

        function test_returns_empty_for_no_comma() {
            weatherServiceLogic.locationCoordinates = "52.52";
            compare(weatherServiceLogic.buildWeatherApiUrl(), "");
        }

        function test_handles_negative_coordinates() {
            weatherServiceLogic.locationCoordinates = "-23.55,-46.63";
            var url = weatherServiceLogic.buildWeatherApiUrl();
            verify(url.indexOf("latitude=-23.55") !== -1);
            verify(url.indexOf("longitude=-46.63") !== -1);
        }
    }

    TestCase {
        name: "WeatherServiceParseWeatherResponse"

        readonly property string sampleWeatherResponse: JSON.stringify({
            current: {
                temperature_2m: 22.5,
                relative_humidity_2m: 65,
                apparent_temperature: 20.3,
                is_day: 1,
                weather_code: 2,
                wind_speed_10m: 12.5
            },
            daily: {
                time: ["2026-03-29", "2026-03-30"],
                weather_code: [2, 61],
                temperature_2m_max: [25.0, 18.0],
                temperature_2m_min: [12.0, 10.0],
                sunrise: ["2026-03-29T06:30", "2026-03-30T06:28"],
                sunset: ["2026-03-29T18:45", "2026-03-30T18:46"]
            }
        })

        function test_parses_current_conditions() {
            weatherServiceLogic.currentConditions = null;
            weatherServiceLogic.forecast = [];
            weatherServiceLogic.parseWeatherResponse(sampleWeatherResponse);

            verify(weatherServiceLogic.currentConditions !== null);
            compare(weatherServiceLogic.currentConditions.weatherCode, 2);
            compare(weatherServiceLogic.currentConditions.weatherDesc, "Partly cloudy");
            compare(weatherServiceLogic.currentConditions.tempC, 23);
            compare(weatherServiceLogic.currentConditions.humidity, 65);
            fuzzyCompare(weatherServiceLogic.currentConditions.windSpeed, 12.5, 0.01);
        }

        function test_parses_fahrenheit_temperature() {
            weatherServiceLogic.currentConditions = null;
            weatherServiceLogic.parseWeatherResponse(sampleWeatherResponse);

            compare(weatherServiceLogic.currentConditions.tempF, Math.round(22.5 * 9 / 5 + 32));
        }

        function test_parses_feels_like_temperature() {
            weatherServiceLogic.currentConditions = null;
            weatherServiceLogic.parseWeatherResponse(sampleWeatherResponse);

            compare(weatherServiceLogic.currentConditions.feelsLikeC, Math.round(20.3));
            compare(weatherServiceLogic.currentConditions.feelsLikeF, Math.round(20.3 * 9 / 5 + 32));
        }

        function test_parses_sunrise_sunset() {
            weatherServiceLogic.currentConditions = null;
            weatherServiceLogic.parseWeatherResponse(sampleWeatherResponse);

            compare(weatherServiceLogic.currentConditions.sunrise, "2026-03-29T06:30");
            compare(weatherServiceLogic.currentConditions.sunset, "2026-03-29T18:45");
        }

        function test_parses_forecast_days() {
            weatherServiceLogic.forecast = [];
            weatherServiceLogic.parseWeatherResponse(sampleWeatherResponse);

            compare(weatherServiceLogic.forecast.length, 2);
            compare(weatherServiceLogic.forecast[0].date, "2026-03-29");
            compare(weatherServiceLogic.forecast[0].maxTempC, 25);
            compare(weatherServiceLogic.forecast[0].minTempC, 12);
            compare(weatherServiceLogic.forecast[0].weatherCode, 2);
            compare(weatherServiceLogic.forecast[0].icon, "partly_cloudy_day");
        }

        function test_parses_second_forecast_day() {
            weatherServiceLogic.forecast = [];
            weatherServiceLogic.parseWeatherResponse(sampleWeatherResponse);

            compare(weatherServiceLogic.forecast[1].date, "2026-03-30");
            compare(weatherServiceLogic.forecast[1].weatherCode, 61);
            compare(weatherServiceLogic.forecast[1].icon, "rainy");
        }

        function test_skips_response_without_current() {
            weatherServiceLogic.currentConditions = null;
            weatherServiceLogic.parseWeatherResponse(JSON.stringify({ daily: { time: [] } }));
            compare(weatherServiceLogic.currentConditions, null);
        }

        function test_skips_response_without_daily() {
            weatherServiceLogic.currentConditions = null;
            weatherServiceLogic.parseWeatherResponse(JSON.stringify({ current: { temperature_2m: 20 } }));
            compare(weatherServiceLogic.currentConditions, null);
        }

        function test_forecast_fahrenheit_conversion() {
            weatherServiceLogic.forecast = [];
            weatherServiceLogic.parseWeatherResponse(sampleWeatherResponse);

            compare(weatherServiceLogic.forecast[0].maxTempF, Math.round(25.0 * 9 / 5 + 32));
            compare(weatherServiceLogic.forecast[0].minTempF, Math.round(12.0 * 9 / 5 + 32));
        }
    }
}
