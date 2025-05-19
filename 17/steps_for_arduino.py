import json
import time
from typing import Dict, Optional, Union
from serial_settings import SerialManager


class ArduinoStepSender:


    def __init__(self, debug_mode: bool = False):
        """
        Инициализация отправителя команд.

        """
        self.serial_manager = SerialManager()  # Используем единый менеджер подключений
        self.debug_mode = debug_mode
        self.step_counter = 1
        self.auto_increment = True
        self._in_rubbing = False
        self._command_buffer = []
        self._batch_mode = False
        self._batch_size = 10
        self._last_error = None

    def enable_batch_mode(self, batch_size: int = 10):
        """Активирует режим пакетной отправки команд"""
        self._batch_mode = True
        self._batch_size = max(1, batch_size)

    def disable_batch_mode(self):
        """Деактивирует режим пакетной отправки команд"""
        self._flush_buffer()
        self._batch_mode = False

    def send_command(self, **kwargs) -> Optional[Dict]:
        """Основной метод отправки команды (обратная совместимость)"""
        return self._process_command(**kwargs)

    def send_step(self, **kwargs) -> Optional[Dict]:
        """Алиас для send_command с явным указанием шага"""
        return self._process_command(**kwargs)

    def _process_command(self, **kwargs) -> Optional[Dict]:

        # Формирование JSON-структуры команды
        command = {
            "step": self.step_counter,
            "data": self._prepare_command_data(**kwargs)
        }

        # Сохранение в историю команд
        self._save_to_history(command)

        # Отправка или буферизация
        if not self._send_or_buffer_command(command):
            return None

        # Автоинкремент счетчика
        if not self._in_rubbing and self.auto_increment:
            self.step_counter += 1

        return command

    def _prepare_command_data(self, **kwargs) -> Dict:
        """Подготавливает данные команды, преобразуя ключи в верхний регистр"""
        data = {}
        for key, value in kwargs.items():
            if value is not None:
                key_upper = key.upper()
                if isinstance(value, (int, float)):
                    data[key_upper] = round(float(value), 2)
                else:
                    data[key_upper] = value
        return data

    def _save_to_history(self, command: Dict):
        """Сохраняет команду во внутреннем журнале"""
        if not hasattr(self, '_command_history'):
            self._command_history = []
        self._command_history.append(command)

    def _send_or_buffer_command(self, command: Dict) -> bool:
        """Отправляет команду напрямую или добавляет в буфер"""
        if self._batch_mode:
            self._command_buffer.append(command)
            if len(self._command_buffer) >= self._batch_size:
                return self._flush_buffer()
            return True
        else:
            return self._send_immediately(command)

    def _send_immediately(self, command: Dict) -> bool:
        """Немедленная отправка одной команды"""
        if self.debug_mode:
            print("[DEBUG] Command:", json.dumps(command, indent=2))
            return True

        if not self.serial_manager.is_connected:
            self._last_error = "No active connection"
            print(f"[ERROR] {self._last_error}")
            return False

        try:
            success = self.serial_manager.send_command(command)
            if not success:
                self._last_error = "Send command failed"
            return success
        except Exception as e:
            self._last_error = str(e)
            print(f"[ERROR] {self._last_error}")
            return False

    def _flush_buffer(self) -> bool:
        """Отправка всех команд из буфера"""
        if not self._command_buffer:
            return True

        if self.debug_mode:
            print("[DEBUG] Batch commands:")
            for cmd in self._command_buffer:
                print(json.dumps(cmd, indent=2))
            self._command_buffer.clear()
            return True

        if not self.serial_manager.is_connected:
            self._last_error = "No active connection for batch"
            print(f"[ERROR] {self._last_error}")
            return False

        try:
            batch = {
                "batch": True,
                "commands": self._command_buffer.copy()
            }
            success = self.serial_manager.send_command(batch)
            if success:
                self._command_buffer.clear()
            else:
                self._last_error = "Batch send failed"
            return success
        except Exception as e:
            self._last_error = str(e)
            print(f"[ERROR] {self._last_error}")
            return False

    def send_rubbing_step(self, step_num: int, value: float) -> Optional[Dict]:

        command = {
            "step": f"{self.step_counter}.{step_num}",
            "data": {"RUKA": round(float(value), 2)}
        }

        if not self._send_immediately(command):
            return None

        if self.debug_mode:
            print(json.dumps(command, indent=2))
        return command

    def start_rubbing(self):
        """Активирует режим притирки"""
        self._in_rubbing = True
        self.auto_increment = False

    def end_rubbing(self):
        """Завершает режим притирки"""
        self._in_rubbing = False
        self.auto_increment = True
        self.step_counter += 1
        if self._batch_mode:
            self._flush_buffer()

    def get_last_error(self) -> Optional[str]:
        """Возвращает последнее сообщение об ошибке"""
        return self._last_error

    def reset_step_counter(self, value: int = 1):
        """Сбрасывает счетчик шагов"""
        self.step_counter = max(1, value)

    def clear_history(self):
        """Очищает историю команд"""
        if hasattr(self, '_command_history'):
            self._command_history.clear()

    def __del__(self):
        """Деструктор - гарантирует отправку оставшихся команд"""
        if self._batch_mode:
            self._flush_buffer()