import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.animation import FuncAnimation
from matplotlib.ticker import FormatStrFormatter

from model import (
    TrafficSimulator,
    TIME_OF_DAY_DAY, TIME_OF_DAY_NIGHT, TIME_OF_DAY_TWILIGHT,
    WEATHER_CLEAR, WEATHER_CLOUDY, WEATHER_RAIN, WEATHER_FOG, WEATHER_SNOW,
    TRAFFIC_MODE_UNIFORM, TRAFFIC_MODE_SPARSE, TRAFFIC_MODE_JAM, TRAFFIC_MODE_VALUES
)

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Умное освещение с учётом погоды и времени суток")
        self.geometry("1300x1000")

        self.simulator = TrafficSimulator(road_length=1000, num_lights=20)
        self.simulation_running = False
        self.animation = None

        self.active_scenario = None
        self.scenario_time = 0.0
        self.time_multiplier = 1.0
        self.ramp_animations = {}

        self.simulation_duration = 100  # по умолчанию

        self._setup_controls()
        self._setup_plots()

    def _setup_controls(self):
        control_frame = ttk.Frame(self)
        control_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        ttk.Label(control_frame, text="Время суток:").grid(row=0, column=0)
        self.time_of_day = tk.StringVar(value=TIME_OF_DAY_NIGHT)
        times = [("День", TIME_OF_DAY_DAY),
                 ("Сумерки", TIME_OF_DAY_TWILIGHT),
                 ("Ночь", TIME_OF_DAY_NIGHT)]
        for i, (text, val) in enumerate(times):
            ttk.Radiobutton(control_frame, text=text, variable=self.time_of_day,
                            value=val).grid(row=0, column=i + 1)

        ttk.Label(control_frame, text="Погода:").grid(row=1, column=0)
        self.weather = tk.StringVar(value=WEATHER_CLEAR)
        weathers = [("Ясно", WEATHER_CLEAR),
                    ("Облачно", WEATHER_CLOUDY),
                    ("Дождь", WEATHER_RAIN),
                    ("Туман", WEATHER_FOG),
                    ("Снег", WEATHER_SNOW)]
        for i, (text, val) in enumerate(weathers):
            ttk.Radiobutton(control_frame, text=text, variable=self.weather,
                            value=val).grid(row=1, column=i + 1)

        ttk.Label(control_frame, text="Режим трафика:").grid(row=2, column=0)
        self.traffic_mode = tk.StringVar(value=TRAFFIC_MODE_UNIFORM)
        modes = [("Равномерный", TRAFFIC_MODE_UNIFORM),
                 ("Редкий", TRAFFIC_MODE_SPARSE),
                 ("Пробка", TRAFFIC_MODE_JAM)]
        for i, (text, val) in enumerate(modes):
            ttk.Radiobutton(control_frame, text=text, variable=self.traffic_mode,
                            value=val).grid(row=2, column=i + 1)

        ttk.Label(control_frame, text="Плотность (0.1-1):").grid(row=3, column=0)
        self.density_slider = ttk.Scale(control_frame, from_=0.1, to=1, value=0.5)
        self.density_slider.grid(row=3, column=1)

        ttk.Label(control_frame, text="Скорость (10-150 км/ч):").grid(row=3, column=2)
        self.speed_slider = ttk.Scale(control_frame, from_=10, to=150, value=50)
        self.speed_slider.grid(row=3, column=3)

        ttk.Label(control_frame, text="Длительность (сек):").grid(row=3, column=4)
        self.duration_label = ttk.Label(control_frame, text=str(self.simulation_duration))
        self.duration_label.grid(row=3, column=5)

        ttk.Button(control_frame, text="Применить условия",
                   command=self._apply_conditions).grid(row=4, column=0)
        ttk.Button(control_frame, text="Сгенерировать трафик",
                   command=self._generate_traffic).grid(row=4, column=1)
        ttk.Button(control_frame, text="Запустить симуляцию",
                   command=self._start_simulation).grid(row=4, column=2)
        ttk.Button(control_frame, text="Остановить",
                   command=self._stop_simulation).grid(row=4, column=3)
        ttk.Button(control_frame, text="Загрузить сценарий",
                   command=self._load_scenario).grid(row=4, column=4)

    def _setup_plots(self):
        self.plot_frame = ttk.Frame(self)
        self.plot_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(12, 9))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self.ax1.set_title("Энергопотребление")
        self.ax1.set_xlabel("Время (с)")
        self.ax1.set_ylabel("Энергия, кВт·ч")
        self.ax1.yaxis.set_major_formatter(FormatStrFormatter('%.3f'))

        self.ax2.set_title("Средняя яркость фонарей")
        self.ax2.set_xlabel("Время (с)")
        self.ax2.set_ylabel("Яркость (0-1)")

        self.energy_line1, = self.ax1.plot([], [], 'g', label="Умное освещение")
        self.energy_line2, = self.ax1.plot([], [], 'r', label="Традиционное")
        self.brightness_line, = self.ax2.plot([], [], 'b')
        self.ax1.legend()

        self.economy_text = self.ax1.text(0.02, 0.95, "", transform=self.ax1.transAxes)

    def _apply_conditions(self):
        try:
            self.simulator.set_conditions(
                self.time_of_day.get(),
                self.weather.get()
            )
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка установки условий: {e}")

    def _generate_traffic(self):
        try:
            mode = self.traffic_mode.get()
            if mode not in TRAFFIC_MODE_VALUES:
                raise ValueError(f"Неверный режим трафика: {mode}")
            self.simulator.traffic_mode = mode
            self.simulator.traffic_density = self.density_slider.get()
            self.simulator.traffic_speed = self.speed_slider.get()
            self.simulator.generate_traffic()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка генерации трафика: {e}")

    def _start_simulation(self):
        if self.animation:
            self.animation.event_source.stop()

        self._apply_conditions()
        self._generate_traffic()

        self.simulator.reset()
        self.simulation_running = True
        self.scenario_time = 0.0
        self.ramp_animations.clear()

        frames = self.simulation_duration if self.active_scenario else 100

        self.animation = FuncAnimation(self.fig, self._update_plots,
                                       frames=frames,
                                       interval=100, blit=False)
        self.canvas.draw()

    def _stop_simulation(self):
        self.simulation_running = False
        if self.animation:
            self.animation.event_source.stop()

    def _update_plots(self, frame):
        if not self.simulation_running:
            return

        self.scenario_time += 1 * self.time_multiplier

        if self.active_scenario:
            while (self.active_scenario['current_event'] < len(self.active_scenario['events']) and
                   self.scenario_time >= self.active_scenario['events'][self.active_scenario['current_event']]['time']):
                event = self.active_scenario['events'][self.active_scenario['current_event']]
                self._process_event(event)
                self.active_scenario['current_event'] += 1

        to_remove = []
        for param, anim in self.ramp_animations.items():
            if self.scenario_time >= anim['end_time']:
                self._set_parameter(param, anim['end_value'])
                to_remove.append(param)
            else:
                progress = (self.scenario_time - anim['start_time']) / (anim['end_time'] - anim['start_time'])
                current_value = anim['start_value'] + (anim['end_value'] - anim['start_value']) * progress
                self._set_parameter(param, current_value)
        for param in to_remove:
            self.ramp_animations.pop(param)

        self.simulator.update(delta_t=1, alpha=0.5, beta=0.1, gamma=0.3, delta=0.2, n_max=10)

        times = list(range(len(self.simulator.energy_history)))
        smart_energy = [e[0] for e in self.simulator.energy_history]
        trad_energy = [e[1] for e in self.simulator.energy_history]

        self.energy_line1.set_data(times, smart_energy)
        self.energy_line2.set_data(times, trad_energy)
        self.brightness_line.set_data(times, self.simulator.brightness_history)

        if trad_energy and trad_energy[-1] > 0:
            economy = (trad_energy[-1] - smart_energy[-1]) / trad_energy[-1] * 100
            self.economy_text.set_text(f"Экономия: {economy:.1f}%")

        for ax in [self.ax1, self.ax2]:
            ax.relim()
            ax.autoscale_view()

        return self.energy_line1, self.energy_line2, self.brightness_line

    def _process_event(self, event):
        for action in event.get('actions', []):
            action_type = action.get('type')
            if action_type == 'set':
                self._apply_action_set(action)
            elif action_type == 'ramp':
                self._start_value_ramp(action)
            else:
                messagebox.showwarning("Сценарий", f"Неизвестный тип действия: {action_type}")

    def _apply_action_set(self, action):
        param = action.get('param')
        value = action.get('value')

        setters = {
            'time_of_day': self.time_of_day.set,
            'weather': self.weather.set,
            'traffic_mode': self.traffic_mode.set,
            'traffic_density': self.density_slider.set,
            'traffic_speed': self.speed_slider.set,
        }

        if param in setters:
            setter = setters[param]
            setter(value)
            self._sync_simulator()
        else:
            messagebox.showwarning("Сценарий", f"Неизвестный параметр: {param}")

    def _start_value_ramp(self, action):
        param = action.get('param')
        from_value = action.get('from')
        to_value = action.get('to')
        duration = action.get('duration')

        if from_value is None:
            from_value = self._get_current_value(param)

        if from_value is None or to_value is None or duration is None:
            messagebox.showwarning("Сценарий", f"Неверно задан ramp для параметра {param}")
            return

        self.ramp_animations[param] = {
            'start_time': self.scenario_time,
            'end_time': self.scenario_time + duration,
            'start_value': from_value,
            'end_value': to_value
        }

    def _get_current_value(self, param):
        getters = {
            'time_of_day': lambda: self.time_of_day.get(),
            'weather': lambda: self.weather.get(),
            'traffic_mode': lambda: self.traffic_mode.get(),
            'traffic_density': lambda: self.density_slider.get(),
            'traffic_speed': lambda: self.speed_slider.get(),
        }
        getter = getters.get(param)
        if getter:
            return getter()
        return None

    def _set_parameter(self, param, value):
        setters = {
            'time_of_day': self.time_of_day.set,
            'weather': self.weather.set,
            'traffic_mode': self.traffic_mode.set,
            'traffic_density': self.density_slider.set,
            'traffic_speed': self.speed_slider.set,
        }
        setter = setters.get(param)
        if setter:
            setter(value)
            self._sync_simulator()

    def _sync_simulator(self):
        try:
            self.simulator.set_conditions(
                self.time_of_day.get(),
                self.weather.get()
            )
            mode = self.traffic_mode.get()
            if mode not in {TRAFFIC_MODE_UNIFORM, TRAFFIC_MODE_SPARSE, TRAFFIC_MODE_JAM}:
                raise ValueError(f"Неверный режим трафика: {mode}")
            self.simulator.traffic_mode = mode
            self.simulator.traffic_density = self.density_slider.get()
            self.simulator.traffic_speed = self.speed_slider.get()
            self.simulator.generate_traffic()
        except Exception as e:
            messagebox.showwarning("Ошибка синхронизации", str(e))

    def _load_scenario(self):
        file_path = filedialog.askopenfilename(
            title="Выберите файл сценария",
            filetypes=[("JSON files", "*.json"), ("Все файлы", "*.*")]
        )
        if not file_path:
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                scenario = json.load(f)

            if 'events' not in scenario:
                raise ValueError("В сценарии отсутствует ключ 'events'")

            events = sorted(scenario['events'], key=lambda x: x['time'])

            self.active_scenario = {
                'events': events,
                'current_event': 0,
                'config': scenario.get('config', {})
            }

            self.time_multiplier = self.active_scenario['config'].get('time_scale', 1.0)
            self.simulation_duration = self.active_scenario['config'].get('duration', 100)
            self.duration_label.config(text=str(self.simulation_duration))

            if events and events[0]['time'] == 0:
                self._process_event(events[0])
                self.active_scenario['current_event'] = 1

            messagebox.showinfo("Успех", "Сценарий успешно загружен!")

        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка загрузки сценария: {e}")


if __name__ == "__main__":
    app = App()
    app.mainloop()
