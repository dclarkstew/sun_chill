import numpy as np
import pandas
import datetime as dt
import matplotlib.pyplot as plt
import csv
from datetime import datetime
from scipy import integrate
import matplotlib.patches as mpatches


# Local imports
import read_temp_data as read_temp_data # type: ignore
# from heat_sink_design import heat_sink_design

# --- NREL historical data ---
# nrel_directory = r'C:\Users\dclar\Documents\Solar Panels\python_analysis\theoretical\\'
nrel_directory = r'C:\Users\dclar\Documents\Solar Panels\Helios\nrel_data\\'
NREL_files = ['denver_1947888_39.74_-105.03_2022_localTime.csv',
            'phoenix_1309015_33.44_-112.05_2022_localTime.csv',
            'atlanta_3894477_33.80_-84.39_2022_localTime.csv',
            'sahara_487671_22.77_5.54_2019_localTime.csv',         # Tamanrasset, Algeria
            'brussels_454991_50.85_4.34_2019_localTime.csv']
 
# === Solar Panel Inputs ===
# https://es-media-prod.s3.amazonaws.com/media/components/panels/spec-sheets/HyundaiEnergySolutions_HiA-SXXXHG_M2_300_315W_xSe5w2v.pdf
sp_area_sqft = (5.5*3.5) # sqft
sqft_to_m2 = 0.0928790337119164
sp_area_m2 = 0.992 * 1.675 # (39.06"x65.94")
SP_power_rating = 305 # Watts
SP_efficiency = 0.184 # %
eff_loss_per_degree = 0.0306 # %
price_per_kWh = 0.136 # dollars

# --- Constants ---
# Specific heat capacity (J/g-C)
c_silicon = 0.705 # Silicon
c_alum = 0.897 # Aluminium

# Heat transfer coefficient (W/m-K)
k_silicon = 0.2 # Silicon
k_alum = 237 # Aluminum

# Room temperature
room_temp = 25 # Celcius

def main():

    # --- Local module calls ---
    # filename = 'test_20240414_cleanedup.txt'
    filename = r'c:\Users\dclar\Documents\Solar Panels\Helios\test_data\2024-06-16 to 2024-06-18 TC.xlsx'
    percent_saved_list = read_temp_data.main(filename)

    # === Heatsink costs ===
    heatsink_build_costs = {
        '1/8" flat plate' : 3837.58,
        '1/2" x 1/2" x 3" bars' : 5788.46,
        '1/4" Honeycomb Grid Core' : 4159.33,
        '1/8" x 3" fins' : 4119.17
    }

    # --- Read in NREL data ---
    nrel_dict = read_nrel_data()

    # --- Sum over the whole year ---
    for i_percent_saved_dict in percent_saved_list:
        power_sum_dict, money_sum_dict = sum_changes_yearly(nrel_dict,i_percent_saved_dict)

        # --- Difference from ambient dict ---
        money_diff_dict_location_deisgn = {}
        for key,i_location_data in money_sum_dict.items():
            ambient_generation = money_sum_dict[key]['ambient']

            money_diff_dict_location_deisgn[key] = {}
            for key2,i_design_value in i_location_data.items():
                money_diff_dict_location_deisgn[key][key2] = round(i_design_value - ambient_generation,2)

        # --- Rearrange diff dict ---
        # money_diff_dict_design_location = {key:{k:money_diff_dict_location_deisgn[k][key] for k in money_diff_dict_location_deisgn if key in money_diff_dict_location_deisgn[k]} for key in ordered_design_names}

        plot_savings_by_location(money_diff_dict_location_deisgn)

        # === Revenue over time ===
        number_of_panels = 20000
        chosen_location = 'phoenix'
        chosen_design = '1/8" x 3" fins'
        increase_per_panel_exp = money_sum_dict[chosen_location][chosen_design]
        increase_per_panel_baseline = money_sum_dict[chosen_location]['ambient']
        increase_per_panel_optimal = increase_per_panel_baseline * 1.1075
        
        lifetime_revenue_baseline = [0]
        lifetime_revenue_experimental = [0]
        lifetime_revenue_optimal = [0]
        x_axis = [0]
        for i_year in range(1,31):
            lifetime_revenue_baseline.append(increase_per_panel_baseline*i_year*number_of_panels)
            lifetime_revenue_experimental.append(increase_per_panel_exp*i_year*number_of_panels)
            lifetime_revenue_optimal.append(increase_per_panel_optimal*i_year*number_of_panels)
            x_axis.append(i_year)

        farm_power_output = SP_power_rating * number_of_panels
        plot_revenue_over_time(lifetime_revenue_baseline,lifetime_revenue_experimental,lifetime_revenue_optimal,x_axis,SP_power_rating, number_of_panels)


def read_nrel_data():
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
            
    return nrel_dict


def sum_changes_yearly(nrel_dict,percent_saved_dict):
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
        for i_heatsink,saved_amount in percent_saved_dict.items():
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
            for i_heatsink,saved_amount in percent_saved_dict.items():
                heatsink_scaled_power_kwh = integrated_kwh * (1+percent_saved_dict[i_heatsink]/100)

                power_sum_dict[key][i_heatsink] += heatsink_scaled_power_kwh
                money_sum_dict[key][i_heatsink] += heatsink_scaled_power_kwh * price_per_kWh
        
    return power_sum_dict, money_sum_dict


# === Plot ===
def plot_savings_by_location(money_diff_dict):

    fig, ax = plt.subplots()

    color_dict = {'control_outside': '#bde6de',
                  '1/8" flat plate': '#84cfb9',
                  '1/2" x 1/2" x 3" bars': '#51b689',
                  '1/4" Honeycomb\nGrid Core': '#2c9553',
                  '1/8" x 3" fins':'#05712f'}
    
    loc_dict = {'brussels':'Brussels, Belgium',
                'atlanta':'Atlanta, GA',
                'denver':'Denver, CO',
                'sahara':'Tamanrasset, Algeria\n(Sahara Desert)',
                'phoenix': 'Phoenix, AZ'}
    
    location_order = ['brussels','atlanta','sahara','denver','phoenix']

    plot_dict = {}
    x_pos = 0
    for loc_idx,key in enumerate(location_order):
    
        i_design_data = money_diff_dict[key]

        plot_dict[key] = {}
        plot_dict[key]['x_vals'] = []
        plot_dict[key]['y_vals'] = []
        for key2,i_location_value in i_design_data.items():

            val_rounded = round(i_location_value,2)

            if val_rounded == 0 or key2 == 'control_inside':
                continue

            # --- Bar plotting ---
            ax.bar(x_pos,val_rounded ,color=color_dict[key2])

            # --- Text formatting ---
            val_rounded_str = str(val_rounded)
            split_decimal = str(val_rounded_str).split('.')
            if len(split_decimal[1]) == 1:
                val_rounded_str = val_rounded_str + '0'
            display_text = '$' + val_rounded_str
            ax.text(x_pos-.4,val_rounded+.05,display_text, fontweight='bold',ha='left')

            x_pos += 1

        # --- Add location separations ---
        if x_pos != 24:
            ax.axvline(x_pos, color='black', linestyle='dashed',label = 'Stop/Start')
        ax.text(x_pos-2.5,4.65,loc_dict[key].upper(),fontsize = 'x-large',fontweight='bold',ha='center',va='center')


        ax.bar(x_pos,0)
        x_pos += 1

    # --- Title ---
    ax.set_title('Estimated Savings from Heat Sinks in a Year',fontsize=28,fontweight='bold')

    # --- All other stuff ---
    ax.grid(True)
    ax.set_axisbelow(True)

    # --- X axis ---
    ax.set_xticklabels([])
    ax.set_xlim([-1, x_pos-1])
    ax.grid(which='major',visible=False,axis='x')
    # ax.set_xlabel('')

    # --- Y axis ---
    ax.set_ylabel('Dollars Saved ($)',fontweight='bold',fontsize=20)
    ax.set_ylim([0, 5.1])
    ax.set_yticks([0,1,2,3,4,5],labels=['$0.00','$1.00','$2.00','$3.00','$4.00','$5.00'])

    # --- Legend --- 
    leg = ax.get_legend()
    legend_properties = {'weight':'bold'}

    
    ghetto_list = []
    for key,value in color_dict.items():

        if key == 'ambient':
            continue

        loc_patch = mpatches.Patch(color=value, label=key)
        ghetto_list.append(loc_patch)
    plt.legend(handles=ghetto_list, loc=(.01,.55),
               fancybox=True, shadow=True,
               prop=legend_properties)

    # --- Add Location text ---
    # for idx,i_loc in enumerate(['Brussels','Atlanta','Denver','Sahara','Phoenix']):
    #     ax.text(idx,10,i_loc, fontsize=20)

    plt.show()

    d=0


def plot_revenue_over_time(revenue_baseline,revenue_exp,revenue_optimal,x_axis,SP_power_rating, number_of_panels):

    fig, ax = plt.subplots()

    color1 = 'black'
    color2 = '#0b84a5' 
    color3 = '#216d41'

    ax.plot(x_axis,revenue_baseline,color=color1)
    ax.plot(x_axis,revenue_exp,color=color2)
    ax.plot(x_axis,revenue_optimal,color=color3)

    # --- Text with difference ---
    x_offset = 0.7
    for ii in [1,5,10,15,20,25,30]:
        ax.vlines(ii,revenue_exp[ii]-7e6,revenue_exp[ii]+7e6,linestyles='dashed',linewidth=2,color='black')

        if ii == 5:
            x_offset = 1.4

        # --- Unmodified returns ---
        if revenue_exp[ii] < 1e6:
            base_val = round(revenue_exp[ii]/1e3)
            base_val_str = '+$' + str(base_val) + 'k'
        else:
            base_val = round(revenue_exp[ii]/1e6,2)
            base_val_str = '$' + str(base_val) + 'M'
        ax.text(ii-x_offset,revenue_exp[ii]+7.9e6,base_val_str, fontsize=20,c=color1)

        # --- Experimental increase ---
        exp_inc = revenue_exp[ii] - revenue_baseline[ii]
        if exp_inc < 1e6:
            exp_inc2 = round(exp_inc/1e3)
            exp_inc_str = '+$' + str(exp_inc2) + 'k'
        else:
            exp_inc2 = round(exp_inc/1e6,2)
            exp_inc_str = '+$' + str(exp_inc2) + 'M'
        ax.text(ii-x_offset,revenue_exp[ii]+10.9e6,exp_inc_str, fontsize=20,c=color2)

        # --- Optimal increase ---
        exp_inc = revenue_optimal[ii] - revenue_baseline[ii]
        print(exp_inc, 1e7)
        if exp_inc < 1e6:
            exp_inc2 = round(exp_inc/1e3)
            exp_inc_str = '+$' + str(exp_inc2) + 'k'
        else:
            exp_inc2 = round(exp_inc/1e6,2)
            exp_inc_str = '+$' + str(exp_inc2) + 'M'
        ax.text(ii-x_offset,revenue_exp[ii]+13.9e6,exp_inc_str, fontsize=20,c=color3)
        
    # --- Title ---
    farm_power_output = str((SP_power_rating * number_of_panels)/1e6) + 'MW'
    title_str = 'Estimated Revenue Generated in Phoenix, AZ\nfrom a ' + farm_power_output + '/' + str(number_of_panels) + ' Panel Farm'
    ax.set_title(title_str,fontsize=28,fontweight='bold')
    
    # --- All other stuff ---
    ax.grid(True)
    ax.set_axisbelow(True)

    # --- Legend --- 
    leg = ax.get_legend()
    legend_properties = {#'weight':'bold',
                         'size': 18}
    leg_handles = [
        mpatches.Patch(color=color3, label='With Optimal Heat Sinks'),
        mpatches.Patch(color=color2, label='With Experimental Heat Sinks'),
        mpatches.Patch(color=color1, label='Unmodified Panel'),
    ]
    plt.legend(handles=leg_handles, loc=(.01,.65),
               fancybox=True, shadow=True,
               prop=legend_properties)


    # --- X axis ---
    ax.set_xlabel('Years',fontweight='bold',fontsize=24)
    ax.xaxis.set_label_coords(.475, -.075)
    ax.set_xlim(left=0)
    plt.xticks([1,5,10,15,20,25,30], weight = 'normal',fontsize=18)

    # --- Y axis ---
    ax.set_ylabel('USD ($)',fontweight='bold',fontsize=24)
    ax.set_ylim(0,7.7e7)
    ax.set_yticks([1e7,2e7,3e7,4e7,5e7,6e7,7e7,8e7],labels=['$10M','$20M','$30M','$40M','$50M','$60M','$70M','$80M'],weight='normal',fontsize=18)

    plt.show()
    g=0

if __name__ == "__main__":
    main()
