import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.animation import FuncAnimation
from model import TrafficSimulator, TrafficMode, TimeOfDay, Weather
from matplotlib.ticker import FormatStrFormatter

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Умное освещение с учётом погоды и времени суток")
        self.geometry("1300x1000")
        
        self.simulator = TrafficSimulator(road_length=1000, num_lights=20)
        self.simulation_running = False
        self.animation = None
        
        self._setup_controls()
        self._setup_plots()
        
    def _setup_controls(self):
        control_frame = ttk.Frame(self)
        control_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)
        
        # Выбор времени суток
        ttk.Label(control_frame, text="Время суток:").grid(row=0, column=0)
        self.time_of_day = tk.StringVar(value=TimeOfDay.NIGHT.value)
        times = [("День", TimeOfDay.DAY.value),
                ("Сумерки", TimeOfDay.TWILIGHT.value),
                ("Ночь", TimeOfDay.NIGHT.value)]
        for i, (text, val) in enumerate(times):
            ttk.Radiobutton(control_frame, text=text, variable=self.time_of_day, 
                           value=val).grid(row=0, column=i+1)
        
        # Выбор погоды
        ttk.Label(control_frame, text="Погода:").grid(row=1, column=0)
        self.weather = tk.StringVar(value=Weather.CLEAR.value)
        weathers = [("Ясно", Weather.CLEAR.value),
                   ("Облачно", Weather.CLOUDY.value),
                   ("Дождь", Weather.RAIN.value),
                   ("Туман", Weather.FOG.value),
                   ("Снег", Weather.SNOW.value)]
        for i, (text, val) in enumerate(weathers):
            ttk.Radiobutton(control_frame, text=text, variable=self.weather, 
                           value=val).grid(row=1, column=i+1)
        
        # Выбор режима трафика
        ttk.Label(control_frame, text="Режим трафика:").grid(row=2, column=0)
        self.traffic_mode = tk.StringVar(value=TrafficMode.UNIFORM.value)
        modes = [("Равномерный", TrafficMode.UNIFORM.value),
                ("Редкий", TrafficMode.SPARSE.value),
                ("Пробка", TrafficMode.JAM.value)]
        for i, (text, val) in enumerate(modes):
            ttk.Radiobutton(control_frame, text=text, variable=self.traffic_mode, 
                           value=val).grid(row=2, column=i+1)
        
        # Параметры трафика
        ttk.Label(control_frame, text="Плотность (0.1-1):").grid(row=3, column=0)
        self.density_slider = ttk.Scale(control_frame, from_=0.1, to=1, value=0.5)
        self.density_slider.grid(row=3, column=1)
        
        ttk.Label(control_frame, text="Скорость (10-120 км/ч):").grid(row=3, column=2)
        self.speed_slider = ttk.Scale(control_frame, from_=10, to=120, value=50)
        self.speed_slider.grid(row=3, column=3)
        
        # Кнопки управления
        ttk.Button(control_frame, text="Применить условия", 
                  command=self._apply_conditions).grid(row=4, column=0)
        ttk.Button(control_frame, text="Сгенерировать трафик", 
                  command=self._generate_traffic).grid(row=4, column=1)
        ttk.Button(control_frame, text="Запустить симуляцию", 
                  command=self._start_simulation).grid(row=4, column=2)
        ttk.Button(control_frame, text="Остановить", 
                  command=self._stop_simulation).grid(row=4, column=3)
        
    def _setup_plots(self):
        self.plot_frame = ttk.Frame(self)
        self.plot_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
        
        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(12, 9))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Настройка осей
        self.ax1.set_title("Энергопотребление")
        self.ax1.set_xlabel("Время (с)")
        self.ax1.set_ylabel("Энергия, кВт·ч")
        self.ax1.yaxis.set_major_formatter(FormatStrFormatter('%.3f'))
        
        self.ax2.set_title("Средняя яркость фонарей")
        self.ax2.set_xlabel("Время (с)")
        self.ax2.set_ylabel("Яркость (0-1)")
        
        # Линии графиков
        self.energy_line1, = self.ax1.plot([], [], 'g', label="Умное освещение")
        self.energy_line2, = self.ax1.plot([], [], 'r', label="Традиционное")
        self.brightness_line, = self.ax2.plot([], [], 'b')
        self.ax1.legend()
        
        # Текст с экономией
        self.economy_text = self.ax1.text(0.02, 0.95, "", transform=self.ax1.transAxes)
        
    def _apply_conditions(self):
        self.simulator.set_conditions(
            TimeOfDay(self.time_of_day.get()),
            Weather(self.weather.get())
        )
        
    def _generate_traffic(self):
        self.simulator.traffic_mode = TrafficMode(self.traffic_mode.get())
        self.simulator.traffic_density = self.density_slider.get()
        self.simulator.traffic_speed = self.speed_slider.get()
        self.simulator.generate_traffic()
        
    def _start_simulation(self):
        if self.animation:
            self.animation.event_source.stop()
            
        self._apply_conditions()
        self._generate_traffic()
        
        self.simulator.energy_smart_kwh = 0
        self.simulator.energy_traditional_kwh = 0
        self.simulator.brightness_history = []
        self.simulator.energy_history = []
        
        self.simulation_running = True
        self.animation = FuncAnimation(self.fig, self._update_plots, 
                                     frames=100, interval=100, blit=False)
        self.canvas.draw()
        
    def _stop_simulation(self):
        self.simulation_running = False
        if self.animation:
            self.animation.event_source.stop()
        
    def _update_plots(self, frame):
        if not self.simulation_running:
            return
            
        self.simulator.update(delta_t=1, alpha=0.5, beta=0.1, gamma=0.3, delta=0.2, n_max=10)
        
        times = list(range(len(self.simulator.energy_history)))
        smart_energy = [e[0] for e in self.simulator.energy_history]
        trad_energy = [e[1] for e in self.simulator.energy_history]
        
        # Обновление графиков
        self.energy_line1.set_data(times, smart_energy)
        self.energy_line2.set_data(times, trad_energy)
        self.brightness_line.set_data(times, self.simulator.brightness_history)
        
        # Расчёт и отображение экономии
        if len(trad_energy) > 0 and trad_energy[-1] > 0:
            economy = (trad_energy[-1] - smart_energy[-1]) / trad_energy[-1] * 100
            self.economy_text.set_text(f"Экономия: {economy:.1f}%")
        
        # Автомасштабирование
        for ax in [self.ax1, self.ax2]:
            ax.relim()
            ax.autoscale_view()
            
        return self.energy_line1, self.energy_line2, self.brightness_line

if __name__ == "__main__":
    app = App()
    app.mainloop()