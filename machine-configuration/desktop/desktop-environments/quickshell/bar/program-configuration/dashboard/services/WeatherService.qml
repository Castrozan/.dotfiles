pragma Singleton

import ".."
import "weather/WeatherCodes.js" as WeatherCodes
import Quickshell
import Quickshell.Io
import QtQuick

Singleton {
    id: weatherServiceRoot

    property string city
    property string locationCoordinates
    property var currentConditions
    property list<var> forecast

    readonly property string icon: currentConditions ? getWeatherIcon(currentConditions.weatherCode) : "cloud_alert"
    readonly property string description: currentConditions?.weatherDesc ?? "No weather"
    readonly property string temperature: DashboardConfig.useFahrenheit ? `${currentConditions?.tempF ?? 0}°F` : `${currentConditions?.tempC ?? 0}°C`
    readonly property string feelsLikeTemperature: DashboardConfig.useFahrenheit ? `${currentConditions?.feelsLikeF ?? 0}°F` : `${currentConditions?.feelsLikeC ?? 0}°C`
    readonly property int humidity: currentConditions?.humidity ?? 0
    readonly property real windSpeed: currentConditions?.windSpeed ?? 0
    readonly property string sunrise: currentConditions ? Qt.formatDateTime(new Date(currentConditions.sunrise), DashboardConfig.useTwelveHourClock ? "h:mm A" : "h:mm") : "--:--"
    readonly property string sunset: currentConditions ? Qt.formatDateTime(new Date(currentConditions.sunset), DashboardConfig.useTwelveHourClock ? "h:mm A" : "h:mm") : "--:--"

    readonly property var weatherIconMap: WeatherCodes.weatherIconMap

    readonly property var weatherConditionMap: WeatherCodes.weatherConditionMap

    function reload(): void {
        fetchLocationProcess.running = true;
    }

    function getWeatherIcon(code): string {
        if (weatherIconMap.hasOwnProperty(code))
            return weatherIconMap[code];
        return "air";
    }

    function getWeatherCondition(code): string {
        return weatherConditionMap[code] || "Unknown";
    }

    function celsiusToFahrenheit(celsius: real): real {
        return celsius * 9 / 5 + 32;
    }

    function buildWeatherApiUrl(): string {
        if (!locationCoordinates || locationCoordinates.indexOf(",") === -1)
            return "";

        const [latitude, longitude] = locationCoordinates.split(",");
        const baseUrl = "https://api.open-meteo.com/v1/forecast";
        const queryParams = ["latitude=" + latitude, "longitude=" + longitude, "daily=weather_code,temperature_2m_max,temperature_2m_min,sunrise,sunset", "current=temperature_2m,relative_humidity_2m,apparent_temperature,is_day,weather_code,wind_speed_10m", "timezone=auto", "forecast_days=7"];

        return baseUrl + "?" + queryParams.join("&");
    }

    function parseWeatherResponse(responseText: string): void {
        const json = JSON.parse(responseText);
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

        const forecastList = [];
        for (let i = 0; i < json.daily.time.length; i++)
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

    onLocationCoordinatesChanged: {
        if (locationCoordinates)
            fetchWeatherDelayTimer.restart();
    }

    Component.onCompleted: fetchLocationProcess.running = true

    Timer {
        id: fetchWeatherDelayTimer
        interval: 100
        onTriggered: fetchWeatherProcess.running = true
    }

    Process {
        id: fetchLocationProcess

        command: ["curl", "-sf", "https://ipinfo.io/json"]
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                try {
                    const response = JSON.parse(data);
                    if (response.loc) {
                        weatherServiceRoot.locationCoordinates = response.loc;
                        weatherServiceRoot.city = response.city ?? "";
                    }
                } catch (e) {}
            }
        }
    }

    Process {
        id: fetchWeatherProcess

        command: {
            const url = weatherServiceRoot.buildWeatherApiUrl();
            return url ? ["curl", "-sf", url] : ["echo"];
        }
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                try {
                    weatherServiceRoot.parseWeatherResponse(data);
                } catch (e) {}
            }
        }
    }

    Timer {
        interval: 3600000
        running: true
        repeat: true
        onTriggered: {
            fetchLocationProcess.running = true;
            fetchWeatherProcess.running = true;
        }
    }
}
