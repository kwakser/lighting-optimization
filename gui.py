import sys
import json
import numpy as np
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QSlider, QGroupBox, QFormLayout,
    QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt, QTimer
import pyqtgraph as pg

from model import (
    TrafficSimulator,
    TIME_OF_DAY_DAY, TIME_OF_DAY_TWILIGHT, TIME_OF_DAY_NIGHT,
    WEATHER_CLEAR, WEATHER_CLOUDY, WEATHER_RAIN, WEATHER_FOG, WEATHER_SNOW,
    TRAFFIC_MODE_UNIFORM, TRAFFIC_MODE_SPARSE, TRAFFIC_MODE_JAM, TRAFFIC_MODE_VALUES
)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Умное освещение с Qt и PyQtGraph")
        self.resize(1200, 800)

        self.simulator = TrafficSimulator()

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)

        control_panel = QGroupBox("Настройки симуляции")
        control_layout = QFormLayout()
        control_panel.setLayout(control_layout)
        control_panel.setMaximumWidth(320)

        # Время суток с русскими названиями
        self.combo_time_of_day = QComboBox()
        self.time_of_day_map = {
            "День": TIME_OF_DAY_DAY,
            "Сумерки": TIME_OF_DAY_TWILIGHT,
            "Ночь": TIME_OF_DAY_NIGHT
        }
        self.combo_time_of_day.addItems(self.time_of_day_map.keys())
        control_layout.addRow(QLabel("Время суток:"), self.combo_time_of_day)

        # Погода с русскими названиями
        self.combo_weather = QComboBox()
        self.weather_map = {
            "Ясно": WEATHER_CLEAR,
            "Облачно": WEATHER_CLOUDY,
            "Дождь": WEATHER_RAIN,
            "Туман": WEATHER_FOG,
            "Снег": WEATHER_SNOW
        }
        self.combo_weather.addItems(self.weather_map.keys())
        control_layout.addRow(QLabel("Погода:"), self.combo_weather)

        # Режим трафика с русскими названиями
        self.combo_traffic_mode = QComboBox()
        self.traffic_mode_map = {
            "Равномерный": TRAFFIC_MODE_UNIFORM,
            "Редкий": TRAFFIC_MODE_SPARSE,
            "Пробка": TRAFFIC_MODE_JAM
        }
        self.combo_traffic_mode.addItems(self.traffic_mode_map.keys())
        control_layout.addRow(QLabel("Режим трафика:"), self.combo_traffic_mode)

        self.slider_density = QSlider(Qt.Horizontal)
        self.slider_density.setMinimum(10)
        self.slider_density.setMaximum(100)
        self.slider_density.setValue(50)
        control_layout.addRow(QLabel("Плотность трафика (0.1-1.0):"), self.slider_density)

        self.slider_speed = QSlider(Qt.Horizontal)
        self.slider_speed.setMinimum(10)
        self.slider_speed.setMaximum(150)
        self.slider_speed.setValue(50)
        control_layout.addRow(QLabel("Скорость трафика (км/ч):"), self.slider_speed)

        # Вертикальный layout для кнопок управления
        btn_layout = QVBoxLayout()
        self.btn_apply = QPushButton("Применить условия")
        self.btn_generate = QPushButton("Сгенерировать трафик")
        self.btn_start = QPushButton("Запустить симуляцию")
        self.btn_stop = QPushButton("Остановить")
        self.btn_clear = QPushButton("Очистить")
        self.btn_load_scenario = QPushButton("Загрузить сценарий")

        btn_layout.addWidget(self.btn_apply)
        btn_layout.addWidget(self.btn_generate)
        btn_layout.addWidget(self.btn_start)
        btn_layout.addWidget(self.btn_stop)
        btn_layout.addWidget(self.btn_clear)
        btn_layout.addWidget(self.btn_load_scenario)

        control_layout.addRow(btn_layout)

        main_layout.addWidget(control_panel)

        plot_panel = QWidget()
        plot_layout = QVBoxLayout(plot_panel)

        self.plot_energy = pg.PlotWidget(title="Энергопотребление (кВт·ч)")
        self.plot_energy.addLegend()
        self.plot_energy.setLabel('left', 'Энергия', units='кВт·ч')
        self.plot_energy.setLabel('bottom', 'Время', units='с')
        self.plot_energy.showGrid(x=True, y=True)
        self.energy_line_smart = self.plot_energy.plot(pen=pg.mkPen('g', width=2), name="Умное освещение")
        self.energy_line_trad = self.plot_energy.plot(pen=pg.mkPen('r', width=2), name="Традиционное освещение")
        self.energy_text = pg.TextItem("", anchor=(0, 1))
        self.plot_energy.addItem(self.energy_text)
        plot_layout.addWidget(self.plot_energy)

        self.plot_brightness = pg.PlotWidget(title="Средняя яркость фонарей")
        self.plot_brightness.setLabel('left', 'Яркость', units='')
        self.plot_brightness.setLabel('bottom', 'Время', units='с')
        self.plot_brightness.showGrid(x=True, y=True)
        self.brightness_line = self.plot_brightness.plot(pen=pg.mkPen('b', width=2))
        plot_layout.addWidget(self.plot_brightness)

        main_layout.addWidget(plot_panel)

        self.timer = QTimer()
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.update_simulation)

        self.btn_apply.clicked.connect(self.apply_conditions)
        self.btn_generate.clicked.connect(self.generate_traffic)
        self.btn_start.clicked.connect(self.start_simulation)
        self.btn_stop.clicked.connect(self.stop_simulation)
        self.btn_clear.clicked.connect(self.clear_simulation)
        self.btn_load_scenario.clicked.connect(self.load_scenario)

        self.simulation_running = False

        self.time_data = []
        self.energy_smart_data = []
        self.energy_trad_data = []
        self.brightness_data = []

        self.active_scenario = None
        self.scenario_time = 0.0
        self.time_multiplier = 1.0
        self.ramp_animations = {}

    def apply_conditions(self):
        try:
            tod = self.time_of_day_map[self.combo_time_of_day.currentText()]
            weather = self.weather_map[self.combo_weather.currentText()]
            self.simulator.set_conditions(tod, weather)
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Ошибка установки условий:\n{e}")

    def generate_traffic(self):
        try:
            mode = self.traffic_mode_map[self.combo_traffic_mode.currentText()]
            if mode not in TRAFFIC_MODE_VALUES:
                raise ValueError(f"Неверный режим трафика: {mode}")
            self.simulator.traffic_mode = mode
            self.simulator.traffic_density = self.slider_density.value() / 100.0
            self.simulator.traffic_speed = self.slider_speed.value()
            self.simulator.generate_traffic()
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Ошибка генерации трафика:\n{e}")

    def load_scenario(self):
        path, _ = QFileDialog.getOpenFileName(self, "Выберите файл сценария", "", "JSON Files (*.json);;All Files (*)")
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                scenario = json.load(f)
            self.prepare_scenario(scenario)
            QMessageBox.information(self, "Успех", "Сценарий успешно загружен")
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Ошибка загрузки сценария:\n{e}")

    def prepare_scenario(self, scenario):
        self.active_scenario = {
            "events": sorted(scenario.get("events", []), key=lambda x: x["time"]),
            "current_event": 0,
            "config": scenario.get("config", {})
        }
        self.time_multiplier = self.active_scenario["config"].get("time_scale", 1.0)
        self.simulation_duration = self.active_scenario["config"].get("duration", 1800)

        self.clear_simulation()
        self.process_initial_events()

    def process_initial_events(self):
        while (self.active_scenario["current_event"] < len(self.active_scenario["events"]) and
               self.active_scenario["events"][self.active_scenario["current_event"]]["time"] == 0):
            event = self.active_scenario["events"][self.active_scenario["current_event"]]
            self.process_event(event)
            self.active_scenario["current_event"] += 1

    def process_event(self, event):
        for action in event.get("actions", []):
            action_type = action.get("type")
            if action_type == "set":
                self.apply_action_set(action)
            elif action_type == "ramp":
                self.start_value_ramp(action)

    def apply_action_set(self, action):
        param = action.get("param")
        value = action.get("value")
        setters = {
            "time_of_day": (self.combo_time_of_day.setCurrentText, self.time_of_day_map),
            "weather": (self.combo_weather.setCurrentText, self.weather_map),
            "traffic_mode": (self.combo_traffic_mode.setCurrentText, self.traffic_mode_map),
            "traffic_density": (lambda v: self.slider_density.setValue(int(v * 100)), None),
            "traffic_speed": (self.slider_speed.setValue, None)
        }
        if param in setters:
            setter, mapping = setters[param]
            if mapping:
                for k, v in mapping.items():
                    if v == value:
                        setter(k)
                        break
            else:
                setter(int(value))
            self._sync_simulator()

    def start_value_ramp(self, action):
        param = action.get("param")
        from_value = action.get("from")
        to_value = action.get("to")
        duration = action.get("duration")

        if from_value is None:
            from_value = self._get_current_value(param)

        self.ramp_animations[param] = {
            "start_time": self.scenario_time,
            "end_time": self.scenario_time + duration,
            "start_value": from_value,
            "end_value": to_value
        }

    def _get_current_value(self, param):
        getters = {
            "time_of_day": lambda: self.time_of_day_map[self.combo_time_of_day.currentText()],
            "weather": lambda: self.weather_map[self.combo_weather.currentText()],
            "traffic_mode": lambda: self.traffic_mode_map[self.combo_traffic_mode.currentText()],
            "traffic_density": lambda: self.slider_density.value() / 100.0,
            "traffic_speed": lambda: self.slider_speed.value()
        }
        return getters[param]()

    def start_simulation(self):
        if not self.simulation_running:
            self.apply_conditions()
            self.generate_traffic()
            self.simulator.reset()
            self.time_data.clear()
            self.energy_smart_data.clear()
            self.energy_trad_data.clear()
            self.brightness_data.clear()
            self.simulation_running = True
            self.scenario_time = 0.0
            self.ramp_animations.clear()
            self.timer.start()

    def stop_simulation(self):
        if self.simulation_running:
            self.timer.stop()
            self.simulation_running = False

    def clear_simulation(self):
        self.stop_simulation()
        self.simulator.reset()
        self.time_data.clear()
        self.energy_smart_data.clear()
        self.energy_trad_data.clear()
        self.brightness_data.clear()
        self.update_plots()

    def update_simulation(self):
        if not self.simulation_running:
            return

        self.scenario_time += 1 * self.time_multiplier

        # Обработка событий сценария
        if self.active_scenario:
            while (self.active_scenario["current_event"] < len(self.active_scenario["events"]) and
                   self.scenario_time >= self.active_scenario["events"][self.active_scenario["current_event"]]["time"]):
                event = self.active_scenario["events"][self.active_scenario["current_event"]]
                self.process_event(event)
                self.active_scenario["current_event"] += 1

        # Обработка плавных изменений (ramp)
        to_remove = []
        for param, anim in self.ramp_animations.items():
            if self.scenario_time >= anim["end_time"]:
                self._set_parameter(param, anim["end_value"])
                to_remove.append(param)
            else:
                progress = (self.scenario_time - anim["start_time"]) / (anim["end_time"] - anim["start_time"])
                current_value = anim["start_value"] + (anim["end_value"] - anim["start_value"]) * progress
                self._set_parameter(param, current_value)
        for param in to_remove:
            del self.ramp_animations[param]

        # Обновление симуляции
        self.simulator.update(delta_t=1)
        t = self.simulator.time
        self.time_data.append(t)
        self.energy_smart_data.append(self.simulator.energy_smart_kwh)
        self.energy_trad_data.append(self.simulator.energy_traditional_kwh)
        self.brightness_data.append(np.mean([light.current_brightness for light in self.simulator.lights]))

        self.update_plots()

        if self.scenario_time >= self.simulation_duration:
            self.stop_simulation()

    def _set_parameter(self, param, value):
        setters = {
            "time_of_day": (self.combo_time_of_day.setCurrentText, self.time_of_day_map),
            "weather": (self.combo_weather.setCurrentText, self.weather_map),
            "traffic_mode": (self.combo_traffic_mode.setCurrentText, self.traffic_mode_map),
            "traffic_density": (lambda v: self.slider_density.setValue(int(v * 100)), None),
            "traffic_speed": (self.slider_speed.setValue, None)
        }
        if param in setters:
            setter, mapping = setters[param]
            if mapping:
                for k, v in mapping.items():
                    if v == value:
                        setter(k)
                        break
            else:
                setter(int(value))
            self._sync_simulator()

    def _sync_simulator(self):
        self.simulator.set_conditions(
            self.time_of_day_map[self.combo_time_of_day.currentText()],
            self.weather_map[self.combo_weather.currentText()]
        )
        self.simulator.traffic_mode = self.traffic_mode_map[self.combo_traffic_mode.currentText()]
        self.simulator.traffic_density = self.slider_density.value() / 100.0
        self.simulator.traffic_speed = self.slider_speed.value()
        self.simulator.generate_traffic()

    def update_plots(self):
        self.energy_line_smart.setData(self.time_data, self.energy_smart_data)
        self.energy_line_trad.setData(self.time_data, self.energy_trad_data)
        self.brightness_line.setData(self.time_data, self.brightness_data)

        if self.energy_trad_data and self.energy_trad_data[-1] > 0:
            economy = (self.energy_trad_data[-1] - self.energy_smart_data[-1]) / self.energy_trad_data[-1] * 100
            self.energy_text.setText(f"Экономия: {economy:.1f}%")
            self.energy_text.setPos(self.time_data[-1], self.energy_smart_data[-1])
        else:
            self.energy_text.setText("")


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
