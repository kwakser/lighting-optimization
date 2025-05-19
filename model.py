import random
import numpy as np

# Константы времени суток
TIME_OF_DAY_DAY = "day"
TIME_OF_DAY_NIGHT = "night"
TIME_OF_DAY_TWILIGHT = "twilight"
TIME_OF_DAY_VALUES = {TIME_OF_DAY_DAY, TIME_OF_DAY_NIGHT, TIME_OF_DAY_TWILIGHT}

# Константы погоды
WEATHER_CLEAR = "clear"
WEATHER_CLOUDY = "cloudy"
WEATHER_RAIN = "rain"
WEATHER_FOG = "fog"
WEATHER_SNOW = "snow"
WEATHER_VALUES = {WEATHER_CLEAR, WEATHER_CLOUDY, WEATHER_RAIN, WEATHER_FOG, WEATHER_SNOW}

# Константы режимов трафика
TRAFFIC_MODE_UNIFORM = "uniform"
TRAFFIC_MODE_SPARSE = "sparse"
TRAFFIC_MODE_JAM = "jam"
TRAFFIC_MODE_VALUES = {TRAFFIC_MODE_UNIFORM, TRAFFIC_MODE_SPARSE, TRAFFIC_MODE_JAM}


class StreetLight:
    def __init__(self, position, power=100, l_min=0.1, l_max=1.0, zone_radius=50):
        self.position = position
        self.power = power
        self.l_min = l_min
        self.l_max = l_max
        self.zone_radius = zone_radius
        self.current_brightness = l_min
        self.is_active = True

    def compute_illumination(self, distance, cars_count, ambient_light,
                             alpha, beta, gamma, delta, n_max,
                             time_of_day_numeric, weather):
        tod_factor = time_of_day_numeric / 2.0  # 0 (ночь) ... 1 (день)

        if tod_factor >= 1.0 and weather not in [WEATHER_RAIN, WEATHER_FOG, WEATHER_SNOW]:
            self.is_active = False
            self.current_brightness = 0
            return 0

        self.is_active = True
        weather_factor = self._get_weather_factor(weather)

        f = (alpha * np.exp(-beta * distance) +
             gamma * (cars_count / n_max) +
             delta * (1 - ambient_light * weather_factor))

        brightness = np.clip(self.l_min + (self.l_max - self.l_min) * f * (1 - tod_factor), 0, 1)
        self.current_brightness = brightness
        return brightness

    def _get_weather_factor(self, weather):
        factors = {
            WEATHER_CLEAR: 1.0,
            WEATHER_CLOUDY: 0.7,
            WEATHER_RAIN: 0.5,
            WEATHER_FOG: 0.3,
            WEATHER_SNOW: 0.4
        }
        return factors.get(weather, 1.0)


class TrafficSimulator:
    def __init__(self, road_length=1000, num_lights=20):
        self.road_length = road_length
        self.lights = [StreetLight(i * (road_length / num_lights)) for i in range(num_lights)]
        self.cars = []
        self.time = 0
        self.weather = WEATHER_CLEAR
        self.time_of_day = TIME_OF_DAY_NIGHT

        self._time_of_day_numeric = self._time_of_day_to_num(self.time_of_day)
        self._target_time_of_day_numeric = self._time_of_day_numeric
        self._time_of_day_transition_duration = 20
        self._time_of_day_transition_elapsed = 0

        self.energy_smart_kwh = 0
        self.energy_traditional_kwh = 0
        self.brightness_history = []
        self.energy_history = []

        self.traffic_mode = TRAFFIC_MODE_UNIFORM
        self.traffic_density = 0.5
        self.traffic_speed = 50

    def _time_of_day_to_num(self, tod_str):
        mapping = {
            TIME_OF_DAY_NIGHT: 0.0,
            TIME_OF_DAY_TWILIGHT: 1.0,
            TIME_OF_DAY_DAY: 2.0
        }
        return mapping.get(tod_str, 0.0)

    def _num_to_time_of_day(self, num):
        if num <= 0.5:
            return TIME_OF_DAY_NIGHT
        elif num <= 1.5:
            return TIME_OF_DAY_TWILIGHT
        else:
            return TIME_OF_DAY_DAY

    def set_conditions(self, time_of_day, weather):
        if time_of_day not in TIME_OF_DAY_VALUES:
            raise ValueError(f"Invalid time_of_day: {time_of_day}")
        if weather not in WEATHER_VALUES:
            raise ValueError(f"Invalid weather: {weather}")
        self.weather = weather
        self._target_time_of_day_numeric = self._time_of_day_to_num(time_of_day)
        self._time_of_day_transition_elapsed = 0

    def add_car(self, position, speed):
        self.cars.append({"position": position, "speed": speed})

    def generate_traffic(self):
        self.cars.clear()
        if self.traffic_mode == TRAFFIC_MODE_JAM:
            car_count = int(self.road_length * self.traffic_density / 10)
            for x in np.linspace(0, self.road_length, car_count):
                self.add_car(x, max(5, self.traffic_speed * 0.1))
        elif self.traffic_mode == TRAFFIC_MODE_UNIFORM:
            car_count = int(self.road_length * self.traffic_density / 50)
            for x in np.linspace(0, self.road_length, car_count):
                self.add_car(x, self.traffic_speed)
        elif self.traffic_mode == TRAFFIC_MODE_SPARSE:
            car_count = int(self.road_length * self.traffic_density / 100)
            positions = random.sample(range(int(self.road_length)), car_count)
            for x in positions:
                self.add_car(x, self.traffic_speed * random.uniform(0.8, 1.2))

    def update(self, delta_t=1, alpha=0.5, beta=0.1, gamma=0.2, delta=0.4, n_max=10):
        if self._time_of_day_numeric != self._target_time_of_day_numeric:
            step = delta_t / self._time_of_day_transition_duration
            diff = self._target_time_of_day_numeric - self._time_of_day_numeric
            if abs(diff) <= step:
                self._time_of_day_numeric = self._target_time_of_day_numeric
            else:
                self._time_of_day_numeric += step if diff > 0 else -step
            self.time_of_day = self._num_to_time_of_day(self._time_of_day_numeric)

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
            N_j = sum(1 for car in self.cars if abs(car["position"] - light.position) <= light.zone_radius)
            L_j = light.compute_illumination(d_j, N_j, ambient_light,
                                             alpha, beta, gamma, delta, n_max,
                                             self._time_of_day_numeric, self.weather)
            smart_energy += light.power * L_j * delta_t if light.is_active else 0
            brightness_levels.append(L_j)

        self.energy_smart_kwh += smart_energy / (1000 * 3600)
        traditional_energy = sum(light.power * delta_t for light in self.lights
                                if self._should_light_be_on(light)) / (1000 * 3600)
        self.energy_traditional_kwh += traditional_energy

        self.brightness_history.append(np.mean(brightness_levels))
        self.energy_history.append((self.energy_smart_kwh, self.energy_traditional_kwh))
        self.time += delta_t

    def _should_light_be_on(self, light):
        if self.time_of_day == TIME_OF_DAY_DAY:
            return self.weather in [WEATHER_RAIN, WEATHER_FOG, WEATHER_SNOW]
        return True

    def _get_ambient_light(self):
        base_light = {
            TIME_OF_DAY_DAY: 0.9,
            TIME_OF_DAY_TWILIGHT: 0.4,
            TIME_OF_DAY_NIGHT: 0.1
        }.get(self.time_of_day, 0.1)

        weather_factor = {
            WEATHER_CLEAR: 1.0,
            WEATHER_CLOUDY: 0.8,
            WEATHER_RAIN: 0.6,
            WEATHER_FOG: 0.4,
            WEATHER_SNOW: 0.5
        }.get(self.weather, 1.0)

        return base_light * weather_factor

    def reset(self):
        self.energy_smart_kwh = 0
        self.energy_traditional_kwh = 0
        self.brightness_history.clear()
        self.energy_history.clear()
        self.cars.clear()
        self.time = 0
        self._time_of_day_numeric = self._time_of_day_to_num(self.time_of_day)
        self._target_time_of_day_numeric = self._time_of_day_numeric
        self._time_of_day_transition_elapsed = 0
