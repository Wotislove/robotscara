import tkinter as tk
from tkinter import ttk
import threading
import time
from serial_settings import SerialManager


class LeftFrame(ttk.LabelFrame):
    def __init__(self, parent, controller):
        """
        Левая панель управления с подключением и индикацией датчиков
        """
        super().__init__(parent, text="Общее", padding=10)
        self.controller = controller
        self.serial_manager = SerialManager()
        self.reading_active = False
        self._shutdown_lock = threading.Lock()

        # Состояние датчиков
        self.sensors = [
            "Концевик верхний",
            "Концевик нижний",
            "Концевик руки",
            "Концевик кисти"
        ]
        self.sensor_states = {sensor: False for sensor in self.sensors}
        self.sensor_labels = {}

        # Элементы управления подключением
        self.port_var = tk.StringVar()
        self.connect_button = None
        self.connection_indicator = None

        # Инициализация интерфейса
        self.setup_ui()

        # Запуск потока для чтения данных
        self.start_reading_thread()

    def setup_ui(self):
        """Настройка всех элементов интерфейса"""
        # Фрейм подключения
        conn_frame = ttk.LabelFrame(self, text="Настройки подключения", padding=10)
        conn_frame.pack(fill=tk.X, padx=5, pady=5)

        # Выбор COM-порта
        self.port_combobox = ttk.Combobox(
            conn_frame,
            textvariable=self.port_var,
            state='readonly',
            width=15
        )
        self.update_ports()
        self.port_combobox.pack(fill=tk.X, pady=(0, 5))

        # Кнопки управления
        btn_frame = ttk.Frame(conn_frame)
        btn_frame.pack(fill=tk.X)

        ttk.Button(
            btn_frame,
            text="Обновить",
            command=self.update_ports,
            width=10
        ).pack(side=tk.LEFT, padx=2)

        self.connect_button = ttk.Button(
            btn_frame,
            text="Подключиться",
            command=self.toggle_connection,
            width=10
        )
        self.connect_button.pack(side=tk.LEFT, padx=2)

        self.connection_indicator = ttk.Label(
            btn_frame,
            text="●",
            font=('Arial', 14),
            foreground='red'
        )
        self.connection_indicator.pack(side=tk.LEFT, padx=5)

        # Индикаторы датчиков
        sensors_frame = ttk.LabelFrame(self, text="Состояние датчиков", padding=10)
        sensors_frame.pack(fill=tk.X, padx=5, pady=5)

        for sensor in self.sensors:
            row = ttk.Frame(sensors_frame)
            row.pack(fill=tk.X, pady=2)

            # Графический индикатор
            indicator = ttk.Label(row, text="⬤", font=('Arial', 14), foreground='red')
            indicator.pack(side=tk.LEFT, padx=5)

            # Название датчика
            ttk.Label(row, text=sensor, width=15).pack(side=tk.LEFT)

            # Текстовый статус
            status_label = ttk.Label(row, text="Выкл")
            status_label.pack(side=tk.RIGHT)

            self.sensor_labels[sensor] = {
                'indicator': indicator,
                'status': status_label
            }

        # Кнопка возврата в исходное положение
        ttk.Button(
            self,
            text="ИСХОДНОЕ ПОЛОЖЕНИЕ",
            command=self.home_position,
            style='Emergency.TButton'
        ).pack(fill=tk.X, padx=5, pady=10)

        # Стиль для кнопки
        self.style = ttk.Style()
        self.style.configure('Emergency.TButton',
                             font=('Arial', 12, 'bold'),
                             background='lightgray',
                             padding=10)

    def home_position(self):
        """Команда возврата в исходное положение"""
        if self.serial_manager.is_connected:
            command = {
                "command": "HOME",
                "timeout": 10000,
                "priority": 1
            }
            self.serial_manager.send_command(command)
            print("Запуск процедуры HOME...")
        else:
            print("Ошибка: нет подключения к Arduino!")

    def update_ports(self):
        """Обновление списка доступных COM-портов"""
        ports = self.serial_manager.settings.get_available_ports()
        self.port_combobox['values'] = ports
        if ports:
            self.port_var.set(ports[0])

    def toggle_connection(self):
        """Переключение состояния подключения"""
        if not self.serial_manager.is_connected:
            port = self.port_var.get()
            if port and self.serial_manager.connect(port):
                self.connect_button.config(text="Отключиться")
                self.connection_indicator.config(foreground='green')
        else:
            self.serial_manager.disconnect()
            self.connect_button.config(text="Подключиться")
            self.connection_indicator.config(foreground='red')
            print("Отключено")

    def start_reading_thread(self):
        """Запуск потока для чтения данных с датчиков"""
        self.reading_active = True

        def reading_loop():
            while self.reading_active:
                try:
                    if self.serial_manager.is_connected:
                        messages = self.serial_manager.get_sensor_messages()
                        for message in messages:
                            self.process_incoming_data(message)
                            self.controller.root.after(0, self.update_sensor_displays)
                except Exception as e:
                    print(f"Ошибка в потоке чтения: {e}")
                time.sleep(0.1)

        self.reading_thread = threading.Thread(
            target=reading_loop,
            daemon=True
        )
        self.reading_thread.start()

    def process_incoming_data(self, data: str):
        """Обработка входящих данных от датчиков"""
        try:
            if data.startswith("SENSOR:"):
                parts = data.split(":")
                if len(parts) >= 3:
                    sensor_type = parts[1].strip().lower()
                    state = parts[2].strip() == "1"

                    for sensor_name in self.sensors:
                        if sensor_type in sensor_name.lower():
                            self.sensor_states[sensor_name] = state
                            break
        except Exception as e:
            print(f"Ошибка обработки данных датчика: {e}")

    def update_sensor_displays(self):
        """Обновление всех индикаторов датчиков"""
        for sensor_name in self.sensors:
            state = self.sensor_states.get(sensor_name, False)
            color = "green" if state else "red"
            text = "Вкл" if state else "Выкл"

            if sensor_name in self.sensor_labels:
                self.sensor_labels[sensor_name]['indicator'].config(foreground=color)
                self.sensor_labels[sensor_name]['status'].config(text=text)

    def safe_shutdown(self):
        """Безопасное завершение работы фрейма"""
        with self._shutdown_lock:
            if not self.reading_active:
                return

            self.reading_active = False

            # Остановка потока с таймаутом
            if hasattr(self, 'reading_thread'):
                self.reading_thread.join(timeout=0.5)
                if self.reading_thread.is_alive():
                    print("Предупреждение: поток чтения не завершился вовремя")

            # Закрытие соединения
            try:
                if self.serial_manager.is_connected:
                    # Отправляем команду выключения перед закрытием
                    self.serial_manager.send_command("x\n")  # Выключить все
                    time.sleep(0.1)
                    self.serial_manager.disconnect()
            except Exception as e:
                print(f"Ошибка при завершении соединения: {e}")

    def __del__(self):
        """Деструктор для дополнительной безопасности"""
        self.safe_shutdown()