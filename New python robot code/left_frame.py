import tkinter as tk
from tkinter import ttk
import serial.tools.list_ports
from serial import SerialException
import threading


class LeftFrame(ttk.LabelFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, text="Общее", width=300)
        self.controller = controller
        self.serial_connection = None

        # Инициализация состояний
        self.sensors = ["Концевик верхний", "Концевик нижний",
                        "Концевик руки", "Концевик кисти"]
        self.sensor_states = {s: False for s in self.sensors}

        self.setup_connection_widgets()
        self.setup_sensor_indicators()
        self.setup_control_button()

    def setup_connection_widgets(self):
        frame = ttk.LabelFrame(self, text="Настройки подключения", padding=10)
        frame.pack(fill=tk.X, padx=5, pady=5)

        self.port_var = tk.StringVar()

        # Строка с кнопками
        button_row = ttk.Frame(frame)
        button_row.pack(fill=tk.X, pady=(0, 5))

        # Кнопка обновления портов
        ttk.Button(
            button_row,
            text="Обновить",
            command=self.update_ports,
            width=14
        ).pack(side=tk.LEFT, padx=2, expand=True)

        # Кнопка подключения
        self.connect_button = ttk.Button(
            button_row,
            text="Подключиться",
            command=self.toggle_connection,
            width=14
        )
        self.connect_button.pack(side=tk.LEFT, padx=2, expand=True)

        # Выпадающий список портов (во всю ширину)
        self.port_combobox = ttk.Combobox(
            frame,
            textvariable=self.port_var,
            state='readonly'
        )
        self.port_combobox.pack(fill=tk.X, pady=(0, 5))

        self.update_ports()

    def setup_sensor_indicators(self):
        frame = ttk.LabelFrame(self, text="Состояние датчиков", padding=10)
        frame.pack(fill=tk.X, padx=5, pady=10)

        self.sensor_labels = {}
        for sensor in self.sensors:
            row = ttk.Frame(frame)
            row.pack(fill=tk.X, padx=5, pady=3)

            indicator = ttk.Label(row, text="⬤", font=('Arial', 14), width=2)
            indicator.pack(side=tk.LEFT, padx=5)

            ttk.Label(row, text=sensor, width=18).pack(side=tk.LEFT)
            status = ttk.Label(row, text="Выкл", width=5)
            status.pack(side=tk.RIGHT)

            self.sensor_labels[sensor] = (indicator, status)

    def setup_control_button(self):
        tk.Button(
            self,
            text="ИСХОДНОЕ ПОЛОЖЕНИЕ",
            command=self.home_position,
            font=('Arial', 12, 'bold'),
            height=2,
            bg='lightgray'
        ).pack(fill=tk.X, padx=5, pady=10)

    def update_ports(self):
        """Обновляет список доступных COM-портов"""
        ports = [p.device for p in serial.tools.list_ports.comports()]
        self.port_combobox['values'] = ports
        if ports:
            self.port_var.set(ports[0])

    def toggle_connection(self):
        """Переключает состояние подключения"""
        if self.connect_button.cget("text") == "Подключиться":
            if port := self.port_var.get():
                try:
                    self.serial_connection = serial.Serial(port, baudrate=9600, timeout=1)
                    self.connect_button.config(text="Отключиться")
                    threading.Thread(target=self.read_serial_data, daemon=True).start()
                except SerialException as e:
                    print(f"Ошибка подключения: {e}")
        else:
            if self.serial_connection:
                self.serial_connection.close()
                self.serial_connection = None
            self.connect_button.config(text="Подключиться")

    def read_serial_data(self):
        """Чтение данных с последовательного порта"""
        while self.serial_connection and self.serial_connection.is_open:
            try:
                line = self.serial_connection.readline().decode('utf-8').strip()
                if line:
                    print(f"Получено с Arduino: {line}")
                    # Здесь можно добавить обработку полученных данных
            except Exception as e:
                print(f"Ошибка чтения данных: {e}")
                break

    def home_position(self):
        """Отправка команды возврата в исходное положение"""
        self.controller.send_command("В исходное положение")