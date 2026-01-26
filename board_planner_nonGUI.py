import pandas as pd
from numpy import nan
import rectpack
import webbrowser

input_file = 'greene_medicine_cabinet - Copy.csv'
purchased_boards_file = 'purchased_boards_greene_medicine_cabinet.csv'
thickness_tolerance = 0.02  # inches
padding = 0.5  # inches

def read_purchased_boards(purchased_boards_csv_filename):
    """Read the purchased boards from the CSV file.

    Args:
        purchased_boards_csv_filename (str): Path to the purchased boards CSV file.
    Returns:
        list: A list of dictionaries representing purchased boards.
    """
    purchased_boards = pd.read_csv(purchased_boards_file).to_dict(orient='records')
    purchased_boards = [{'Material': pb['Material'].lower(),
                        'Width': float(pb['Width']),
                        'Thickness': float(pb['Thickness']),
                        'Length': float(pb['Length']), 'BoardID': ix+1} for ix, pb in enumerate(purchased_boards)]
    return purchased_boards

def read_and_clean_board_data(input_csv_filename, thickness_tolerance, padding, input_dataframe=None):
    """Read and clean the board data from the input CSV file.

    Args:
        input_csv_filename (str): Path to the input CSV file.
        thickness_tolerance (float): Tolerance for grouping similar thicknesses.
        padding (float): Padding to add to width and length.
        input_dataframe (pd.DataFrame, optional): If provided, use this DataFrame instead of reading from CSV.
    Returns:
        list: A list of dictionaries representing cleaned board data.
    """

    if input_dataframe is not None:
        project_boards = input_dataframe
    else:
        project_boards = pd.read_csv(input_csv_filename)

    # remove any record where the 'Use' column is not 1
    project_boards = project_boards[project_boards['Use'] == 1].copy()
    # drop the 'Use' column
    project_boards.drop(columns=['Use'], inplace=True)

    # convert the material column to lowercase
    project_boards['Material'] = project_boards['Material'].str.lower()
    project_boards['Units'] = project_boards['Units'].str.lower()

    # if the 'Units' column does not contain the substring 'in', assume the units
    # are in mm and convert to inches
    project_boards.loc[~project_boards['Units'].str.contains('in'), 'Length'] /= 25.4
    project_boards.loc[~project_boards['Units'].str.contains('in'), 'Width'] /= 25.4
    project_boards.loc[~project_boards['Units'].str.contains('in'), 'Thickness'] /= 25.4

    # set the 'Units' column to 'inches'
    project_boards['Units'] = 'inches'

    # set the Quantity column to an integer
    project_boards['Quantity'] = project_boards['Quantity'].astype(int)

    # find the unique values in the 'Thickness' column
    unique_thicknesses = sorted(project_boards['Thickness'].unique().tolist())
    unique_materials = sorted(project_boards['Material'].unique().tolist())

    # apply the thickness tolerance to group similar thicknesses.
    # create a dict to map original thickness to adjusted thickness
    thickness_map = {}
    for t in unique_thicknesses:
        # check if t is within tolerance of any existing keys in thickness_map
        found = False
        for key in thickness_map.keys():
            if abs(t - key) <= thickness_tolerance:
                thickness_map[t] = thickness_map[key]
                found = True
                break
        if not found:
            thickness_map[t] = t

    # apply the thickness map to the 'Thickness' column
    project_boards['Adjusted Thickness'] = project_boards['Thickness'].map(thickness_map)
    project_boards['Adjusted Width'] = project_boards['Width'] + padding
    project_boards['Adjusted Length'] = project_boards['Length'] + padding

    prj_board_dict = project_boards.to_dict(orient='records')

    # make a second dictionary that has an individual entry for each board needed.  Note the Quantity field
    # remove the Quantity field since each entry is now a single board and assign all boards a unique ID
    id_counter = 1
    expanded_board_data = []
    for board in prj_board_dict:
        for _ in range(board['Quantity']):
            board_copy = board.copy()
            board_copy['ID'] = id_counter
            id_counter += 1
            expanded_board_data.append(board_copy)
    board_data = expanded_board_data
    for board in board_data:
        del board['Quantity']
    return board_data

def make_board_groups(board_data):
    board_groups = {'groups': {}, 'rects': {}}
    for board in board_data:
        key = (board['Material'], board['Adjusted Thickness'])
        if key not in board_groups['groups']:
            board_groups['groups'][key] = []
            board_groups['rects'][key] = []
        board_groups['groups'][key].append([board['ID'], (board['Adjusted Width'], board['Adjusted Length']), board['Item'], board['Sticker'], board['Comments']])
        board_groups['rects'][key].append((board['Adjusted Width'], board['Adjusted Length'], board['ID']))

    return board_groups


def pack_boards(board_groups, purchased_boards, thickness_tolerance):
    rects = board_groups['rects']
    success = True
    for key in rects.keys():
        print(f"Processing material/thickness group: {key}")
        material = key[0]
        thickness = key[1]

        # get the purchased boards that match this material and thickness
        matching_purchased_boards = []
        for pb in purchased_boards:
            if pb['Material'] == material and abs(pb['Thickness'] - thickness) <= thickness_tolerance:
                matching_purchased_boards.append(pb)

        if not matching_purchased_boards:
            print(f"No purchased boards match material {material} and thickness {thickness}")
            success = False
            raise ValueError(f"No purchased boards match material {material} and thickness {thickness}")

        # create a packer
        packer = rectpack.newPacker(rotation=True)
        for rect in rects[key]:
            packer.add_rect(*rect)
        for pb in matching_purchased_boards:
            packer.add_bin(pb['Width'], pb['Length'], 1, bid=pb['BoardID'])

        packer.pack()
        for abin in packer:
            for rect in abin:
                position = (rect.x, rect.y)
                ID = rect.rid
                # add position info to the board_groups data structure
                for board in board_groups['groups'][key]:
                    if board[0] == ID:
                        board.extend([position, abin.bid])
                        break
        
        # check for any rectangles that were not packed
        all_packed_ids = [rect.rid for abin in packer for rect in abin]
        unpacked_rects = [rect for rect in rects[key] if rect[2] not in all_packed_ids]
        if unpacked_rects:
            success = False
            # add unpacked_rects to board_groups with position set to 'unpacked'
            for rect in unpacked_rects:
                ID = rect[2]
                for board in board_groups['groups'][key]:
                    if board[0] == ID:
                        board.extend(['unpacked', -1])
                        break   
    board_data_labels = {0: 'ID', 1: 'Dimensions', 2: 'Item', 3: 'Sticker',
                        4: 'Comments', 5: 'Start Position', 6: 'Purchased Board ID'}
    board_data_with_labels_dict = {}
    # Let's convert each value in the board_groups['groups'] to a dict with labels
    for key in board_groups['groups'].keys():
        board_data_with_labels_dict[key] = []
        for board in board_groups['groups'][key]:
            board_dict = {}
            for ix, label in board_data_labels.items():
                board_dict[label] = board[ix]
            board_data_with_labels_dict[key].append(board_dict)
    return board_data_with_labels_dict

def get_end_positions(packed_boards):
    max_dim = {}
    # calculate end position for each packed board
    for key in packed_boards.keys():
        for board in packed_boards[key]:
            start_pos = board['Start Position']
            dimensions = board['Dimensions']
            if start_pos == 'unpacked':
                board['End Position'] = 'unpacked'
                continue
            end_pos = (start_pos[0] + dimensions[0], start_pos[1] + dimensions[1])
            board['End Position'] = end_pos

            if board['Purchased Board ID'] not in max_dim:
                max_dim[board['Purchased Board ID']] = [0, 0]
            if end_pos[0] > max_dim[board['Purchased Board ID']][0]:
                max_dim[board['Purchased Board ID']][0] = end_pos[0]
            if end_pos[1] > max_dim[board['Purchased Board ID']][1]:
                max_dim[board['Purchased Board ID']][1] = end_pos[1]
    return max_dim

def make_html_output(packed_boards, purchased_boards, board_data, padding, max_board_dim):

    html_output = '<html><head><title>Board Cutting Plan</title></head><body>'

    html_output += '<h1>Board Cutting Plan</h1>'
    html_output += '<ul>'
    html_output += f'<li>Padding added to each dimension: {padding:.6g} in</li>'
    html_output += f'<li>Total number of purchased boards: {len(purchased_boards)}</li>'
    html_output += f'<li>Total number of parts to be cut: {len(board_data)}</li>'
    html_output += '</ul>'

    html_output += '<h2>Unplaced parts:</h2>'
    html_output += '<table border="1">'
    success = True
    for key in packed_boards.keys():
        for b in packed_boards[key]:
            if b['Start Position'] == 'unpacked':
                success = False
                html_output += '<tr><td>'
                html_output += f"<font color='red'>Material: {key[0].capitalize()}, Thickness: {key[1]:.6g} in</font>"
                comments = b['Comments'] if 'Comments' in b and b['Comments'] != nan else ''
                html_output += f"<br>ID: {b['ID']}, Item: {b['Item']}, Sticker: {b['Sticker']}, Padded Dimensions (W x L): {b['Dimensions'][0]:.6g} x {b['Dimensions'][1]:.6g}, Comments: {comments}</br>"
                html_output += '</td></tr>'
    if success:
        html_output += '<tr><td><font color="green"><b>All parts were successfully placed on the purchased boards.</b></font></td></tr>'
    html_output += '</table>'


    for board in purchased_boards:
        html_output += f"<h2>Purchased Board ID: {board['BoardID']} - Material: {board['Material'].capitalize()}, Thickness: {board['Thickness']:.6g} in, Width: {board['Width']:.6g} in, Length: {board['Length']:.6g} in:</h2>"

        # state the max used dimensions
        if board['BoardID'] in max_board_dim:
            used_w, used_l = max_board_dim[board['BoardID']]
            html_output += f"<font color='green'><b>Max Used Dimensions: {used_w:.6g} in (W) x {used_l:.6g} in (L)</b></font><br>"
        html_output += '<table border="1"><tr><th>ID</th><th>Item</th><th>Ltr</th><th>Padded Dims (W x L)</th><th>Dims (W x L)</th><th>Start Pos. (X, Y)</th><th>End Pos. (X, Y)</th><th>Notes</th></tr>'
        for key in packed_boards.keys():
            for b in packed_boards[key]:
                if b['Purchased Board ID'] == board['BoardID']:
                    comments = b['Comments'] if 'Comments' in b and b['Comments'] != nan else ''
                    html_output += f"<tr><td>{b['ID']}</td><td>{b['Item']}</td><td>{b['Sticker']}</td><td>{b['Dimensions'][0]:.6g} x {b['Dimensions'][1]:.6g}</td><td>{(b['Dimensions'][0]-padding):.6g} x {(b['Dimensions'][1]-padding):.6g}</td><td>({b['Start Position'][0]:.6g}, {b['Start Position'][1]:.6g})</td><td>({b['End Position'][0]:.6g}, {b['End Position'][1]:.6g})</td><td>{comments}</td></tr>"
        html_output += '</table>'

    html_output += '</body></html>'

    with open('board_cutting_plan.html', 'w') as f:
        f.write(html_output)
    # open the output HTML file in the default web browser

    webbrowser.open('board_cutting_plan.html')
if __name__ == '__main__':

    purchased_boards = read_purchased_boards(purchased_boards_file)
    board_data = read_and_clean_board_data(input_file, thickness_tolerance, padding)
    board_groups = make_board_groups(board_data)
    packed_boards = pack_boards(board_groups, purchased_boards, thickness_tolerance)
    max_board_dim = get_end_positions(packed_boards)
    make_html_output(packed_boards, purchased_boards, board_data, padding, max_board_dim)



x = 2


