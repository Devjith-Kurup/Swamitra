export interface Location {
  latitude: number;
  longitude: number;
}

export interface CurrentWeather {
  temperature_c: number;
  humidity_percent: number;
  rainfall_mm: number;
  wind_speed_kph: number;
  timestamp: string;
}

export interface DailyForecast {
  date: string;
  max_temperature_c: number;
  min_temperature_c: number;
  rainfall_mm: number;
}

export interface WeatherResponse {
  location: Location;
  current: CurrentWeather;
  forecast: DailyForecast[];
  provider: string;
}
