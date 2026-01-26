# GUI inputs #
from board_planner_nonGUI import read_purchased_boards, read_and_clean_board_data, make_board_groups, pack_boards, get_end_positions, make_html_output
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog, QMessageBox
import sys

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
# thickness tolerance input #
thickness_label = QLabel('Thickness Tolerance (inches):')
thickness_input = QLineEdit('0.02')
layout.addWidget(thickness_label)
layout.addWidget(thickness_input)
# padding input #
padding_label = QLabel('Padding (inches):')
padding_input = QLineEdit('0.5')
layout.addWidget(padding_label)
layout.addWidget(padding_input)
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

# run button, colored green #

run_button = QPushButton('Run Board Planner')
run_button.setStyleSheet("background-color: green; color: white;")
run_button.clicked.connect(on_run_button_clicked)
layout.addWidget(run_button)


# Set layout and show window
window.setLayout(layout)
window.show()

# Start the application event loop
sys.exit(app.exec())
