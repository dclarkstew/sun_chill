import numpy as np
import pandas
import datetime as dt
import matplotlib.pyplot as plt
import csv
from datetime import datetime
from scipy import integrate

# Local imports
import read_temp_data as read_temp_data # type: ignore
# from heat_sink_design import heat_sink_design
 
def main():
    # reading the CSV file
    nrel_directory = r'C:\Users\dclar\Documents\Solar Panels\python_analysis\theoretical\\'
    NREL_files = ['denver_1947888_39.74_-105.03_2022_localTime.csv',
                'phoenix_1309015_33.44_-112.05_2022_localTime.csv',
                'atlanta_3894477_33.80_-84.39_2022_localTime.csv',
                'sahara_487671_22.77_5.54_2019_localTime.csv',         # Tamanrasset
                'brussels_454991_50.85_4.34_2019_localTime.csv']

    # === Solar Panel Inputs ===
    # https://es-media-prod.s3.amazonaws.com/media/components/panels/spec-sheets/HyundaiEnergySolutions_HiA-SXXXHG_M2_300_315W_xSe5w2v.pdf
    sp_area_sqft = (5.5*3.5) # sqft
    sqft_to_m2 = 0.0928790337119164
    sp_area_m2 = 0.992 * 1.675 # (39.06"x65.94")
    SP_power_rating = 305 # Watts
    SP_efficiency = 0.184 # %
    eff_loss_per_degree = 0.0306 # %
    price_per_kWh = 0.16 # dollars

    # --- Constants ---
    # Specific heat capacity (J/g-C)
    c_silicon = 0.705 # Silicon
    c_alum = 0.897 # Aluminium

    # Heat transfer coefficient (W/m-K)
    k_silicon = 0.2 # Silicon
    k_alum = 237 # Aluminum

    # Room temperature
    room_temp = 25 # Celcius

    # --- Local module calls ---
    filename = 'test_20240414_cleanedup.txt'
    ordered_design_names, percent_saved_list = read_temp_data.read_temp_data(filename)

    # === Heatsink costs ===
    heatsink_build_costs = {
        '1/8" flat plate' : 3837.58,
        '1/2" x 1/2" x 3" bars' : 5788.46,
        '1/4" Honeycomb Grid Core' : 4159.33,
        '1/8" x 3" fins' : 4119.17
    }

    # ========================
    # === Import NREL data ===
    # ========================

    nrel_dict = []
    for idx_file,i_csv in enumerate(NREL_files):

        # --- Initialize ---
        NREL_datetime = []
        NREL_DNI =[]
        NREL_temp = []
        nrel_temp_in_sun = []
        nrel_time_in_sun = []
        nrel_dni_in_sun = []
        i_power_ideal = []
        i_power_heated = []

        filename_split = i_csv.split('_')
        filename_location = filename_split[0]

        nrel_dict.append( { 'name': filename_location,'data_days':[] } )

        nrel_filepath = nrel_directory + i_csv
        with open(nrel_filepath, newline='') as csvNREL:
            NREL_reader = csv.reader(csvNREL, delimiter=' ', quotechar='|')

            day_last = 1
            for row_idx,row in enumerate(NREL_reader):

                # Start of data
                if row[0][0:2] == '20':
                    split_row = row[0].split(',')

                    year = 2022 #int(split_row[0])
                    month = int(split_row[1])
                    day = int(split_row[2])
                    hour = int(split_row[3])
                    minute = int(split_row[4])

                    # --- Is the entry on the same day? ---
                    if day_last != day:
                        nrel_dict[-1]['data_days'].append( {'time': nrel_time_in_sun,
                                                            'dni' : NREL_DNI,
                                                            'temp': nrel_temp_in_sun,
                                                            'power_ideal': i_power_ideal,
                                                            'power_heated':i_power_heated } )
                        day_last = day
                        nrel_time_in_sun = []
                        NREL_DNI = []
                        nrel_temp_in_sun = []
                        i_power_ideal = []
                        i_power_heated = []     

                    # --- Sun has risen ---
                    if float(split_row[5]) > 0:
                        i_temp = float(split_row[6])
                        i_dni = int(split_row[5])
                        nrel_temp_in_sun.append(i_temp)
                        nrel_time_in_sun.append(datetime(year, month, day, hour, minute))
                        nrel_dni_in_sun.append(i_dni)                        

                        # --- Pretend this is the temp of the panel not the air ---
                        temp_above_roomtemp = i_temp - room_temp
                        if temp_above_roomtemp < 0:
                            efficiency_loss = 0
                        else:
                            efficiency_loss = temp_above_roomtemp * eff_loss_per_degree

                        i_irrad_panel = sp_area_m2 * i_dni
                        i_power_possible = i_irrad_panel*SP_efficiency
                        if i_power_possible >= SP_power_rating:
                            i_power_ideal.append(SP_power_rating)
                            i_power_heated.append(SP_power_rating - (SP_power_rating * efficiency_loss))
                        else:
                            i_power_ideal.append(i_power_possible)
                            i_power_heated.append(i_power_possible - (i_power_possible * efficiency_loss))

            # --- Need this to get the last day ---
            nrel_dict[-1]['data_days'].append( {'time': nrel_time_in_sun,
                                                'dni' : NREL_DNI,
                                                'temp': nrel_temp_in_sun,
                                                'power_ideal': i_power_ideal,
                                                'power_heated':i_power_heated } )
            
    # === Sum data for power loss from temperature ===
    power_sum_dict = {}
    money_sum_dict = {}

    # --- Loop through each location ---
    for i_location_data in nrel_dict:

        key = i_location_data['name']
        
        # --- Initialize sums ---
        power_sum_dict[key] = {}
        money_sum_dict[key] = {}
        power_sum_dict[key]['ambient'] = 0
        money_sum_dict[key]['ambient'] = 0
        for i_heatsink in ordered_design_names:
            power_sum_dict[key][i_heatsink] = 0
            money_sum_dict[key][i_heatsink] = 0 
        
        # --- Loop through each day at each location ---
        for i_day in i_location_data['data_days']:

            if i_day['time'] == []:
                continue

            start_time = i_day['time'][0]

            sec_from_start = [(val - start_time).seconds for val in i_day['time']]

            # --- Integrate power over day and sum money earned for ambient temperatures ---
            integrated_kwh = integrate.trapezoid(i_day['power_heated'],x=sec_from_start) /1000/3600
            power_sum_dict[key]['ambient'] += integrated_kwh
            money_sum_dict[key]['ambient'] += integrated_kwh * price_per_kWh

            # --- Do the same but included heat sinks ---
            for idx,i_heatsink in enumerate(ordered_design_names):
                heatsink_scaled_power_kwh = integrated_kwh * (1+percent_saved_list[idx]/100)

                power_sum_dict[key][i_heatsink] += heatsink_scaled_power_kwh
                money_sum_dict[key][i_heatsink] += heatsink_scaled_power_kwh * price_per_kWh

    # --- Rearrange dict ---
    heatsink_type_location_dict = {key:{k:money_sum_dict[k][key] for k in money_sum_dict if key in money_sum_dict[k]} for key in ordered_design_names}

    # --- Difference from ambient dict ---
    money_diff_dict = {}
    for key,i_location_data in money_sum_dict.items():
        ambient_generation = money_sum_dict[key]['ambient']

        money_diff_dict[key] = {}
        for key2,i_design_value in i_location_data.items():
            money_diff_dict[key][key2] = round(i_design_value - ambient_generation,2)

    plot2_wtf(money_diff_dict)
    gsd=0

def plot2_wtf(money_sum_dict):

    # fig, ax = plt.subplots(1,5)
    fig, ax = plt.subplots()

    plot_dict = {}

    for key,i_location_data in money_sum_dict.items():

        plot_dict[key] = {}
        plot_dict[key]['x_vals'] = []
        plot_dict[key]['y_vals'] = []
        for key2,i_design_value in i_location_data.items():

            val_rounded = round(i_design_value,2)

            if val_rounded == 0:
                continue

            plot_dict[key]['x_vals'].append(str(val_rounded))
            plot_dict[key]['y_vals'].append( val_rounded )

    # --- Plot per location ---
    for i_loc in ['brussels','atlanta','denver','sahara','phoenix']:

        x_vals = plot_dict[i_loc]['x_vals']
        y_vals = plot_dict[i_loc]['y_vals']

        ax.bar(x_vals,y_vals)

    ax.set_title('brussels '+'atlanta '+'denver '+'sahara '+'phoenix')

    plt.show()

    d=0    


# === Plot ===
def plot_location_data1(phx_idx,nrel_dict):
    color_list = ['red','blue','green','black','orange']

    fig, ax1 = plt.subplots()
    # for idx,i_loc in enumerate(nrel_dict):
    #     ax1.plot(i_loc['time'],i_loc['temp'], color=color_list[idx],label=i_loc['name'])

    ax1.plot(nrel_dict[phx_idx]['time'],nrel_dict[phx_idx]['temp'], color=color_list[phx_idx],label=nrel_dict[phx_idx]['name'])

    fig.suptitle('Temp vs date')
    fig.legend(loc = 'upper right')
    ax1.set(xlabel='Date-time', ylabel='Temperature C')
    ax1.grid()

    plt.show()


    h =0

if __name__ == "__main__":
    main()
