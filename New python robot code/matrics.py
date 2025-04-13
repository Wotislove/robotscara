# Глобальные переменные для хранения позиций
glue_point = {
    "X": "0.00",  # Базовая координата X для клеевой точки
    "Y": "0.00",  # Базовая координата Y для клеевой точки
    "Z": "0.00",  # Базовая координата Z для клеевой точки
    "rows": "1",  # Количество строк в сетке
    "cols": "1"  # Количество столбцов в сетке
}

magazine_pos = {
    "X": "0.00",  # Координата X магазина
    "Y": "0.00",  # Координата Y магазина
    "Z": "0.00"  # Координата Z магазина
}


def validate_value(value, default=0.0, min_val=None, max_val=None):
    """
    Проверяет и корректирует входное значение.

    Args:
        value (str): Входное значение для проверки
        default: Значение по умолчанию при ошибке
        min_val: Минимальное допустимое значение
        max_val: Максимальное допустимое значение

    Returns:
        str: Откорректированное строковое значение
    """
    # Если значение пустое или "-", возвращаем значение по умолчанию
    if not value.strip() or value.strip() == "-":
        return str(default)

    try:
        # Пробуем преобразовать в число (float или int)
        num = float(value) if "." in value else int(value)

        # Проверяем границы значений
        if min_val is not None and num < min_val:
            return str(min_val)
        if max_val is not None and num > max_val:
            return str(max_val)

        return str(num)
    except ValueError:
        # При ошибке преобразования возвращаем значение по умолчанию
        return str(default)


def save_positions(new_glue_point, new_magazine_pos):
    """
    Сохраняет новые позиции с проверкой значений.

    Args:
        new_glue_point (dict): Новые параметры клеевой точки
        new_magazine_pos (dict): Новые параметры магазина
    """
    global glue_point, magazine_pos

    # Обновляем позицию клеевой точки с проверкой значений
    glue_point.update({
        'X': validate_value(new_glue_point['X'], 0.0),
        'Y': validate_value(new_glue_point['Y'], 0.0),
        'Z': validate_value(new_glue_point['Z'], 0.0, min_val=0, max_val=1000),
        'rows': validate_value(new_glue_point.get('rows', '1'), 1, min_val=1),
        'cols': validate_value(new_glue_point.get('cols', '1'), 1, min_val=1)
    })

    # Обновляем позицию магазина с проверкой значений
    magazine_pos.update({
        'X': validate_value(new_magazine_pos['X'], 0.0),
        'Y': validate_value(new_magazine_pos['Y'], 0.0),
        'Z': validate_value(new_magazine_pos['Z'], 0.0, min_val=0, max_val=1000)
    })


def get_positions():
    """
    Возвращает текущие позиции в виде словаря.

    Returns:
        dict: Копии текущих позиций glue_point и magazine_pos
    """
    return {
        'glue_point': glue_point.copy(),
        'magazine_pos': magazine_pos.copy()
    }


def get_grid_coordinates():
    """
    Генерирует координаты сетки на основе параметров glue_point.

    Returns:
        dict: Словарь с координатами всех точек сетки
             Ключи: (row, col), Значения: {'X': x, 'Y': y, 'Z': z}
    """
    # Получаем параметры сетки из glue_point
    rows = int(glue_point['rows'])
    cols = int(glue_point['cols'])
    base_x = float(glue_point['X'])
    base_y = float(glue_point['Y'])
    base_z = float(glue_point['Z'])

    # Создаем пустой словарь для координат
    grid_coords = {}

    # Генерируем координаты для каждой ячейки сетки
    for row in range(rows):
        for col in range(cols):
            # Вычисляем координаты с шагом 10 мм между точками
            grid_coords[(row, col)] = {
                'X': str(base_x + col * 10),  # X увеличивается по столбцам
                'Y': str(base_y + row * 10),  # Y увеличивается по строкам
                'Z': str(base_z)  # Z одинаков для всех точек
            }

    return grid_coords