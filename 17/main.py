import tkinter as tk
from tkinter import ttk
import threading
import time
import json
from left_frame import LeftFrame
from center_frame import CenterFrame
from right_frame import RightFrame
from manipulator import ManipulatorController
from serial_settings import SerialManager


class SerialApp:
    def __init__(self, root):
        self.root = root
        self._setup_main_window()

        # Инициализация менеджера подключений (Singleton)
        self.serial_manager = SerialManager()

        # Создание контроллера манипулятора
        self.manipulator = ManipulatorController()

        # Инициализация фреймов
        self._create_frames()

        # Настройка управления программой
        self._setup_program_controls()

        # Состояние выполнения программы
        self.program_running = False
        self.program_paused = False
        self.current_step = 0

    def _setup_main_window(self):
        """Настройка главного окна"""
        self.root.title("Skara robot")
        self.root.geometry("1280x700")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)  # Привязка обработчика закрытия

    def _create_frames(self):
        """Создание и размещение фреймов"""
        # Левый фрейм - управление подключением и датчиками
        self.left_frame = LeftFrame(self.root, self)
        self.left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

        # Центральный фрейм - управление программой
        self.center_frame = CenterFrame(self.root, self)
        self.center_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Правый фрейм - ручное управление
        self.right_frame = RightFrame(self.root, self)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)

    def _setup_program_controls(self):
        """Настройка кнопок управления программой"""
        controls = {
            'start_button': self.start_program,
            'pause_button': self.pause_program,
            'restart_button': self.restart_program,
            'stop_button': self.stop_program
        }

        for control, command in controls.items():
            getattr(self.center_frame, control).config(command=command)

    def on_close(self):
        """Обработчик закрытия приложения"""
        if getattr(self, '_is_closing', False):
            return

        self._is_closing = True

        try:
            # 1. Выключаем все устройства
            try:
                if hasattr(self, 'serial_manager') and self.serial_manager.is_connected:
                    self.serial_manager.send_command("x\n")
                    time.sleep(0.1)
            except:
                pass

            # 2. Безопасно завершаем работу фреймов
            if hasattr(self, 'left_frame'):
                self.left_frame.safe_shutdown()

            # 3. Закрываем окно
            if hasattr(self, 'root') and self.root.winfo_exists():
                self.root.after(100, self.root.destroy)
        except Exception as e:
            print(f"Ошибка при закрытии: {e}")
            if hasattr(self, 'root') and self.root.winfo_exists():
                self.root.after(100, self.root.destroy)

    def process_sensor_message(self, message: str):
        """Перенаправляем сообщения датчиков в left_frame"""
        self.left_frame.process_incoming_data(message)

    def start_program(self):
        """Запуск программы"""
        if not self.program_running:
            self.program_running = True
            self.program_paused = False
            self.current_step = 0
            threading.Thread(target=self._run_program, daemon=True).start()
            print("Программа запущена")

    def pause_program(self):
        """Пауза программы"""
        if self.program_running and not self.program_paused:
            self.program_paused = True
            print("Программа на паузе")

    def restart_program(self):
        """Перезапуск программы"""
        self.stop_program()
        self.start_program()
        print("Программа перезапущена")

    def stop_program(self):
        """Остановка программы"""
        if self.program_running:
            self.program_running = False
            self.program_paused = False
            self.current_step = 0
            self.center_frame.current_step.set("0")
            print("Программа остановлена")

    def _run_program(self):
        """Основной цикл выполнения программы"""
        steps = self.center_frame.steps_commands.get_steps()
        total_steps = len(steps)

        while self.program_running and self.current_step < total_steps:
            if self.program_paused:
                time.sleep(0.1)
                continue

            step_num = sorted(steps.keys())[self.current_step]
            command = steps[step_num]

            # Обновляем интерфейс
            self.root.after(0, self._update_ui_step, step_num)

            # Отправляем команду
            try:
                self.manipulator.execute_command(command)

                # Ожидаем подтверждения от Arduino
                if not self._wait_for_arduino_confirmation(step_num):
                    print(f"Таймаут выполнения шага {step_num}")
                    self.stop_program()
                    break

                # Обновляем координаты (имитация)
                self._update_coordinates_after_step(command)

            except Exception as e:
                print(f"Ошибка выполнения шага: {e}")
                self.stop_program()
                break

            self.current_step += 1
            time.sleep(0.5)  # Задержка между шагами

        if self.current_step >= total_steps:
            print("Программа выполнена полностью")
            self.program_running = False
            self.center_frame.current_step.set("Готово")

    def _wait_for_arduino_confirmation(self, step_num, timeout=2.0):
        """Ожидание подтверждения от Arduino"""
        if not self.serial_manager.is_connected:
            print("Режим отладки - подтверждение не требуется")
            return True

        start_time = time.time()
        while time.time() - start_time < timeout:
            data = self.serial_manager.read_data()
            if data:
                try:
                    response = json.loads(data)
                    if self._validate_response(response, step_num):
                        return True
                except json.JSONDecodeError:
                    continue
            time.sleep(0.01)

        print("Таймаут ожидания подтверждения")
        return False

    def send_pneumatic_command(self, valve1: bool, valve2: bool):
        """Отправляет команду управления пневматикой на Arduino"""
        if valve1 and valve2:
            command = 'e\n'  # Оба клапана (Присоска)
        elif not valve1 and valve2:
            command = 'r\n'  # Только D6 (Дозатор)
        else:
            command = 'x\n'  # Выключить все

        if hasattr(self, 'serial_manager'):
            self.serial_manager.send_raw_command(command)

    def _validate_response(self, data, step_num):
        """Проверка валидности ответа от Arduino"""
        if str(data.get("step", 0)) == str(step_num):
            if data.get("status") == "done":
                print(f"Подтверждение для шага {step_num}")
                return True
            elif "error" in data:
                print(f"Ошибка Arduino: {data}")
        return False

    def _update_ui_step(self, step_num):
        """Обновление UI в главном потоке"""
        self.center_frame.current_step.set(str(step_num))

    def _update_coordinates_after_step(self, command):
        """Имитация обновления координат после выполнения шага"""
        coords = self.center_frame.current_coords
        current_x = float(coords["X"].get())
        current_y = float(coords["Y"].get())
        current_z = float(coords["Z"].get())

        # Простая логика обновления координат для демонстрации
        if "RUKA" in command:
            current_x += 10
        if "PLECHO" in command:
            current_y += 10
        if "LIFT" in command:
            current_z += 5 if "LIFT" in command and float(command.split(":")[1]) > 0 else -5

        self.update_current_coords(current_x, current_y, current_z)

    def update_current_coords(self, x, y, z):
        """Обновление текущих координат в интерфейсе"""
        self.center_frame.current_coords["X"].set(f"{x:.2f}")
        self.center_frame.current_coords["Y"].set(f"{y:.2f}")
        self.center_frame.current_coords["Z"].set(f"{z:.2f}")

    def update_lamp_state(self, lamp, state):
        """Обновление состояния индикаторов"""
        if lamp in self.center_frame.lamp_states:
            self.center_frame.lamp_states[lamp].set(state)


def center_window(root):
    """Центрирование окна на экране"""
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f"+{x}+{y}")


if __name__ == "__main__":
    root = tk.Tk()
    app = SerialApp(root)
    center_window(root)
    root.mainloop()