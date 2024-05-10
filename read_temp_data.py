import datetime as dt
import matplotlib.pyplot as plt
import matplotlib.ticker as tck
from scipy import integrate
# import plotly.express as px
# from datetime import datetime

import os

arr = os.listdir()

filename = 'test_20240414_cleanedup.txt'
price_per_kWh = 0.16 # dollars
eff_loss_per_degree = 0.306 # %
SP_power_rating = 305 # Watts

def read_temp_data(filename):

    data_dict = {'time':[], 'seconds':[]
                 ,'nyc_front':[],'nyc_back':[],
                 'venice_front':[],'venice_back':[],
                 'wichita_front':[],'wichita_back':[],
                 'behive_front':[],'behive_back':[],
                 'control_front':[],'control_back':[],
                 'ambient':[]}

    f = open(filename, "r")
    lines = f.readlines()
    for i_line in lines:

        # --- Time (datetime) ---
        split_1 = i_line.split(' -> ')
        no_milli = split_1[0].split('.')
        i_time = dt.datetime.strptime(no_milli[0],'%H:%M:%S')
        i_time = i_time.replace(year=2024,month=4,day=14)
        data_dict['time'].append(i_time)

        # --- Time (seconds) ---
        sec_from_start = (i_time - data_dict['time'][0]).seconds
        data_dict['seconds'].append(sec_from_start)

        i_temp_data_raw = split_1[1]
        split_2 = i_temp_data_raw.split(',')
        for idx_temp,i_temp in enumerate(split_2):
            split_2[idx_temp] = i_temp.replace(' ','')
            i_temp = split_2[idx_temp]
            
            if i_temp == '0' and idx_temp != 5:
                temp_value = int(split_2[idx_temp+1]) / 100
                temp_value = (temp_value - 32) * 5/9
                data_dict['nyc_front'].append( temp_value )
            elif i_temp == '1':
                temp_value = int(split_2[idx_temp+1]) / 100
                temp_value = (temp_value - 32) * 5/9
                data_dict['nyc_back'].append( temp_value )
            elif i_temp == '3':
                temp_value = int(split_2[idx_temp+1]) / 100
                temp_value = (temp_value - 32) * 5/9
                data_dict['venice_front'].append( temp_value )
            elif i_temp == '4':
                temp_value = int(split_2[idx_temp+1]) / 100
                temp_value = (temp_value - 32) * 5/9
                data_dict['venice_back'].append( temp_value )
            elif i_temp == '5':
                temp_value = int(split_2[idx_temp+1]) / 100
                temp_value = (temp_value - 32) * 5/9
                data_dict['wichita_front'].append( temp_value )
            elif i_temp == '6':
                temp_value = int(split_2[idx_temp+1]) / 100
                temp_value = (temp_value - 32) * 5/9
                data_dict['wichita_back'].append( temp_value )
            elif i_temp == '7':
                temp_value = int(split_2[idx_temp+1]) / 100
                temp_value = (temp_value - 32) * 5/9
                data_dict['behive_front'].append( temp_value )
            elif i_temp == '8':
                temp_value = int(split_2[idx_temp+1]) / 100
                temp_value = (temp_value - 32) * 5/9
                data_dict['behive_back'].append( temp_value )
            elif i_temp == '9':
                temp_value = int(split_2[idx_temp+1]) / 100
                temp_value = (temp_value - 32) * 5/9
                data_dict['control_front'].append( temp_value )
            elif i_temp == '10':
                temp_value = int(split_2[idx_temp+1]) / 100
                temp_value = (temp_value - 32) * 5/9
                data_dict['control_back'].append( temp_value )
            elif i_temp == '11':
                temp_value = int(split_2[idx_temp+1]) / 100
                temp_value = (temp_value - 32) * 5/9
                data_dict['ambient'].append( temp_value )


    # --- Temp compare ---
    power_saved_list = []
    money_saved_list = []
    money_saved_dict = {}
    for key,comare_data in data_dict.items():
        if 'front' in key and 'control' not in key:
            output1, recovered_kwh = money_saved(data_dict['ambient'],comare_data,data_dict['seconds'])
            money_saved_dict[key] = round(output1,3)
            money_saved_list.append(round(output1,2))
            power_saved_list.append(round(recovered_kwh,2))
    money_saved_list.sort()

    # === Plot ===
    # fig, ax1 = plt.subplots()

    # plot_front = False
    # ax1.plot(data_dict['time'],data_dict['ambient'], color='black', label='ambient')
    # if plot_front:
    #     ax1.plot(data_dict['time'],data_dict['nyc_front'], color='blue', label='nyc_front') # 0
    #     ax1.plot(data_dict['time'],data_dict['venice_front'], color='r', label='venice_front')
    #     ax1.plot(data_dict['time'],data_dict['wichita_front'], color='orange', label='wichita_front')
    #     ax1.plot(data_dict['time'],data_dict['behive_front'],color='g', label='behive_front')
    #     # ax1.plot(data_dict['time'],data_dict['control_front'], color='peru', label='control_front',linewidth=7.0)
    #     plt.title("Front side of panel temperatures")

    # plot_back = False
    # if plot_back:
    #     ax1.plot(data_dict['time'],data_dict['nyc_back'], color='blue',linestyle = 'dashed', label='nyc_back')
    #     ax1.plot(data_dict['time'],data_dict['venice_back'], color='r',linestyle = 'dashed', label='venice_back')
    #     ax1.plot(data_dict['time'],data_dict['wichita_back'], color='orange',linestyle = 'dashed', label='wichita_back') # 5
    #     ax1.plot(data_dict['time'],data_dict['behive_back'], color='g',linestyle = 'dashed', label='behive_front')
    #     ax1.plot(data_dict['time'],data_dict['control_back'], color='peru',linestyle = 'dashed', label='control_back',linewidth=7.0)
    #     plt.title("Back side of panel temperatures")
    
    # ax1.legend()
    # plt.show()
    # g=0

    # === Plot ===
    fig, ax2  = plt.subplots()
    
    bar_legend_name = ['red', 'blue', 'red', 'orange']
    bar_colors = ['tab:red', 'tab:blue', 'tab:red', 'tab:orange']

    money_saved_items = []
    for key,value in money_saved_dict.items():
        money_saved_items.append(key)
    bars = ax2.bar(money_saved_items, money_saved_list, label=bar_legend_name, color=bar_colors)

    ax2.set_ylabel('% gained')
    time_start = data_dict['time'][0]
    time_end = data_dict['time'][-1]

    ax2.set_title('Percent efficiency gained by design ('+ str(time_start) + ' to ' + str(time_end) + ')') #zzz have it say over
    ax2.legend(title='Design Name')

    ax2.grid(visible=True, which='major', axis='y',color='green', linestyle='-', linewidth = 1.5)
    ax2.grid(visible=True, which='minor', axis='y',color='lime', linestyle='--')
    ax2.set_axisbelow(True)
    ax2.tick_params(axis='y', which='minor', bottom=False)
    
    # bars = ax2.barh(indexes, values)
    # ax2.bar_label(bars)
    for i, v in enumerate(money_saved_list):
        ax2.text(i-.40, v + .075, str(v)+'% / '+str(power_saved_list[i])+' kWh', color='black', fontweight='bold', verticalalignment='center')
        # zzz also need to add average temperature saved. Use trapezoid method
    

    ax2.yaxis.set_minor_locator(tck.AutoMinorLocator())

    plt.show()
    
    g=0

# === Sub functions =====

def money_saved(ambient_data,compare_data,seconds_data):

    # F to C
    # theoretical_c = [(fahr - 32) * 5 / 9 for fahr in ambient_data]
    # experimental_c =  [(fahr - 32) * 5 / 9 for fahr in compare_data]

    theoretical_power_loss  = [(100 - ((val-25)*eff_loss_per_degree))*SP_power_rating/100 for val in ambient_data]
    experimental_power_loss = [(100 - ((val-25)*eff_loss_per_degree))*SP_power_rating/100 for val in compare_data]

    theoretical_power_inte = integrate.trapezoid(theoretical_power_loss,seconds_data)
    experimental_power_inte = integrate.trapezoid(experimental_power_loss,seconds_data)

    tot_power_diff = experimental_power_inte - theoretical_power_inte
    in_kWh = tot_power_diff/1000/3600

    recovered_kwh = round(in_kWh,2)
    recovered_percent = round(tot_power_diff / theoretical_power_inte * 100,3)
    
    # --- Savings in dollar ---
    in_dollars = in_kWh*price_per_kWh*200*5
    b = theoretical_power_inte/1000/3600*200*5
    
    return recovered_percent, recovered_kwh
    # return in_dollars


read_temp_data(filename)
