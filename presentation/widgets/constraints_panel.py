from PyQt5.QtWidgets import (QScrollArea, QGroupBox, QGridLayout, QComboBox, QLineEdit,
                             QTableWidget, QTableWidgetItem, QPushButton, QLabel, QHBoxLayout,
                             QMessageBox)
from PyQt5.QtCore import Qt

class ConstraintsPanel(QScrollArea):
    def __init__(self, analysis_type, parent=None):
        super().__init__(parent)
        self.analysis_type = analysis_type
        self.parent = parent  # parent в данном случае будет InputPage
        self.constraints = {}
        self.init_ui()
        self.setWidgetResizable(True)

    def init_ui(self):
        group = QGroupBox("Управление ограничениями параметров")
        layout = QGridLayout()

        # Выбор параметра
        self.param_selector = QComboBox()
        layout.addWidget(QLabel("Параметр:"), 0, 0)
        layout.addWidget(self.param_selector, 0, 1)

        # Выбор типа ограничения
        self.constraint_type = QComboBox()
        self.constraint_type.addItems([
            "Допустимый диапазон",
            "Минимальное значение",
            "Максимальное значение",
            "Фиксированное значение"
        ])
        layout.addWidget(QLabel("Тип ограничения:"), 1, 0)
        layout.addWidget(self.constraint_type, 1, 1)

        # Поля ввода значений
        self.min_label = QLabel("Мин:")
        self.max_label = QLabel("Макс:")
        self.fixed_label = QLabel("Фикс:")
        
        self.min_input = QLineEdit()
        self.max_input = QLineEdit()
        self.fixed_input = QLineEdit()

        input_layout = QHBoxLayout()
        input_layout.addWidget(self.min_label)
        input_layout.addWidget(self.min_input)
        input_layout.addWidget(self.max_label)
        input_layout.addWidget(self.max_input)
        input_layout.addWidget(self.fixed_label)
        input_layout.addWidget(self.fixed_input)
        layout.addLayout(input_layout, 2, 0, 1, 2)

        # Кнопки управления
        self.btn_add = QPushButton("Добавить ограничение")
        self.btn_add.clicked.connect(self.add_constraint)
        self.btn_clear = QPushButton("Очистить все")
        self.btn_clear.clicked.connect(self.clear_constraints)
        
        layout.addWidget(self.btn_add, 3, 0)
        layout.addWidget(self.btn_clear, 3, 1)

        # Таблица активных ограничений
        self.constraints_table = QTableWidget()
        self.constraints_table.setColumnCount(3)
        self.constraints_table.setHorizontalHeaderLabels(["Параметр", "Тип", "Значения"])
        self.constraints_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.constraints_table, 4, 0, 1, 2)

        # Начальное состояние
        self.update_input_visibility()
        self.constraint_type.currentIndexChanged.connect(self.update_input_visibility)
        
        group.setLayout(layout)
        self.setWidget(group)

    def update_input_visibility(self):
        """Обновление видимости полей ввода в зависимости от типа ограничения"""
        constraint_type = self.constraint_type.currentText()
        
        # Скрываем все элементы
        self.min_label.hide()
        self.max_label.hide()
        self.fixed_label.hide()
        self.min_input.hide()
        self.max_input.hide()
        self.fixed_input.hide()

        # Очищаем неиспользуемые поля
        if constraint_type != "Допустимый диапазон":
            self.min_input.clear()
            self.max_input.clear()
        if constraint_type != "Фиксированное значение":
            self.fixed_input.clear()

        # Показываем нужные элементы
        if constraint_type == "Допустимый диапазон":
            self.min_label.show()
            self.max_label.show()
            self.min_input.show()
            self.max_input.show()
            self.min_input.setPlaceholderText("Минимум")
            self.max_input.setPlaceholderText("Максимум")
            
        elif constraint_type == "Минимальное значение":
            self.min_label.show()
            self.min_input.show()
            self.min_input.setPlaceholderText("Минимальное значение")
            
        elif constraint_type == "Максимальное значение":
            self.max_label.show()
            self.max_input.show()
            self.max_input.setPlaceholderText("Максимальное значение")
            
        elif constraint_type == "Фиксированное значение":
            self.fixed_label.show()
            self.fixed_input.show()
            self.fixed_input.setPlaceholderText("Фиксированное значение")

    def add_constraint(self):
        """Добавление нового ограничения"""
        param = self.param_selector.currentText()
        c_type = self.constraint_type.currentText()
        
        if not param:
            QMessageBox.warning(self, "Ошибка", "Выберите параметр!")
            return

        try:
            constraint_data = {}
            display_value = ""
            
            if c_type == "Допустимый диапазон":
                min_val = float(self.min_input.text())
                max_val = float(self.max_input.text())
                if min_val >= max_val:
                    raise ValueError("Минимум должен быть меньше максимума")
                constraint_data = {'type': 'range', 'min': min_val, 'max': max_val}
                display_value = f"[{min_val} - {max_val}]"
                
            elif c_type == "Минимальное значение":
                min_val = float(self.min_input.text())
                constraint_data = {'type': 'min', 'value': min_val}
                display_value = f"≥ {min_val}"
                
            elif c_type == "Максимальное значение":
                max_val = float(self.max_input.text())
                constraint_data = {'type': 'max', 'value': max_val}
                display_value = f"≤ {max_val}"
                
            elif c_type == "Фиксированное значение":
                fixed_val = float(self.fixed_input.text())
                constraint_data = {'type': 'fixed', 'value': fixed_val}
                display_value = f"= {fixed_val}"
                
            # Обновление хранилища ограничений
            if self.analysis_type == "static":
                self.parent.parent.static_constraints[param] = constraint_data
            else:
                self.parent.parent.dynamic_constraints[param] = constraint_data
                
            # Обновление таблицы
            self._update_table(param, c_type, display_value)
            
        except ValueError as e:
            QMessageBox.warning(self, "Ошибка", f"Некорректные значения: {str(e)}")

    def _update_table(self, param, c_type, values):
        """Обновление таблицы ограничений"""
        row = self.constraints_table.rowCount()
        self.constraints_table.insertRow(row)
        
        self.constraints_table.setItem(row, 0, QTableWidgetItem(param))
        self.constraints_table.setItem(row, 1, QTableWidgetItem(c_type))
        self.constraints_table.setItem(row, 2, QTableWidgetItem(values))
        
        # Автоматическое выравнивание столбцов
        self.constraints_table.resizeColumnsToContents()

    def clear_constraints(self):
        """Очистка всех ограничений для текущего типа анализа"""
        if self.analysis_type == "static":
            self.parent.parent.static_constraints.clear()
        else:
            self.parent.parent.dynamic_constraints.clear()
            
        self.constraints_table.setRowCount(0)

    def update_params(self, params):
        """Обновление списка доступных параметров"""
        current_param = self.param_selector.currentText()
        self.param_selector.clear()
        self.param_selector.addItems(params)
        
        # Восстановление предыдущего выбора если параметр существует
        if current_param in params:
            self.param_selector.setCurrentText(current_param)