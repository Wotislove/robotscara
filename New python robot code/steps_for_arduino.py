import serial
import time
from serial import SerialException


class ArduinoStepSender:
    """
    Класс для отправки команд на Arduino.
    Поддерживает режим отладки без реального подключения.
    """

    def __init__(self, port=None, baudrate=9600, debug_mode=True):
        """
        Инициализация подключения к Arduino.

        Args:
            port (str): COM-порт Arduino (например, 'COM3')
            baudrate (int): Скорость передачи данных (по умолчанию 9600)
            debug_mode (bool): Режим отладки (True - эмуляция, False - реальное подключение)
        """
        self.port = port  # Порт подключения
        self.baudrate = baudrate  # Скорость соединения
        self.connection = None  # Объект соединения
        self.debug_mode = debug_mode  # Режим отладки

        # Автоподключение при выключенном режиме отладки
        if not self.debug_mode and self.port:
            self.connect()

    def connect(self):
        """
        Устанавливает соединение с Arduino.

        Returns:
            bool: True если подключение успешно, False при ошибке
        """
        if self.debug_mode:
            print("[DEBUG] Режим отладки - подключение не требуется")
            return True

        try:
            # Открываем последовательное соединение
            self.connection = serial.Serial(self.port, self.baudrate, timeout=1)
            time.sleep(2)  # Даем время Arduino на инициализацию
            print(f"Успешное подключение к Arduino на {self.port}")
            return True
        except Exception as e:
            print(f"Ошибка подключения: {e}")
            self.connection = None
            return False

    def send_step(self, **kwargs):
        """
        Отправляет команду на Arduino.

        Args:
            **kwargs: Параметры команды (например, ruka=100, plecho=50)

        Returns:
            bool: True если команда отправлена успешно, False при ошибке
        """
        # Режим отладки - выводим команду в консоль
        if self.debug_mode:
            print("\n" + "=" * 40)
            print("[DEBUG] Эмуляция отправки команды:")
            for key, value in kwargs.items():
                print(f"  {key.upper()}: {value}")
            print("=" * 40 + "\n")
            return True

        # Проверяем подключение
        if not self.connection or not self.connection.is_open:
            if not self.connect():  # Пытаемся переподключиться
                print("Ошибка: подключение к Arduino не установлено!")
                return False

        # Формируем команду из параметров
        command_parts = []
        for key, value in kwargs.items():
            if value is not None:
                # Форматируем значение
                if isinstance(value, str):
                    command_parts.append(f"{key.upper()}:{value}")
                else:
                    command_parts.append(f"{key.upper()}:{float(value):.2f}")

        # Проверяем что есть что отправлять
        if not command_parts:
            print("Ошибка: пустая команда")
            return False

        # Собираем полную команду
        command = "|".join(command_parts) + "\n"

        # Отправляем команду
        try:
            self.connection.write(command.encode('utf-8'))
            print(f"Отправлена команда: {command.strip()}")
            return True
        except SerialException as e:
            print(f"Ошибка отправки: {e}")
            self.connection.close()
            self.connection = None
            return False

    def close(self):
        """Закрывает соединение с Arduino."""
        if not self.debug_mode and self.connection and self.connection.is_open:
            self.connection.close()
            print("Соединение с Arduino закрыто")
        elif self.debug_mode:
            print("[DEBUG] Эмуляция: соединение закрыто")