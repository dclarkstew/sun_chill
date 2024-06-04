import os
import csv

dir_path = r'C:\Users\daniel.stewart\Documents\Daniel\solar\mouser_search\\'

search_list = []
price_list = []

od_file_list = os.listdir(dir_path)
for i_file in od_file_list:
    split_1 = i_file.split('.')

    csv_filename = dir_path + i_file
    with open(csv_filename,'r') as file:
        propagation_csv = csv.DictReader(file)
        for line_idx,line in enumerate(propagation_csv):

            # --- Length ---
            line_length = line['Length']
            if 'mm' in line_length:
                split_length = line_length.split('mm')
                length_str = split_length[0].replace(' ','')
                length_float = float(length_str)/25.4
            elif 'in' in line_length:
                split_length = line_length.split('in')
                length_str = split_length[0].replace(' ','')
                length_float = float(length_str)
            elif 'ft' in line_length:
                split_length = line_length.split('ft')
                length_str = split_length[0].replace(' ','')
                length_float = float(length_str)/12
            elif line_length == '':
                todo = 0
            else:
                g=0

            # --- Width ---
            line_width = line['Width']
            if 'mm' in line_width:
                split_width = line_width.split('mm')
                width_str = split_width[0].replace(' ','')
                width_float = float(width_str)/25.4
            elif 'in' in line_width:
                split_width = line_width.split('in')
                width_str = split_width[0].replace(' ','')
                width_float = float(width_str)
            elif 'ft' in line_width:
                split_width = line_width.split('ft')
                width_str = split_width[0].replace(' ','')
                width_float = float(width_str)/12
            elif line_width == '':
                todo = 0
            else:
                g=0

            # --- Price ---
            line_price = line['Pricing']
            split_price = line_price.split('$')
            price_str = split_price[1].replace('"','')
            price_str = price_str.replace(',','')
            price_float = float(price_str)


            area = width_float * length_float
            cost_per_sq_in = price_float / area

            print(cost_per_sq_in)
            line['Pricing'] = cost_per_sq_in
            search_list.append(line)

            


search_list = sorted(search_list, key=lambda d: d['Pricing'])

# --- Print the good ones ---
for idx,i_line in enumerate(search_list):
    
    line_pn = i_line['Mfr Part Number']
    line_avail = i_line['Availability']
    line_price = round(i_line['Pricing'],2)
    line_thermal = i_line['Thermal Conductivity']
    line_type = i_line['Type']

    print(line_pn,line_price,line_thermal,line_type)

    if idx == 25:
        break

done =0