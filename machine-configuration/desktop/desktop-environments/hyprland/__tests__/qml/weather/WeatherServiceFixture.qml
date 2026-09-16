import QtQuick
import "../../../../quickshell/bar/program-configuration/dashboard/services/weather/WeatherCodes.js" as WeatherCodes

Item {
    id: root

    property QtObject weatherServiceLogic: QtObject {
        id: weatherServiceLogic

        property string locationCoordinates: ""

        readonly property var weatherIconMap: WeatherCodes.weatherIconMap

        readonly property var weatherConditionMap: WeatherCodes.weatherConditionMap

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
            var queryParams = ["latitude=" + latitude, "longitude=" + longitude, "daily=weather_code,temperature_2m_max,temperature_2m_min,sunrise,sunset", "current=temperature_2m,relative_humidity_2m,apparent_temperature,is_day,weather_code,wind_speed_10m", "timezone=auto", "forecast_days=7"];

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
}
