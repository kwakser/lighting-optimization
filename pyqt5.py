import sys
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QWidget,
                             QTextEdit, QTableWidget, QTableWidgetItem, QGraphicsScene, QGraphicsView, QCheckBox,
                             QLineEdit, QFormLayout, QComboBox, QStackedWidget)
from PyQt5.QtGui import QPen, QBrush, QPainter, QPolygonF
from PyQt5.QtCore import Qt, QPointF


class LightingInterface(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LightingModel")
        self.setGeometry(100, 100, 800, 600)

        self.centralWidget = QWidget()
        self.setCentralWidget(self.centralWidget)

        mainLayout = QHBoxLayout()
        leftLayout = QVBoxLayout()
        rightLayout = QVBoxLayout()

        paramsForm = QFormLayout()

        self.lamp_power = QLineEdit("10")
        self.true_lamp_power = QLineEdit("20")
        self.lamp_price = QLineEdit("1.0")
        self.road_length = QLineEdit("5.0")
        self.type_of_sensors = QComboBox(self)
        self.type_of_sensors.addItems(["Camera", "Lidar", "Radar"])
        self.type_of_sensors.currentIndexChanged.connect(self.change_sensor_page)


        paramsForm.addRow("Мощность лампы:", self.lamp_power)
        paramsForm.addRow("Полезная мощность лампы:", self.true_lamp_power)
        paramsForm.addRow("Цена лампы:", self.lamp_price)
        paramsForm.addRow("Длина дороги:", self.road_length)
        paramsForm.addRow("Тип датчика:", self.type_of_sensors)

        leftLayout.addLayout(paramsForm)

        self.stacked_widget = QStackedWidget()
        leftLayout.addWidget(self.stacked_widget)

        self.create_camera_page()
        self.create_lidar_page()
        self.create_radar_page()

        mainLayout.addLayout(leftLayout, 1)
        mainLayout.addLayout(rightLayout, 2)

        self.centralWidget.setLayout(mainLayout)

    def create_camera_page(self):
        """Страница настроек камеры"""
        page = QWidget()
        form_layout = QFormLayout()

        self.cam_resolution = QLineEdit("1920x1080")
        self.cam_fps = QLineEdit("30")
        self.cam_fov = QLineEdit("90")
        self.cam_min_light = QLineEdit("0.1")
        self.cam_price = QLineEdit("1000")

        form_layout.addRow("Разрешение (пиксели):", self.cam_resolution)
        form_layout.addRow("Частота кадров (FPS):", self.cam_fps)
        form_layout.addRow("Угол обзора (FoV, °):", self.cam_fov)
        form_layout.addRow("Мин. освещенность (лк):", self.cam_min_light)
        form_layout.addRow("Стоимость:", self.cam_price)

        page.setLayout(form_layout)
        self.stacked_widget.addWidget(page)

    def create_lidar_page(self):
        """Страница настроек лидара"""
        page = QWidget()
        form_layout = QFormLayout()

        self.lidar_range = QLineEdit("100")
        self.lidar_accuracy = QLineEdit("0.02")
        self.lidar_scan_rate = QLineEdit("10")
        self.lidar_beam_count = QLineEdit("16")
        self.lidar_price = QLineEdit("10000")

        form_layout.addRow("Дальность (м):", self.lidar_range)
        form_layout.addRow("Точность (±м):", self.lidar_accuracy)
        form_layout.addRow("Частота сканирования (Гц):", self.lidar_scan_rate)
        form_layout.addRow("Количество лучей:", self.lidar_beam_count)
        form_layout.addRow("Стоимость:", self.lidar_price)

        page.setLayout(form_layout)
        self.stacked_widget.addWidget(page)

    def create_radar_page(self):
        """Страница настроек радара"""
        page = QWidget()
        form_layout = QFormLayout()

        self.radar_range = QLineEdit("150")
        self.radar_update_rate = QLineEdit("20")
        self.radar_angle_res = QLineEdit("5")
        self.radar_min_speed = QLineEdit("0.5")
        self.radar_price = QLineEdit("5000")

        form_layout.addRow("Дальность (м):", self.radar_range)
        form_layout.addRow("Частота обновления (Гц):", self.radar_update_rate)
        form_layout.addRow("Угловое разрешение (°):", self.radar_angle_res)
        form_layout.addRow("Мин. скорость (м/с):", self.radar_min_speed)
        form_layout.addRow("Стоимость:", self.radar_price)

        page.setLayout(form_layout)
        self.stacked_widget.addWidget(page)

    def change_sensor_page(self, index):
        """Переключает страницу в зависимости от выбранного датчика"""
        self.stacked_widget.setCurrentIndex(index)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = LightingInterface()
    window.show()
    sys.exit(app.exec_())
