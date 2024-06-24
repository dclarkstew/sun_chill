import datetime as dt
import matplotlib.pyplot as plt
import matplotlib.ticker as tck
from scipy import integrate
import numpy as np
from matplotlib import colormaps
import pandas as pd
import os

arr = os.listdir()

filename = 'test_20240414_cleanedup.txt'
price_per_kWh = 0.16 # dollars
eff_loss_per_degree = 0.306 # %
SP_power_rating = 305 # Watts

# --- Temperature data file ---
filename = r'c:\Users\dclar\Documents\Solar Panels\Helios\test_data\2024-06-16 to 2024-06-18 TC.xlsx'
day1_sunrise = dt.datetime(year=2024,month=6,day=17,hour=5,minute=32)
day1_sunset = dt.datetime(year=2024,month=6,day=17,hour=20,minute=31)
day2_sunrise = dt.datetime(year=2024,month=6,day=18,hour=5,minute=32)
day2_sunset = dt.datetime(year=2024,month=6,day=18,hour=20,minute=31)

def main(filename):
    temp_over_time_dict = read_data_to_dict(filename)

    days_rise_set = [ [day1_sunrise,day1_sunset] , [day2_sunrise,day2_sunset] ]
    data_per_day_list = split_dict_by_day(temp_over_time_dict,days_rise_set)

    # --- Temp compare ---
    temp_saved_list = []
    power_saved_list = []
    percent_saved_list = []
    money_saved_list = []
    percent_saved_list = []
    
    for idx_day_dict,i_day_dict in enumerate(data_per_day_list): 
        plot_temp_vs_time(i_day_dict)

        # --- Analysis ---
        temp_saved_list.append({})
        power_saved_list.append({})
        money_saved_list.append({})
        percent_saved_list.append({})

        control_data = i_day_dict['controlS']
        seconds_data = i_day_dict['seconds']

        for key,comare_data in i_day_dict.items():
            if key not in ['time','control','seconds']:
                recovered_percent, recovered_kwh, recovered_temp = money_saved(control_data,comare_data,seconds_data)
                money_saved_list[idx_day_dict][key] = round(recovered_percent,3)
                percent_saved_list[idx_day_dict][key] = round(recovered_percent,2)
                power_saved_list[idx_day_dict][key] = round(recovered_kwh,2)
                temp_saved_list[idx_day_dict][key] = round(recovered_temp,2)

    return percent_saved_list

def split_dict_by_day(temp_over_time_dict,days_rise_set):

    num_days = len(days_rise_set)
    data_per_day_dict = {'time':[], 'seconds':[],
                 'control':[],
                 '1/8" flat plate':[],
                 '1/2" x 1/2" x 3" bars':[],
                 '1/4" Honeycomb\nGrid Core':[],
                 '1/8" x 3" fins':[]
                }
    
    data_per_day_dict2 = {'time':[], 'seconds':[],
                 'control':[],
                 '1/8" flat plate':[],
                 '1/2" x 1/2" x 3" bars':[],
                 '1/4" Honeycomb\nGrid Core':[],
                 '1/8" x 3" fins':[]
                }

    data_per_day_list = [data_per_day_dict, data_per_day_dict2]
    for idx_time, i_time in enumerate(temp_over_time_dict['time']):

        for idx_day,i_day in enumerate(days_rise_set):

            if i_day[0] <= i_time <= i_day[1]:

                for key,comare_data in temp_over_time_dict.items():
                    data_per_day_list[idx_day][key].append(temp_over_time_dict[key][idx_time])

    return data_per_day_list


def read_data_to_dict(filename):
    # --- Read in file ---
    temp_over_time_dict = {'time':[], 'seconds':[],
                 'control':[],
                 '1/8" flat plate':[],
                 '1/2" x 1/2" x 3" bars':[],
                 '1/4" Honeycomb\nGrid Core':[],
                 '1/8" x 3" fins':[]
                }

    with pd.ExcelFile(filename) as xls:  
        df1 = pd.read_excel(xls, "Sheet1")

    # --- Rename keys ---
    temp_data_dict = df1.to_dict()
    new_keys = ['SN','DATE','TIME','T1','T2','T3','T4','T5','T6','T7','T8']
    for key,n_key in zip(temp_data_dict.keys(), new_keys):
        temp_data_dict[n_key] = temp_data_dict.pop(key)
        temp_data_dict[n_key] = list(temp_data_dict[n_key].values())[3:]

    # --- Combine datetime ---
    date,time = temp_data_dict['DATE'],temp_data_dict['TIME']
    temp_data_dict['dt'] = []
    for idx in range(len(date)):
        idx_date = date[idx]
        idx_time = time[idx]
        temp_data_dict['dt'].append(idx_date + dt.timedelta(hours=idx_time.hour,minutes=idx_time.minute,seconds=idx_time.second))

    # --- Now combine the multi read TCs ---
    temp_over_time_dict['time'] = temp_data_dict['dt']
    temp_over_time_dict['control'] = [(temp_data_dict['T1'][i] + temp_data_dict['T8'][i]) / 2 for i in range(len(temp_data_dict['T1']))]
    temp_over_time_dict['1/8" flat plate'] = temp_data_dict['T3']
    temp_over_time_dict['1/2" x 1/2" x 3" bars'] = temp_data_dict['T2']
    temp_over_time_dict['1/4" Honeycomb\nGrid Core'] = [(temp_data_dict['T6'][i] + temp_data_dict['T7'][i]) / 2 for i in range(len(temp_data_dict['T6']))]
    temp_over_time_dict['1/8" x 3" fins'] = [(temp_data_dict['T4'][i] + temp_data_dict['T5'][i]) / 2 for i in range(len(temp_data_dict['T4']))]

    # --- Time (seconds) ---
    t0_dt = temp_over_time_dict['time'][0]
    for i_time in temp_over_time_dict['time']:
        sec_from_start = (i_time - t0_dt).total_seconds()
        temp_over_time_dict['seconds'].append(sec_from_start)

    return temp_over_time_dict

    g=0


def plot_temp_vs_time(data_dict):

    # === Plot ===
    fig, ax1 = plt.subplots()

    plot_colors_dict = {'time':[], 'seconds':[],
                 'control':'black',                      
                 '1/8" flat plate':'red',
                 '1/2" x 1/2" x 3" bars': 'blue',
                 '1/4" Honeycomb\nGrid Core':'yellow',
                 '1/8" x 3" fins':'green',
                 }
    
    for key,comare_data in data_dict.items():
        if key not in ['time','seconds']:
            ax1.plot(data_dict['time'],data_dict[key], label=key,linewidth=3, color=plot_colors_dict[key]) # 0

    plt.title("Temperature vs Time")

    ax1.legend()
    plt.show()


def plot_experimental_data(ordered_design_names, percent_saved_list,data_dict,power_saved_list,temp_saved_list):

    # === Plot ===
    if True:
        fig, ax2  = plt.subplots()

        # --- Font ---
        SMALL_SIZE = 8
        MEDIUM_SIZE = 10
        BIGGER_SIZE = 12

        plt.rc('font', size=12)          # controls default text sizes
        plt.rc('axes', titlesize=40)     # fontsize of the axes title
        plt.rc('axes', labelsize=40)    # fontsize of the x and y labels
        plt.rc('xtick', labelsize=40)    # fontsize of the tick labels
        plt.rc('ytick', labelsize=40)    # fontsize of the tick labels
        plt.rc('legend', fontsize=40)    # legend fontsize
        plt.rc('figure', titlesize=20)  # fontsize of the figure title
        
        bar_legend_name = ['red', 'blue', 'green', 'orange']
        bar_colors = ['#84cfb9','#51b689','#2c9553','#05712f']

        bars = ax2.bar(ordered_design_names, percent_saved_list, color=bar_colors, label=ordered_design_names)

        ax2.set_ylabel('% gained', fontsize=20, fontweight='bold')
        
        # --- Figure Title ---
        time_start = data_dict['time'][0]
        time_end = data_dict['time'][-1]
        ax2.set_title('Percent efficiency gained by design\n('+ str(time_start) + ' to ' + str(time_end) + ')',fontsize=28,fontweight='bold') 

        # ax2.legend(title='Design')

        ax2.grid(visible=True, which='major', axis='y',color='green', linestyle='-', linewidth = 1.5)
        ax2.grid(visible=True, which='minor', axis='y',color='lime', linestyle='--')
        ax2.set_axisbelow(True)

        # --- Y axis ---
        ax2.tick_params(axis='y', labelsize=20)
        ax2.yaxis.set_minor_locator(tck.AutoMinorLocator())

        # --- X axis ---
        ax2.tick_params(axis='x', labelsize=20)
        plt.xticks(ordered_design_names, weight = 'bold')

        # --- Add column values ---
        for i, v in enumerate(percent_saved_list):
            ax2.text(i-.38, v-.4, str(v)+'%\n' + str(power_saved_list[i]) + ' kWh\n' + str(temp_saved_list[i]) + ' °C', 
                    color='black', 
                    #  fontweight='bold', 
                    verticalalignment='center',
                    fontsize=24)
        
        plt.show()
        g=0

# === Sub functions =====

def money_saved(ambient_data,compare_data,seconds_data):
    
    control_max_possible_power = []
    for i_frame in ambient_data:
        if i_frame > 25:
            frame_max_power = (100 - ((i_frame-25)*eff_loss_per_degree))*SP_power_rating/100
        else:
            frame_max_power = SP_power_rating
        control_max_possible_power.append(frame_max_power)

    variable_max_possible_power = []
    for i_frame in compare_data:
        if i_frame > 25:
            frame_max_power = (100 - ((i_frame-25)*eff_loss_per_degree))*SP_power_rating/100
        else:
            frame_max_power = SP_power_rating
        variable_max_possible_power.append(frame_max_power)

    # --- Power ---
    control_power_inte = integrate.trapezoid(control_max_possible_power,x=seconds_data)
    variable_power_inte = integrate.trapezoid(variable_max_possible_power,x=seconds_data)

    # --- Temperature ---
    control_temp_inte = integrate.trapezoid(ambient_data,seconds_data) / seconds_data[-1]
    variable_temp_inte = integrate.trapezoid(compare_data,seconds_data) / seconds_data[-1]
    recovered_temp = control_temp_inte - variable_temp_inte

    tot_power_diff = variable_power_inte - control_power_inte
    in_kWh = tot_power_diff/1000/3600

    recovered_kwh = round(in_kWh,2)
    recovered_percent = round(tot_power_diff / control_power_inte * 100,3)
    
    # --- Savings in dollar ---
    in_dollars = in_kWh*price_per_kWh*200*5
    b = control_power_inte/1000/3600*200*5
    
    return recovered_percent, recovered_kwh, recovered_temp
    # return in_dollars

def c_to_f(C_value):
    temp_value = int(C_value) / 100
    f_value = (temp_value - 32) * 5/9
    return f_value

if __name__ == "__main__":
    main(filename)
