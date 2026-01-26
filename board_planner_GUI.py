# GUI inputs #
from board_planner_nonGUI import read_purchased_boards, read_and_clean_board_data, make_board_groups, pack_boards, get_end_positions, make_html_output
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog, QMessageBox
import sys
from PySide6 import QtWidgets
from PySide6 import QtCore
from PySide6.QtWidgets import QTableView
import pandas as pd

# Add this function before the GUI setup section
def on_table_context_menu(position):
    menu = QtWidgets.QMenu()
    load_action = menu.addAction('Load DataFrame from CSV')
    save_action = menu.addAction('Save DataFrame to CSV')
    add_row_action = menu.addAction('Add Row')
    
    action = menu.exec(part_data_table.mapToGlobal(position))
    
    if action == load_action:
        file_name, _ = QFileDialog.getOpenFileName(window, 'Load DataFrame from CSV', '', 'CSV Files (*.csv)')
        if file_name:
            global part_data
            part_data = pd.read_csv(file_name)
            part_data_model = TableModel(part_data)
            part_data_table.setModel(part_data_model)
    
    elif action == save_action:
        file_name, _ = QFileDialog.getSaveFileName(window, 'Save DataFrame to CSV', '', 'CSV Files (*.csv)')
        if file_name:
            part_data.to_csv(file_name, index=False)
            QMessageBox.information(window, 'Success', f'DataFrame saved to {file_name}')
    
    elif action == add_row_action:
        new_row = {col: '' for col in part_data.columns}
        part_data.loc[len(part_data)] = new_row
        part_data_model = TableModel(part_data)
        part_data_table.setModel(part_data_model)

class TableModel(QtCore.QAbstractTableModel):

    # make editable table model for displaying pandas dataframe in QTableView

    def __init__(self, data):
        super().__init__()
        self._data = data

    def data(self, index, role):
        if role == QtCore.Qt.DisplayRole:
            value = self._data.iloc[index.row(), index.column()]
            return str(value)

    def setData(self, index, value, role):
        if role == QtCore.Qt.EditRole:
            self._data.iloc[index.row(), index.column()] = value
            self.dataChanged.emit(index, index)
            return True
        return False

    def flags(self, index):
        return super().flags(index) | QtCore.Qt.ItemIsEditable

    def rowCount(self, index):
        return self._data.shape[0]

    def columnCount(self, index):
        return self._data.shape[1]

    def headerData(self, section, orientation, role):
        # section is the index of the column/row.
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                return str(self._data.columns[section])

            if orientation == QtCore.Qt.Vertical:
                return str(self._data.index[section])
            
def on_run_button_clicked():
    try:
        thickness_tolerance = float(thickness_input.text())
        padding = float(padding_input.text())
        input_file = input_file_path.text()
        purchased_boards_file = purchased_boards_path.text()
        purchased_boards = read_purchased_boards(purchased_boards_file)
        board_data = read_and_clean_board_data(input_file, thickness_tolerance, padding)
        board_groups = make_board_groups(board_data)
        packed_boards = pack_boards(board_groups, purchased_boards, thickness_tolerance)
        max_board_dim = get_end_positions(packed_boards)
        make_html_output(packed_boards, purchased_boards, board_data, padding, max_board_dim)
        QMessageBox.information(window, 'Success', 'Board planning completed successfully!\nCheck board_cutting_plan.html for output.')
    except Exception as e:
        QMessageBox.critical(window, 'Error', f'An error occurred: {e}')

# GUI setup #
app = QApplication(sys.argv)
window = QWidget()
window.setWindowTitle('Board Planner Settings')
layout = QVBoxLayout()
horiz_layout = QHBoxLayout()
sub_layout1 = QVBoxLayout()
# thickness tolerance input #
thickness_label = QLabel('Thickness Tolerance (inches):')
thickness_input = QLineEdit('0.02')
sub_layout1.addWidget(thickness_label)
sub_layout1.addWidget(thickness_input)
horiz_layout.addLayout(sub_layout1)

sublayout2 = QVBoxLayout()
# padding input #
padding_label = QLabel('Padding (inches):')
padding_input = QLineEdit('0.5')
sublayout2.addWidget(padding_label)
sublayout2.addWidget(padding_input)
horiz_layout.addLayout(sublayout2)
layout.addLayout(horiz_layout)
# input file selection #
input_file_label = QLabel('Input File:')
input_file_path = QLineEdit('greene_medicine_cabinet.csv')
input_file_button = QPushButton('Browse')
def browse_input_file():
    file_name, _ = QFileDialog.getOpenFileName(window, 'Select Input CSV File', '', 'CSV Files (*.csv)')
    if file_name:
        input_file_path.setText(file_name)  
input_file_button.clicked.connect(browse_input_file)
layout.addWidget(input_file_label)
layout.addWidget(input_file_path)
layout.addWidget(input_file_button)
# purchased boards file selection #
purchased_boards_label = QLabel('Purchased Boards File:')
purchased_boards_path = QLineEdit('purchased_boards_greene_medicine_cabinet.csv')
purchased_boards_button = QPushButton('Browse')
def browse_purchased_boards_file():
    file_name, _ = QFileDialog.getOpenFileName(window, 'Select Purchased Boards CSV File', '', 'CSV Files (*.csv)')
    if file_name:
        purchased_boards_path.setText(file_name)
purchased_boards_button.clicked.connect(browse_purchased_boards_file)
layout.addWidget(purchased_boards_label)
layout.addWidget(purchased_boards_path)
layout.addWidget(purchased_boards_button)


resizable_horizontal_layout = QHBoxLayout()
vlayout1 = QVBoxLayout()


# add a table view for displaying board data #
part_data_label = QLabel('Part Data Setup:')
layout.addWidget(part_data_label)
part_data_table = QTableView()
# 100 rows.  Initialize all 'Use' to 0
data_init = [{'Item': '', 'Use': 0, 'Quantity': 0, 'Thickness': 0.0, 'Width': 0.0, 'Length': 0.0, 'Units': 'in', 'Material': '', 'Sticker': '', 'Comments': ''} for _ in range(100)]
part_data = pd.DataFrame(data_init)
part_data_model = TableModel(part_data)
part_data_table.setModel(part_data_model)
part_data_table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
part_data_table.customContextMenuRequested.connect(on_table_context_menu)


vlayout1.addWidget(part_data_table)
resizable_horizontal_layout.addLayout(vlayout1)
layout.addLayout(resizable_horizontal_layout)


# run button, colored green #

run_button = QPushButton('Run Board Planner')
run_button.setStyleSheet("background-color: green; color: white;")
run_button.clicked.connect(on_run_button_clicked)



# Set layout and show window
window.setLayout(layout)
window.show()

# Start the application event loop
sys.exit(app.exec())
