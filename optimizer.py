import numpy as np
from scipy.optimize import minimize, Bounds
from core import LightingModel

class LightingOptimizer:
    def __init__(self, model: LightingModel, time_window: tuple = (0, 3600)):
        self.model = model
        self.t_eval = np.linspace(time_window[0], time_window[1], 100)  # Время моделирования, сек

    def objective(self, x: np.ndarray) -> float:
        """
        Целевая функция: интегральное энергопотребление за весь период времени.
        x[0] — мощность светильника (Вт)
        x[1] — расстояние между фонарями (м)
        """
        P, d = x[0], x[1]
        delta_t = self.t_eval[1] - self.t_eval[0]
        total_energy = 0.0

        for t in self.t_eval:
            L = self.model.brightness_profile(t, P, d)
            avg_brightness = np.mean(L)
            energy_t = P * avg_brightness * delta_t  # Энергия за интервал delta_t
            total_energy += energy_t

        return total_energy

    def gost_constraints(self) -> dict:
        """
        Ограничение по минимальной освещенности (ГОСТ 33176-2014)
        Минимум 20 люкс.
        """
        def constraint_min_illuminance(x):
            P, d = x[0], x[1]
            illuminances = []
            for t in self.t_eval:
                L = self.model.brightness_profile(t, P, d)
                illuminances.extend(L * 100)  # Преобразование в люксы
            return np.min(illuminances) - 20  # должна быть >= 0

        return {
            'type': 'ineq',
            'fun': constraint_min_illuminance
        }

    def optimize(self):
        initial_guess = [100.0, 30.0]  # [мощность Вт, расстояние м]
        bounds = Bounds([50.0, 20.0], [200.0, 50.0])  # Диапазон значений

        result = minimize(
            fun=self.objective,
            x0=initial_guess,
            method='SLSQP',
            bounds=bounds,
            constraints=[self.gost_constraints()],
            options={'disp': True}
        )
        return result
