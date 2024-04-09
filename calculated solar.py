import numpy as np
import pandas
import datetime as dt
import matplotlib.pyplot as plt
import csv
from datetime import datetime

# Local imports
from heat_sink_design import heat_sink_design
 
# reading the CSV file
NREL_file = '1951980_39.74_-104.99_2019.csv'

# ---- Inputs ---
# http://www.solardesigntool.com/components/module-panel-solar/Canadian-Solar/1327/CS6P-250M/specification-data-sheet.html
SP_area = 17.334375 # Sqft
SP_area = 1.61 # m^2
SP_power_rating = 250 # Watts
SP_efficiency = 0.1554 # %
price_per_kWh = 0.23 # dollars
mass = 20000 # g
dissapation_delta = 8.45 # celcius
eff_per_degree = 0.45 # %
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

NREL_datetime = []
NREL_DNI =[]
NREL_temp = []

with open(NREL_file, newline='') as csvNREL:
    NREL_reader = csv.reader(csvNREL, delimiter=' ', quotechar='|')
    for row in NREL_reader:

        # Start of data
        if row[0][0:2] == '20':
            split_row = row[0].split(',')

            year = int(split_row[0])
            month = int(split_row[1])
            day = int(split_row[2])
            hour = int(split_row[3])
            minute = int(split_row[4])
            NREL_datetime.append(datetime(year, month, day, hour, minute))

            NREL_DNI.append(int(split_row[5]))
            NREL_temp.append(float(split_row[6])) # Celcius

# print(min(NREL_temp) , max(NREL_temp))

# ========================
# === Heat sink addition ===
# ========================

panel_dissipate_SArea, heatsink_dissipate_SArea, total_bar_weight = heat_sink_design(SP_area, num_bars)

# ========================
# === Calculate ===
# ========================

SP_pwr_per_area = SP_power_rating / SP_area

calc_pwr_per_time = []
calc_heatsink_temp = []
calc_panel_temp = [15] # celcius
calc_heatsink_temp = [15]

for idx,iRad in enumerate(NREL_DNI):
    i_temp_panel = calc_panel_temp[idx]
    i_temp_heatsink = calc_heatsink_temp[idx]
    i_temp_air = NREL_temp[idx]

    if idx+1 < len(NREL_DNI):
        time = (NREL_datetime[idx+1] - NREL_datetime[idx]).total_seconds()
    else:
        time = 0

    # Irradiance
    i_total_irradiance = iRad * SP_area
    if i_total_irradiance*SP_efficiency >= SP_power_rating:
        calc_pwr_per_time.append(SP_power_rating)
    else:
        calc_pwr_per_time.append(i_total_irradiance*SP_efficiency)

    # Temperature - change irradiance
    q_in = (time*i_total_irradiance)/(mass*c_silicon)

    # Temperature - change dissapation
    # Panel dissapation
    q_dot_panel = k_silicon * (SP_area*2) * (i_temp_air - i_temp_panel)
    delta_q = q_in + q_dot_panel

    # Alumninum bar dissapation
    q_dot_heatsink = (i_temp_air - i_temp_heatsink) * (k_alum * heatsink_dissipate_SArea + k_silicon * panel_dissipate_SArea)
    delta_q_heatsink = q_in + q_dot_heatsink

    # Resolve temps
    i_temp_panel_diss = i_temp_panel + (time*delta_q)/(mass*c_silicon)
    i_temp_heatsink_diss = i_temp_panel + (time*delta_q_heatsink)/((mass+total_bar_weight)*c_alum)

    # Append
    calc_panel_temp.append(i_temp_panel_diss)
    calc_heatsink_temp.append(i_temp_heatsink_diss)
    # print(idx, delta_q, i_temp_panel_diss, '---', q_dot_heatsink, i_temp_heatsink_diss)

    h =0

del calc_panel_temp[-1]
# del calc_panel_temp[-1]

gg = max(calc_panel_temp)
ggg = max(NREL_temp)

# =====================
# === Add heat sink ===
# =====================

hs_panel_eff = []
hs_panel_temp = []
num_under_RT = 0
num_over_RT = 0
hs_power = []
hs_power_sum = 0
trapezoid = 0
values_temp_year1_max = max(calc_panel_temp)

# For loop
for ii,value in enumerate(calc_panel_temp):

    if value < room_temp:
        hs_panel_temp.append(value)
        hs_panel_eff.append(100)
        ii_power = calc_pwr_per_time[ii]
        num_under_RT += 1
    else:
        scaled_value = value -(((value-room_temp)/(values_temp_year1_max-room_temp)) * dissapation_delta )
        hs_panel_temp.append(scaled_value)

        ii_panel_eff = (100+((value-scaled_value)*eff_per_degree)) / 100
        hs_panel_eff.append(ii_panel_eff)
        ii_power = calc_pwr_per_time[ii]*ii_panel_eff
        num_over_RT += 1

    hs_power.append(ii_power)

    # sum power 
    if ii > 0:
        time = abs(NREL_datetime[ii]-NREL_datetime[ii-1]).total_seconds() / 3600
        trapezoid = ( (hs_power[ii] + hs_power[ii-1]) / 2 ) * time
        hs_power_sum += trapezoid

    if trapezoid > 0:
        h = 0


# ========================
# === Calculate 2 ===
# ========================

calc_power_sum = 0

for idx,this_power in enumerate(calc_pwr_per_time):

    if idx+2 <= len(calc_pwr_per_time):
        # Only if same day, if new day its over night
        if NREL_datetime[idx+1].day == NREL_datetime[idx].day:
            time = abs(NREL_datetime[idx+1]-NREL_datetime[idx]).total_seconds() / 3600
            trapezoid = ( (calc_pwr_per_time[idx] + calc_pwr_per_time[idx+1]) / 2 ) * time
            calc_power_sum += trapezoid

money_per_year = calc_power_sum/1000 * price_per_kWh

kWhr_saved = (hs_power_sum - calc_power_sum)/1000 # kW-hr

money_saved = (kWhr_saved)*price_per_kWh

ratio = money_saved / money_per_year

# === Plot ===

fig, ax1 = plt.subplots()
ax1.scatter(NREL_datetime,calc_panel_temp, color='r')
ax1.scatter(NREL_datetime,NREL_temp, color='b')


fig.suptitle('Temp vs date')

ax1.set(xlabel='Date-time', ylabel='Temperature C')
ax1.grid()

plt.show()


h =0