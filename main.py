import matplotlib.pyplot as plt
import numpy as np

from core import LightingModel
from optimizer import LightingOptimizer

def main():
    # Параметры модели
    params = {
        'alpha': 0.4,
        'beta': 0.2,
        'gamma': 0.3,
        'delta': 0.1,
        'Nmax': 50
    }

    # Создаем модель для участка 1000 м с 20 фонарями
    model = LightingModel(params, road_length=1000, num_lights=20)

    # Создаем оптимизатор с временным окном 1 час (3600 сек)
    optimizer = LightingOptimizer(model, time_window=(0, 3600))

    # Запускаем оптимизацию
    result = optimizer.optimize()

    if result.success:
        P_opt, d_opt = result.x
        print(f"Оптимальная мощность: {P_opt:.2f} Вт")
        print(f"Оптимальное расстояние между фонарями: {d_opt:.2f} м")
        print(f"Минимальное энергопотребление за период: {result.fun:.2f} Вт·с")

        # Визуализируем яркость в течение суток по оптимальным параметрам
        t_full = np.linspace(0, 86400, 1000)  # сутки в секундах
        brightness = [model.brightness_profile(t, P_opt, d_opt).mean() for t in t_full]

        plt.figure(figsize=(12, 5))
        plt.plot(t_full / 3600, brightness, label='Средняя яркость')
        plt.xlabel('Время суток (часы)')
        plt.ylabel('Яркость (0-1)')
        plt.title('Динамика средней яркости освещения в течение суток')
        plt.grid(True)
        plt.legend()
        plt.show()

    else:
        print("Оптимизация не удалась:", result.message)

if __name__ == "__main__":
    main()
