import serial
import serial.tools.list_ports
import threading
import time
import json
from typing import Optional, List, Dict, Any, Union
from queue import Queue


class SerialSettings:
    """Класс для хранения настроек последовательного порта"""

    def __init__(self):
        self.baudrate = 9600
        self.timeout = 1
        self.write_timeout = 1
        self.port = None

    def get_available_ports(self) -> List[str]:
        """Возвращает список доступных COM-портов"""
        return [port.device for port in serial.tools.list_ports.comports()]

    def validate_port(self, port: str) -> bool:
        """Проверяет, существует ли указанный порт"""
        return port in self.get_available_ports()


class SerialManager:
    """Класс для управления подключением к Arduino с улучшенной обработкой сообщений"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Инициализация менеджера с очередями сообщений"""
        self.settings = SerialSettings()
        self._connection = None
        self._monitoring_thread = None
        self._monitoring_thread_running = False
        self._last_received_data = ""

        # Очереди для разных типов сообщений
        self._sensor_messages = Queue()  # Для сообщений от датчиков
        self._other_messages = Queue()  # Для прочих сообщений
        self._command_queue = []  # Для отправки команд

        # Блокировки для потокобезопасности
        self._sensor_lock = threading.Lock()
        self._message_lock = threading.Lock()
        self._command_lock = threading.Lock()

    @property
    def is_connected(self) -> bool:
        """Проверяет, активно ли подключение"""
        return self._connection is not None and self._connection.is_open

    def connect(self, port: str) -> bool:
        """Устанавливает соединение с Arduino и начинает мониторинг сообщений"""
        if self.is_connected:
            self.disconnect()

        try:
            self._connection = serial.Serial(
                port=port,
                baudrate=self.settings.baudrate,
                timeout=0.5,
                write_timeout=self.settings.write_timeout
            )

            # Очистка буферов
            self._connection.reset_input_buffer()
            self._connection.reset_output_buffer()

            # Запуск мониторинга сообщений
            self._start_monitoring_thread()

            # Проверка связи
            self._connection.write(b"\n")
            time.sleep(0.1)

            # Ожидание ответа от Arduino
            start_time = time.time()
            while time.time() - start_time < 2:
                if self._connection.in_waiting > 0:
                    data = self._connection.readline().decode('utf-8', errors='replace').strip()
                    if data and ("ready" in data.lower() or "готов" in data.lower()):
                        break

            self._connection.timeout = self.settings.timeout
            print(f"Успешное подключение к {port}")
            return True

        except serial.SerialException as e:
            print(f"Ошибка подключения: {e}")
            return False

    def _start_monitoring_thread(self):
        """Запускает поток для постоянного мониторинга сообщений"""

        def monitoring_loop():
            buffer = ""
            while self._monitoring_thread_running and self.is_connected:
                try:
                    # Чтение всех доступных данных
                    if self._connection.in_waiting > 0:
                        data = self._connection.read(self._connection.in_waiting).decode('utf-8', errors='replace')
                        buffer += data

                        # Обработка полных сообщений (разделенных \n)
                        while '\n' in buffer:
                            line, buffer = buffer.split('\n', 1)
                            line = line.strip()
                            if line:
                                # Раздельная обработка сенсорных и прочих сообщений
                                if line.startswith("SENSOR:"):
                                    with self._sensor_lock:
                                        self._sensor_messages.put(line)
                                else:
                                    with self._message_lock:
                                        self._other_messages.put(line)
                                        self._last_received_data = line
                except Exception as e:
                    print(f"Ошибка чтения в потоке мониторинга: {e}")
                    break
                time.sleep(0.01)

        self._stop_monitoring_thread()
        self._monitoring_thread_running = True
        self._monitoring_thread = threading.Thread(
            target=monitoring_loop,
            daemon=True
        )
        self._monitoring_thread.start()

    def _stop_monitoring_thread(self):
        """Останавливает поток мониторинга"""
        if self._monitoring_thread is not None:
            self._monitoring_thread_running = False
            self._monitoring_thread.join(timeout=0.5)
            self._monitoring_thread = None

    def get_sensor_messages(self) -> List[str]:
        """Возвращает все накопленные сообщения от датчиков"""
        messages = []
        while not self._sensor_messages.empty():
            messages.append(self._sensor_messages.get())
        return messages

    def get_other_messages(self) -> List[str]:
        """Возвращает прочие накопленные сообщения"""
        messages = []
        while not self._other_messages.empty():
            messages.append(self._other_messages.get())
        return messages

    def send_command(self, command: Union[str, Dict]) -> bool:
        """Отправляет команду на Arduino (строку или JSON)"""
        if not self.is_connected:
            print("Ошибка: Нет подключения!")
            return False

        try:
            if isinstance(command, dict):
                full_command = json.dumps(command) + "\n"
            else:
                full_command = command + "\n" if not command.endswith("\n") else command

            with self._command_lock:
                self._connection.write(full_command.encode('utf-8'))
                self._connection.flush()

            print(f"[Отправлено] {full_command.strip()}")
            return True
        except serial.SerialException as e:
            print(f"Ошибка отправки команды: {e}")
            return False

    def disconnect(self):
        """Закрывает соединение с Arduino"""
        self._stop_monitoring_thread()
        if self.is_connected:
            self._connection.close()
        self._connection = None
        print("Отключено от COM-порта")

    def read_data(self) -> Optional[str]:
        """Читает данные из порта (устаревший метод, лучше использовать get_sensor_messages)"""
        if not self.is_connected:
            return None

        try:
            if self._connection.in_waiting > 0:
                line = self._connection.readline().decode('utf-8').strip()
                return line if line else None
        except Exception as e:
            print(f"Ошибка чтения: {e}")
        return None

    def get_last_received_data(self) -> str:
        """Возвращает последние полученные данные"""
        return self._last_received_data

    def send_raw_command(self, command: str) -> bool:
        """Отправляет сырую команду без JSON-форматирования (для обратной совместимости)"""
        return self.send_command(command)

    def clear_buffers(self):
        """Очищает буферы ввода/вывода"""
        if self.is_connected:
            self._connection.reset_input_buffer()
            self._connection.reset_output_buffer()