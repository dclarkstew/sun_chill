import numpy as np
import pandas
import datetime as dt
import matplotlib.pyplot as plt
import csv
from datetime import datetime

# Local imports
# from heat_sink_design import heat_sink_design
 
# reading the CSV file
NREL_files = {'denver_1947888_39.74_-105.03_2022_localTime.csv',
             'phoenix_1309015_33.44_-112.05_2022_localTime.csv',
             'atlanta_3894477_33.80_-84.39_2022_localTime.csv',
             'sahara_487671_22.77_5.54_2019_localTime.csv',
             'brussels_454991_50.85_4.34_2019_localTime.csv'}

# === Solar Panel Inputs ===
# http://www.solardesigntool.com/components/module-panel-solar/Canadian-Solar/1327/CS6P-250M/specification-data-sheet.html
sp_area_sqft = (5.5*3.5) # sqft
sqft_to_m2 = 0.0928790337119164
sp_area_m2 = sp_area_sqft * sqft_to_m2
SP_area = 17.334375 # Sqft
SP_area = 1.61 # m^2
SP_power_rating = 305 # Watts
SP_efficiency = 0.1554 # %
eff_loss_per_degree = 0.045 # %
mass = 20000 # g

price_per_kWh = 0.23 # dollars

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

    filename_split = i_csv.split('_')
    filename_location = filename_split[0]

    if filename_location == 'phoenix':
        phx_idx = idx_file

    with open(i_csv, newline='') as csvNREL:
        NREL_reader = csv.reader(csvNREL, delimiter=' ', quotechar='|')
        for row in NREL_reader:

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

                if int(split_row[5]) > 0:
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
        
for i_loc in nrel_dict:

    # --- Ideal ---
    calc_power_sum_ideal = 0
    for idx,this_power in enumerate(i_loc['power_ideal']):

        if idx == len(i_loc['power_ideal'])-1:
            # print('break')
            break

        this_time = i_loc['time'][idx]
        next_time = i_loc['time'][idx+1]
        time_delta = (next_time - this_time).total_seconds() / 3600
        next_power = i_loc['power_ideal'][idx+1]

        trapezoid = ((this_power + next_power) / 2) * time_delta
        calc_power_sum_ideal += trapezoid

    # --- Heated ---
    calc_power_sum_heated = 0
    for idx,this_power in enumerate(i_loc['power_heated']):

        if idx == len(i_loc['power_heated'])-1:
            # print('break')
            break

        this_time = i_loc['time'][idx]
        next_time = i_loc['time'][idx+1]
        time_delta = (next_time - this_time).total_seconds() / 3600
        next_power = i_loc['power_heated'][idx+1]

        trapezoid = ((this_power + next_power) / 2) * time_delta
        calc_power_sum_heated += trapezoid

    money_per_year_ideal = calc_power_sum_ideal/1000 * price_per_kWh
    money_per_year_heated = calc_power_sum_heated/1000 * price_per_kWh

    # kWhr_saved = (hs_power_sum - calc_power_sum)/1000 # kW-hr

    money_saved = money_per_year_ideal - money_per_year_heated

    ratio = money_saved / money_per_year_ideal

    print('*'*50)
    print(i_loc['name'])
    print('Ideal generation: $',round(money_per_year_ideal,2))
    print('Actual generation: $',round(money_per_year_heated,2))
    print('Money lost $',round(money_saved,2))
    print('Ratio:',round(ratio,2),'\n')


# === Plot ===

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