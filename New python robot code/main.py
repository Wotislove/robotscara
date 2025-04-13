import tkinter as tk
from tkinter import ttk
import threading
import time
from left_frame import LeftFrame
from center_frame import CenterFrame
from right_frame import RightFrame
from manipulator import ManipulatorController


class SerialApp:
    """
    Главный класс приложения для управления роботом Skara.
    Создает графический интерфейс и управляет выполнением программы.
    """

    def __init__(self, root):
        """
        Инициализация главного окна приложения.

        Args:
            root: Главное окно Tkinter
        """
        self.root = root
        self._setup_main_window()  # Настройка основного окна
        self._init_manipulator()  # Инициализация контроллера робота
        self._create_frames()  # Создание интерфейсных фреймов
        self._setup_program_controls()  # Настройка управления программой

        # Состояние выполнения программы
        self.program_running = False
        self.program_paused = False
        self.current_step = 0

    def _setup_main_window(self):
        """Настраивает параметры главного окна"""
        self.root.title("Skara robot")  # Заголовок окна
        self.root.geometry("1280x700")  # Размер окна

    def _init_manipulator(self):
        """Инициализирует контроллер манипулятора"""
        self.manipulator = ManipulatorController()  # Создаем контроллер робота
        self.port = None  # COM-порт (будет установлен позже)

    def _create_frames(self):
        """Создает и размещает основные элементы интерфейса"""
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
        """Привязывает кнопки управления программой к методам"""
        controls = {
            'start_button': self.start_program,
            'pause_button': self.pause_program,
            'restart_button': self.restart_program,
            'stop_button': self.stop_program
        }

        for control, command in controls.items():
            getattr(self.center_frame, control).config(command=command)

    def send_command(self, command):
        """
        Отправляет команду на выполнение манипулятору.

        Args:
            command (str): Команда для выполнения
        """
        self.manipulator.execute_command(command)

    def start_program(self):
        """Запускает выполнение программы"""
        if not self.program_running:
            self.program_running = True
            self.program_paused = False
            self.current_step = 0
            # Запускаем в отдельном потоке, чтобы не блокировать интерфейс
            threading.Thread(target=self._run_program, daemon=True).start()

    def pause_program(self):
        """Ставит программу на паузу"""
        if self.program_running and not self.program_paused:
            self.program_paused = True

    def restart_program(self):
        """Перезапускает программу с начала"""
        self.stop_program()
        self.start_program()

    def stop_program(self):
        """Полностью останавливает выполнение программы"""
        self.program_running = False
        self.program_paused = False
        self.current_step = 0
        self.center_frame.current_step.set("0")  # Сбрасываем отображение шага

    def _run_program(self):
        """
        Основной цикл выполнения программы.
        Выполняет команды последовательно с заданным интервалом.
        """
        steps = self.center_frame.steps_commands.get_steps()
        total_steps = len(steps)

        while self.program_running and self.current_step < total_steps:
            if self.program_paused:
                time.sleep(0.1)  # При паузе просто ждем
                continue

            # Получаем текущую команду
            step_num = sorted(steps.keys())[self.current_step]
            command = steps[step_num]

            # Выполняем команду
            self.manipulator.execute_command(command)

            # Обновляем интерфейс
            self.center_frame.current_step.set(str(step_num))

            # Переходим к следующему шагу
            self.current_step += 1

            # Задержка между командами для стабильности работы
            time.sleep(0.5)

        # Завершение программы
        self.program_running = False
        self.center_frame.current_step.set("0")

    def update_current_coords(self, x, y, z):
        """
        Обновляет отображение текущих координат в интерфейсе.

        Args:
            x (float): Координата X
            y (float): Координата Y
            z (float): Координата Z
        """
        coords = {'X': x, 'Y': y, 'Z': z}
        for axis, value in coords.items():
            self.center_frame.current_coords[axis].set(f"{value:.2f}")

    def update_lamp_state(self, lamp, state):
        """
        Обновляет состояние индикатора (лампочки) в интерфейсе.

        Args:
            lamp (str): Название индикатора ('Вакуум', 'Доза', 'Магазин')
            state (bool): Состояние (True/False)
        """
        if lamp in self.center_frame.lamp_states:
            self.center_frame.lamp_states[lamp].set(state)


def center_window(root):
    """Центрирует окно на экране"""
    root.update_idletasks()  # Обновляем информацию о размерах окна

    # Получаем размеры окна и экрана
    window_width = root.winfo_width()
    window_height = root.winfo_height()
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    # Вычисляем позицию для центрирования
    x = (screen_width // 2) - (window_width // 2)
    y = (screen_height // 2) - (window_height // 2)

    # Устанавливаем новую позицию окна
    root.geometry(f"+{x}+{y}")


if __name__ == "__main__":
    # Создаем главное окно
    root = tk.Tk()

    # Инициализируем приложение
    app = SerialApp(root)

    # Центрируем окно на экране
    center_window(root)

    # Запускаем главный цикл обработки событий
    root.mainloop()