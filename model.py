import numpy as np
import random
from enum import Enum

class TimeOfDay(Enum):
    DAY = "day"
    NIGHT = "night"
    TWILIGHT = "twilight"

class Weather(Enum):
    CLEAR = "clear"
    CLOUDY = "cloudy"
    RAIN = "rain"
    FOG = "fog"
    SNOW = "snow"

class TrafficMode(Enum):
    UNIFORM = "uniform"
    SPARSE = "sparse"
    JAM = "jam"

class StreetLight:
    def __init__(self, position, power, l_min, l_max, zone_radius):
        self.position = position
        self.power = power
        self.l_min = l_min
        self.l_max = l_max
        self.zone_radius = zone_radius
        self.current_brightness = l_min
        self.is_active = True

    def compute_illumination(self, distance, cars_count, ambient_light, alpha, beta, gamma, delta, n_max, time_of_day, weather):
        # Днём фонари выключены, если нет плохой погоды
        if time_of_day == TimeOfDay.DAY and weather not in [Weather.RAIN, Weather.FOG, Weather.SNOW]:
            self.is_active = False
            self.current_brightness = 0
            return 0
            
        self.is_active = True
        weather_factor = self._get_weather_factor(weather)
        f = (alpha * np.exp(-beta * distance) + 
             gamma * (cars_count / n_max) + 
             delta * (1 - ambient_light * weather_factor))
        self.current_brightness = np.clip(self.l_min + (self.l_max - self.l_min) * f, 0, 1)
        return self.current_brightness

    def _get_weather_factor(self, weather):
        factors = {
            Weather.CLEAR: 1.0,
            Weather.CLOUDY: 0.7,
            Weather.RAIN: 0.5,
            Weather.FOG: 0.3,
            Weather.SNOW: 0.4
        }
        return factors.get(weather, 1.0)

class TrafficSimulator:
    def __init__(self, road_length, num_lights):
        self.road_length = road_length
        self.lights = [StreetLight(i * (road_length / num_lights), 100, 0.1, 1.0, 50) 
                      for i in range(num_lights)]
        self.cars = []
        self.time = 0
        self.weather = Weather.CLEAR
        self.time_of_day = TimeOfDay.NIGHT
        self.energy_smart_kwh = 0
        self.energy_traditional_kwh = 0
        self.brightness_history = []
        self.energy_history = []
        self.traffic_mode = TrafficMode.UNIFORM
        self.traffic_density = 0.5
        self.traffic_speed = 50

    def set_conditions(self, time_of_day, weather):
        self.time_of_day = time_of_day
        self.weather = weather

    def add_car(self, position, speed):
        self.cars.append({"position": position, "speed": speed})

    def generate_traffic(self):
        self.cars.clear()
        
        if self.traffic_mode == TrafficMode.JAM:
            car_count = int(self.road_length * self.traffic_density / 10)
            for x in np.linspace(0, self.road_length, car_count):
                self.add_car(x, max(5, self.traffic_speed * 0.1))
                
        elif self.traffic_mode == TrafficMode.UNIFORM:
            car_count = int(self.road_length * self.traffic_density / 50)
            for x in np.linspace(0, self.road_length, car_count):
                self.add_car(x, self.traffic_speed)
                
        elif self.traffic_mode == TrafficMode.SPARSE:
            car_count = int(self.road_length * self.traffic_density / 100)
            positions = random.sample(range(int(self.road_length)), car_count)
            for x in positions:
                self.add_car(x, self.traffic_speed * random.uniform(0.8, 1.2))

    def update(self, delta_t, alpha, beta, gamma, delta, n_max):
        for car in self.cars:
            car["position"] += car["speed"] * delta_t / 3600
            if car["position"] > self.road_length:
                car["position"] = 0

        smart_energy = 0
        brightness_levels = []
        ambient_light = self._get_ambient_light()
        
        for light in self.lights:
            distances = [abs(car["position"] - light.position) for car in self.cars]
            d_j = min(distances) if distances else light.zone_radius
            N_j = sum(1 for car in self.cars 
                     if abs(car["position"] - light.position) <= light.zone_radius)
            L_j = light.compute_illumination(d_j, N_j, ambient_light, 
                                           alpha, beta, gamma, delta, n_max, 
                                           self.time_of_day, self.weather)
            smart_energy += light.power * L_j * delta_t if light.is_active else 0
            brightness_levels.append(L_j)

        # Расчёт в кВт·ч
        self.energy_smart_kwh += smart_energy / (1000 * 3600)
        traditional_energy = sum(light.power * delta_t for light in self.lights 
                               if self._should_light_be_on(light)) / (1000 * 3600)
        self.energy_traditional_kwh += traditional_energy
        
        self.brightness_history.append(np.mean(brightness_levels))
        self.energy_history.append((self.energy_smart_kwh, self.energy_traditional_kwh))
        self.time += delta_t

    def _should_light_be_on(self, light):
        """Определяет, должен ли фонарь быть включён в традиционном режиме"""
        if self.time_of_day == TimeOfDay.DAY:
            return self.weather in [Weather.RAIN, Weather.FOG, Weather.SNOW]
        return True

    def _get_ambient_light(self):
        """Возвращает уровень естественного освещения с учётом погоды (0-1)"""
        base_light = {
            TimeOfDay.DAY: 0.9,
            TimeOfDay.TWILIGHT: 0.4,
            TimeOfDay.NIGHT: 0.1
        }.get(self.time_of_day, 0.1)
        
        weather_factor = {
            Weather.CLEAR: 1.0,
            Weather.CLOUDY: 0.8,
            Weather.RAIN: 0.6,
            Weather.FOG: 0.4,
            Weather.SNOW: 0.5
        }.get(self.weather, 1.0)
        
        return base_light * weather_factor