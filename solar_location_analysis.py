import numpy as np
import pandas
import datetime as dt
import matplotlib.pyplot as plt
import csv
from datetime import datetime
from scipy import integrate

# Local imports
import read_temp_data as read_temp_data
# from heat_sink_design import heat_sink_design
 
def main():
    # reading the CSV file
    nrel_directory = r'C:\Users\dclar\Documents\Solar Panels\analysis\theoretical\\'
    NREL_files = {'denver_1947888_39.74_-105.03_2022_localTime.csv',
                'phoenix_1309015_33.44_-112.05_2022_localTime.csv',
                'atlanta_3894477_33.80_-84.39_2022_localTime.csv',
                'sahara_487671_22.77_5.54_2019_localTime.csv',         # Tamanrasset
                'brussels_454991_50.85_4.34_2019_localTime.csv'}

    # === Solar Panel Inputs ===
    # https://es-media-prod.s3.amazonaws.com/media/components/panels/spec-sheets/HyundaiEnergySolutions_HiA-SXXXHG_M2_300_315W_xSe5w2v.pdf
    sp_area_sqft = (5.5*3.5) # sqft
    sqft_to_m2 = 0.0928790337119164
    sp_area_m2 = 0.992 * 1.675 # (39.06"x65.94")
    SP_power_rating = 305 # Watts
    SP_efficiency = 0.184 # %
    eff_loss_per_degree = 0.0306 # %

    price_per_kWh = 0.16 # dollars

    dissapation_delta = 8.45 # celcius
    num_bars = 10

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
    nrel_in_sun_dict = []

    for idx_file,i_csv in enumerate(NREL_files):

        NREL_datetime = []
        NREL_DNI =[]
        NREL_temp = []

        nrel_temp_in_sun = []
        nrel_time_in_sun = []
        nrel_dni_in_sun = []
        power_loss_due_to_temp = 0
        i_power_ideal = []
        i_power_heated = []

        flag_found_sunrise_idx = False
        sunrise_idx = []

        filename_split = i_csv.split('_')
        filename_location = filename_split[0]

        # if filename_location == 'phoenix':
        #     phx_idx = idx_file

        nrel_filepath = nrel_directory + i_csv
        with open(nrel_filepath, newline='') as csvNREL:
            NREL_reader = csv.reader(csvNREL, delimiter=' ', quotechar='|')
            for row_idx,row in enumerate(NREL_reader):

                # Start of data
                if row[0][0:2] == '20':
                    split_row = row[0].split(',')

                    year = 2022 #int(split_row[0])
                    month = int(split_row[1])
                    day = int(split_row[2])
                    hour = int(split_row[3])
                    minute = int(split_row[4])
                    # NREL_datetime.append(datetime(year, month, day, hour, minute))

                    # NREL_DNI.append(int(split_row[5]))
                    # NREL_temp.append(float(split_row[6])) # Celcius

                    # --- Sun has risen ---
                    if float(split_row[5]) > 0:
                        i_temp = float(split_row[6])
                        i_dni = int(split_row[5])
                        nrel_temp_in_sun.append(i_temp)
                        nrel_time_in_sun.append(datetime(year, month, day, hour, minute))
                        nrel_dni_in_sun.append(i_dni)

                        # --- Find sun rise ---
                        if flag_found_sunrise_idx == False:
                            sunrise_idx = row_idx
                            sunrise_dt = datetime(year, month, day, hour, minute)                        

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

            # nrel_dict.append( { 'name': filename_location,
            #                     'time': NREL_datetime,
            #                     'dni' : NREL_DNI,
            #                     'temp': NREL_temp} )
            
            nrel_dict.append( { 'name': filename_location,
                                'time': nrel_time_in_sun,
                                'dni' : NREL_DNI,
                                'temp': nrel_temp_in_sun,
                                'power_ideal': i_power_ideal,
                                'power_heated':i_power_heated } )
            
    # === Sum data for power loss from temperature ===
    power_sum_ideal_kwh = {}
    heatsink_power_sum = {}
    money_sum_ideal = {}
    heatsink_money_sum = {}
    for i_loc in nrel_dict:

        key = i_loc['name']

        start_time = i_loc['time'][0]
        sec_from_start = [(start_time - val).seconds for val in i_loc['time']]

        # --- Integration needs to be broken up for day to day --- 
        integrated_kwh = integrate.trapezoid(i_loc['power_ideal'],sec_from_start) /1000/3600
        power_sum_ideal_kwh[key] = integrated_kwh
        money_sum_ideal[key] = round(integrated_kwh * price_per_kWh,2)

        heatsink_power_sum[key] = {}
        heatsink_money_sum[key] = {}
        for idx,i_heatsink in enumerate(ordered_design_names):
            heatsink_scaled_power_kwh = integrated_kwh * (1+percent_saved_list[idx]/100)

            heatsink_power_sum[key][i_heatsink] = heatsink_scaled_power_kwh
            heatsink_money_sum[key][i_heatsink] = round(heatsink_scaled_power_kwh * price_per_kWh,2)
    gg= 0
    plot2_wtf(money_sum_ideal,heatsink_money_sum)
    gsd=0

def plot2_wtf(money_sum_ideal,heatsink_money_sum):

    fig, ax  = plt.subplots()

    # for key,value in heatsink_build_costs.items():

    list_to_plot = []
    names = []
    kk=0
    for key,value in money_sum_ideal.items():

        ambient_generation = value
        list_to_plot.append(ambient_generation)
        names.append(str(ambient_generation))

        hf = heatsink_money_sum[key]
        for key2,value2 in heatsink_money_sum[key].items():
            heatsink_generation = heatsink_money_sum[key][key2]
            list_to_plot.append(heatsink_generation)
            names.append(str(heatsink_generation))

            g=0

        list_to_plot.append(0)
        
        kk += 1
        names.append(str(kk))

    bars = ax.bar(names, list_to_plot)
    plt.show()

    d=0    


    # --- Ideal ---
    # calc_power_sum_ideal = 0
    # for idx,this_power in enumerate(i_loc['power_ideal']):

    #     if idx == len(i_loc['power_ideal'])-1:
    #         # print('break')
    #         break

    #     this_time = i_loc['time'][idx]
    #     next_time = i_loc['time'][idx+1]
    #     time_delta = (next_time - this_time).total_seconds() / 3600
    #     next_power = i_loc['power_ideal'][idx+1]

    #     trapezoid = ((this_power + next_power) / 2) * time_delta
    #     calc_power_sum_ideal += trapezoid

    # --- Heated ---
    # calc_power_sum_heated = 0
    # for idx,this_power in enumerate(i_loc['power_heated']):

    #     if idx == len(i_loc['power_heated'])-1:
    #         # print('break')
    #         break

    #     this_time = i_loc['time'][idx]
    #     next_time = i_loc['time'][idx+1]
    #     time_delta = (next_time - this_time).total_seconds() / 3600
    #     next_power = i_loc['power_heated'][idx+1]

    #     trapezoid = ((this_power + next_power) / 2) * time_delta
    #     calc_power_sum_heated += trapezoid

    # # money_per_year_ideal = calc_power_sum_ideal/1000 * price_per_kWh
    # money_per_year_heated = calc_power_sum_heated/1000 * price_per_kWh

    # kWhr_saved = (hs_power_sum - calc_power_sum)/1000 # kW-hr

    # money_lost = money_per_year_ideal - money_per_year_heated

    # percent_lost = money_lost / money_per_year_ideal * 100

    # nrel_dict.append( {
    #     'ideal gen':  money_per_year_ideal,
    #     'actual gen': money_per_year_heated,
    #     'money lost': money_lost,
    #     'percent lost': percent_lost
    # })

    # print('*'*50)
    # print(i_loc['name'])
    # print('Ideal generation: $',round(money_per_year_ideal,2))
    # print('Actual generation: $',round(money_per_year_heated,2))
    # print('Money lost $',round(money_lost,2))
    # print('% lost:',round(percent_lost,2),'%\n')


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
