import tkinter as tk
from tkinter import ttk
import threading
import time
from serial_settings import SerialManager


class RightFrame(ttk.LabelFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, text="Ручное управление", padding=10)
        self.controller = controller
        self.serial_manager = SerialManager()

        # Состояния моторов
        self.motor_states = {
            0: {"active": False, "direction": None},  # Верхний
            1: {"active": False, "direction": None},  # Нижний
            2: {"active": False, "direction": None},  # Руки
            3: {"active": False, "direction": None}  # Кисти
        }

        # Пневматика
        self.pneumatic_states = {
            "Присоска": False,
            "Дозатор": False
        }

        # Флаг работы потока
        self.running = True
        self.command_lock = threading.Lock()

        # Инициализация интерфейса
        self.setup_ui()

        # Запуск потока отправки команд
        self.command_thread = threading.Thread(
            target=self._command_sender_loop,
            daemon=True
        )
        self.command_thread.start()

    def setup_ui(self):
        """Настройка интерфейса"""
        # Фрейм управления моторами
        motor_frame = ttk.LabelFrame(self, text="Двигатели", padding=10)
        motor_frame.pack(fill=tk.X, padx=5, pady=5)

        # Стиль для кнопок
        style = ttk.Style()
        style.configure('Motor.TButton', width=3, font=('Arial', 10))

        # Моторы
        motors = [
            ("Верхний", 0),
            ("Нижний", 1),
            ("Руки", 2),
            ("Кисти", 3)
        ]

        for name, motor_id in motors:
            row = ttk.Frame(motor_frame)
            row.pack(fill=tk.X, pady=2)

            ttk.Label(row, text=name, width=8).pack(side=tk.LEFT)

            # Кнопка "Назад"
            btn_left = ttk.Button(row, text="←", style='Motor.TButton')
            btn_left.pack(side=tk.LEFT, padx=2)
            btn_left.bind(
                '<ButtonPress>',
                lambda e, m=motor_id: self._motor_start(m, "backward")
            )
            btn_left.bind(
                '<ButtonRelease>',
                lambda e, m=motor_id: self._motor_stop(m)
            )

            # Кнопка "Вперёд"
            btn_right = ttk.Button(row, text="→", style='Motor.TButton')
            btn_right.pack(side=tk.LEFT, padx=2)
            btn_right.bind(
                '<ButtonPress>',
                lambda e, m=motor_id: self._motor_start(m, "forward")
            )
            btn_right.bind(
                '<ButtonRelease>',
                lambda e, m=motor_id: self._motor_stop(m)
            )

        # Фрейм пневматики
        pneumatic_frame = ttk.LabelFrame(self, text="Пневматика", padding=10)
        pneumatic_frame.pack(fill=tk.X, padx=5, pady=5)

        # Кнопка присоски
        self.suction_btn = tk.Button(
            pneumatic_frame,
            text="Присоска ВКЛ",
            command=lambda: self._toggle_pneumatic("Присоска"),
            bg='lightgray',
            height=1,
            font=('Arial', 10)
        )
        self.suction_btn.pack(fill=tk.X, pady=2)

        # Кнопка дозатора
        self.dispenser_btn = tk.Button(
            pneumatic_frame,
            text="Дозатор ВКЛ",
            command=lambda: self._toggle_pneumatic("Дозатор"),
            bg='lightgray',
            height=1,
            font=('Arial', 10)
        )
        self.dispenser_btn.pack(fill=tk.X, pady=2)

    def _motor_start(self, motor_id, direction):
        """Обработчик нажатия кнопки мотора"""
        with self.command_lock:
            self.motor_states[motor_id]["active"] = True
            self.motor_states[motor_id]["direction"] = direction

    def _motor_stop(self, motor_id):
        """Обработчик отпускания кнопки мотора"""
        with self.command_lock:
            self.motor_states[motor_id]["active"] = False
            self._send_command(f"m{motor_id}0\n")  # Команда остановки

    def _toggle_pneumatic(self, device):
        """Переключение состояния пневматики"""
        new_state = not self.pneumatic_states[device]

        if device == "Присоска":
            self.pneumatic_states["Присоска"] = new_state
            self.pneumatic_states["Дозатор"] = False
            self._send_command("e\n" if new_state else "x\n")
        else:
            self.pneumatic_states["Дозатор"] = new_state
            self.pneumatic_states["Присоска"] = False
            self._send_command("r\n" if new_state else "x\n")

        # Обновление кнопок
        self.suction_btn.config(
            text="Присоска ВЫКЛ" if self.pneumatic_states["Присоска"] else "Присоска ВКЛ",
            bg='lightblue' if self.pneumatic_states["Присоска"] else 'lightgray'
        )
        self.dispenser_btn.config(
            text="Дозатор ВЫКЛ" if self.pneumatic_states["Дозатор"] else "Дозатор ВКЛ",
            bg='lightblue' if self.pneumatic_states["Дозатор"] else 'lightgray'
        )

    def _send_command(self, command):
        """Безопасная отправка команды"""
        if hasattr(self.controller, 'serial_manager') and self.serial_manager.is_connected:
            try:
                self.serial_manager._connection.write(command.encode())
                self.serial_manager._connection.flush()
            except Exception as e:
                print(f"Ошибка отправки команды: {e}")

    def _command_sender_loop(self):
        """Цикл отправки команд для активных моторов"""
        while self.running:
            with self.command_lock:
                for motor_id, state in self.motor_states.items():
                    if state["active"]:
                        direction_code = "1" if state["direction"] == "forward" else "2"
                        self._send_command(f"m{motor_id}{direction_code}\n")

            time.sleep(0.1)  # Интервал 20 мс (50 команд/сек)

    def cleanup(self):
        """Корректное завершение работы"""
        self.running = False

        # Остановка всех моторов
        for motor_id in range(4):
            self._send_command(f"m{motor_id}0\n")

        # Выключение пневматики
        self._send_command("x\n")

        # Ожидание завершения потока
        if hasattr(self, 'command_thread'):
            self.command_thread.join(timeout=0.5)