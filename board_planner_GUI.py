# GUI inputs #
from board_planner_nonGUI import read_purchased_boards, read_and_clean_board_data, make_board_groups, pack_boards, get_end_positions, make_html_output
from PySide6.QtWidgets import QApplication, QWidget, QSplitter, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog, QMessageBox
import sys
from PySide6 import QtWidgets
from PySide6 import QtCore
from PySide6.QtWidgets import QTableView
import pandas as pd
from PIL import Image, ImageDraw, ImageFont

def tentative_int(value):
    try:
        return int(value)
    except (ValueError, TypeError):
        return value

# Add this function before the GUI setup section
def part_on_table_context_menu(position):
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
            {'Item': '', 'Use': 0, 'Quantity': 0, 'Thickness': 0.0, 'Width': 0.0, 'Length': 0.0, 'Units': 'in', 'Material': '', 'Sticker': '', 'Comments': ''}
            part_data = pd.DataFrame([{'Item': row['Item'],
                        'Use': tentative_int(float(row['Use'])),
                        'Quantity': tentative_int(float(row['Quantity'])),
                        'Thickness': float(row['Thickness']),
                        'Width': float(row['Width']),
                        'Length': float(row['Length']),
                        'Units': row['Units'],
                        'Material': row['Material'],
                        'Sticker': row['Sticker'],
                        'Comments': row['Comments']} for ix, row in part_data.iterrows()])
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

# Add this function before the GUI setup section
def PB_on_table_context_menu(position):
    menu = QtWidgets.QMenu()
    load_action = menu.addAction('Load DataFrame from CSV')
    save_action = menu.addAction('Save DataFrame to CSV')
    add_row_action = menu.addAction('Add Row')
    
    action = menu.exec(PB_data_table.mapToGlobal(position))
    
    if action == load_action:
        file_name, _ = QFileDialog.getOpenFileName(window, 'Load DataFrame from CSV', '', 'CSV Files (*.csv)')
        if file_name:
            global PB_data

            loaded_df = pd.read_csv(file_name)
            PB_data = pd.DataFrame([{'Material': pb['Material'].lower(),
                        'Width': float(pb['Width']),
                        'Thickness': float(pb['Thickness']),
                        'Length': float(pb['Length']), 'BoardID': ix+1} for ix, pb in loaded_df.iterrows()])


            PB_data_model = TableModel(PB_data)
            PB_data_table.setModel(PB_data_model)
    
    elif action == save_action:
        file_name, _ = QFileDialog.getSaveFileName(window, 'Save DataFrame to CSV', '', 'CSV Files (*.csv)')
        if file_name:
            PB_data.to_csv(file_name, index=False)
            QMessageBox.information(window, 'Success', f'DataFrame saved to {file_name}')
    
    elif action == add_row_action:
        new_row = {col: '' for col in PB_data.columns}
        PB_data.loc[len(PB_data)] = new_row
        PB_data_model = TableModel(PB_data)
        PB_data_table.setModel(PB_data_model)

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
            col_name = self._data.columns[index.column()]
            if col_name in ['Use', 'Quantity', 'BoardID']:
                try:
                    value = int(value)
                except ValueError:
                    return False
            elif col_name in ['Thickness', 'Width', 'Length']:
                try:
                    value = float(value)
                except ValueError:
                    return False
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
            
def draw_boards(packed_boards, boards, max_board_dim, padding):
    # image size in pixels: Use 1/16 inch = 3 pixels
    image_names = {}

    margin = 10  # pixels
    scale = 48  # 1 inch = 48 pixels (1/16 inch = 3 pixels)

    light_colors_PIL = {
        0: (255, 182, 193),  # Light Pink
        1: (173, 216, 230),  # Light Blue
        2: (144, 238, 144),  # Light Green
        3: (255, 255, 224),  # Light Yellow
        4: (255, 228, 181),  # Light Orange
        5: (240, 230, 140),  # Khaki
        6: (176, 224, 230),  # Powder Blue
        7: (152, 251, 152),  # Pale Green
        8: (255, 240, 245),   # Lavender Blush
        9: (255, 250, 205),  # Lemon Chiffon
        10: (216, 191, 216),  # Thistle
    }

    for board in boards:
        color_num = 0
        board_ID = board.get('BoardID', None)
        if board_ID is None:
            print('oops')
            continue
        img_width = int((board['Width']) * scale) + 2 * margin
        img_length = int((board['Length']) * scale) + 2 * margin
        image = Image.new('RGB', (img_width, img_length), 'white')
        draw = ImageDraw.Draw(image)
        # Draw purchased board outline
        b_w = board['Width'] * scale
        b_l = board['Length'] * scale
        draw.rectangle([margin, margin, margin + b_w, margin + b_l], outline='black', width=2)

        # Draw parts for this board
        for pb in packed_boards:
            part_list = packed_boards[pb]
            for part in part_list:
                if part.get('Purchased Board ID', None) != board_ID:
                    continue

                # outer rectangle with padding
                x1 = margin + part['Start Position'][0] * scale
                y1 = margin + part['Start Position'][1] * scale
                x2 = margin + part['End Position'][0] * scale
                y2 = margin + part['End Position'][1] * scale
                draw.rectangle([x1, y1, x2, y2], outline='red', width=1)

                x_inner1 = x1 + padding * scale
                y_inner1 = y1 + padding * scale

                x_inner2 = x2 - padding * scale
                y_inner2 = y2 - padding * scale
                color = light_colors_PIL[color_num % len(light_colors_PIL)]
                color_num += 1
                draw.rectangle([x_inner1, y_inner1, x_inner2, y_inner2], outline='blue', fill=color, width=1)
                # add text label in center
                text = f"{part['Sticker']}"
                text_x = (x_inner1 + x_inner2) / 2
                text_y = (y_inner1 + y_inner2) / 2
                text_size_px = int(min(scale * 1.0, (x_inner2 - x_inner1) // 2))  # 0.25 inch in pixels, capped at 24px
                font = ImageFont.truetype("arial.ttf", size=text_size_px)
                
                draw.text((text_x, text_y), text, fill='black', anchor='mm', font=font)
        # save image for this board
        image.save(f'purchased_board_{board_ID}.png')
        image_names[board_ID] = {'height': img_length, 'width': img_width, 'file': f'purchased_board_{board_ID}.png'}
        print(f'Saved image for purchased board {board_ID} as purchased_board_{board_ID}.png')
    return image_names
            
def on_run_button_clicked():
    try:
        thickness_tolerance = float(thickness_input.text())
        padding = float(padding_input.text())
        # purchased_boards_file = purchased_boards_path.text()
        #purchased_boards = read_purchased_boards(purchased_boards_file)
        purchased_boards = PB_data.to_dict(orient='records')
        #input_csv_filename, thickness_tolerance, padding
        board_data = read_and_clean_board_data(input_csv_filename='', thickness_tolerance=thickness_tolerance, padding=padding, input_dataframe=part_data)
        board_groups = make_board_groups(board_data)
        packed_boards = pack_boards(board_groups, purchased_boards, thickness_tolerance)
        max_board_dim = get_end_positions(packed_boards)
        image_files = draw_boards(packed_boards, purchased_boards, max_board_dim, padding)
        make_html_output(packed_boards, purchased_boards, board_data, padding, max_board_dim, image_files)
        QMessageBox.information(window, 'Success', f'Board planning completed successfully!\nCheck board_cutting_plan.html for output.\nImage files saved: {", ".join([info["file"] for info in image_files.values()])}')
    except Exception as e:
        # print entire traceback to QMessageBox
        import traceback
        tb_str = traceback.format_exc()

        QMessageBox.critical(window, 'Error', f'An error occurred: {str(e)}\n\nTraceback:\n{tb_str}')

def on_save_button_clicked():
    # Save current settings to a config file #
    # We will need to open these later, so just use a pickle file for simplicity #
    file_name, _ = QFileDialog.getSaveFileName(window, 'Save Settings to Board Planner File', '', 'Board Planner Files (*.pkl)')
    if file_name:
        import pickle
        settings = {
            'thickness_tolerance': thickness_input.text(),
            'padding': padding_input.text(),
            'part_data': part_data,
            'PB_data': PB_data
        }
        with open(file_name, 'wb') as f:
            pickle.dump(settings, f)
        QMessageBox.information(window, 'Success', f'Settings saved to {file_name}')

def on_load_button_clicked():
    # Load settings from a config file #
    file_name, _ = QFileDialog.getOpenFileName(window, 'Load Settings from Board Planner File', '', 'Board Planner Files (*.pkl)')
    if file_name:
        import pickle
        with open(file_name, 'rb') as f:
            settings = pickle.load(f)
        thickness_input.setText(settings.get('thickness_tolerance', '0.02'))
        padding_input.setText(settings.get('padding', '0.5'))
        global part_data, PB_data
        part_data = settings.get('part_data', part_data)
        PB_data = settings.get('PB_data', PB_data)
        # Update table models
        part_data_model = TableModel(part_data)
        part_data_table.setModel(part_data_model)
        PB_data_model = TableModel(PB_data)
        PB_data_table.setModel(PB_data_model)
        QMessageBox.information(window, 'Success', f'Settings loaded from {file_name}')




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


splitter = QSplitter(QtCore.Qt.Horizontal)

# Part data table with label
part_data_container = QWidget()
part_data_layout = QVBoxLayout()
part_data_label = QLabel('Part Data Setup')
part_data_layout.addWidget(part_data_label)
part_data_table = QTableView()
# 100 rows.  Initialize all 'Use' to 0
data_init = [{'Item': '', 'Use': 0, 'Quantity': 0, 'Thickness': 0.0, 'Width': 0.0, 'Length': 0.0, 'Units': 'in', 'Material': '', 'Sticker': '', 'Comments': ''} for _ in range(100)]
part_data = pd.DataFrame(data_init)
part_data_model = TableModel(part_data)
part_data_table.setModel(part_data_model)
part_data_table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
part_data_table.customContextMenuRequested.connect(part_on_table_context_menu)
part_data_layout.addWidget(part_data_table)
part_data_container.setLayout(part_data_layout)
splitter.addWidget(part_data_container)

# Purchased boards table with label
PB_data_container = QWidget()
PB_data_layout = QVBoxLayout()
PB_data_label = QLabel('Purchased Board Data')
PB_data_layout.addWidget(PB_data_label)
# 100 rows.  Initialize all 'Use' to 0
data2_init = [{'Material': '', 'Thickness': 0.0, 'Width': 0.0, 'Length': 0.0} for _ in range(100)]
PB_data = pd.DataFrame(data2_init)
PB_data_model = TableModel(PB_data)
PB_data_table = QTableView()
PB_data_table.setModel(PB_data_model)
PB_data_table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
PB_data_table.customContextMenuRequested.connect(PB_on_table_context_menu)
PB_data_layout.addWidget(PB_data_table)
PB_data_container.setLayout(PB_data_layout)
splitter.addWidget(PB_data_container)

layout.addWidget(splitter)

layout.setStretchFactor(horiz_layout, 1)
layout.setStretchFactor(splitter, 9)

# run button, colored green #

# horizontal layout for run, save, load buttons
button_layout = QHBoxLayout()

run_button = QPushButton('Run Board Planner')
run_button.setStyleSheet("background-color: green; color: white;")
run_button.clicked.connect(on_run_button_clicked)
button_layout.addWidget(run_button)

# save settings button (colored blue) #
save_button = QPushButton('Save Settings')
save_button.setStyleSheet("background-color: blue; color: white;")
save_button.clicked.connect(on_save_button_clicked)
button_layout.addWidget(save_button)

# load settings button (colored red) #
load_button = QPushButton('Load Settings')
load_button.setStyleSheet("background-color: red; color: white;")
load_button.clicked.connect(on_load_button_clicked)
button_layout.addWidget(load_button)

layout.addLayout(button_layout)

# Set layout and show window
window.setLayout(layout)
window.show()

# Start the application event loop
sys.exit(app.exec())
