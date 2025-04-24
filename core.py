import numpy as np

class LightingModel:
    def __init__(self, params: dict, road_length: float, num_lights: int):
        self.alpha = params['alpha']
        self.beta = params['beta']
        self.gamma = params['gamma']
        self.delta = params['delta']
        self.Nmax = params['Nmax']
        self.road_length = road_length
        self.num_lights = num_lights
        self.x = np.linspace(0, road_length, num_lights)
        self.v = 25.0

    def vehicle_density(self, t: float) -> float:
        # Модель плотности трафика с двумя пиковыми часами
        return 20 + 15 * np.sin(2 * np.pi * (t - 25200) / 86400)

    def ambient_light(self, t: float) -> float:
        # Модель естественной освещенности (нормированная 0-1)
        return np.clip(0.5 * np.sin(2 * np.pi * t / 86400 - np.pi / 2) + 0.5, 0, 1)

    def brightness_profile(self, t: float, P: float, d: float) -> np.ndarray:
        """
        Расчет яркости фонарей в момент времени t
        по формуле:
        f(d,N,Iamb) = α·e^(−β·distance) + γ·(N/Nmax) + δ·(1−Iamb)
        где distance — расстояние от машины до фонаря
        """
        N = self.vehicle_density(t)
        Iamb = self.ambient_light(t)

        # Позиция машины по дороге (с учётом цикличности)
        position_car = (self.v * t) % (self.x[-1] + d)

        # Расстояния от машины до каждого фонаря
        distances = np.abs(self.x - position_car)

        brightness = (
            self.alpha * np.exp(-self.beta * distances) +
            self.gamma * (N / self.Nmax) +
            self.delta * (1 - Iamb)
        )
        # Ограничение яркости по ГОСТ: min 0.2, max 1.0 (нормированная)
        return np.clip(brightness, 0.2, 1.0)
