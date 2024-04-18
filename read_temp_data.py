import datetime as dt
import matplotlib.pyplot as plt
from scipy import integrate
# from datetime import datetime

filename = 'test_20240414.txt'
price_per_kWh = 0.23 # dollars
print(price_per_kWh)

def read_temp_data(filename):

    data_dict = {'time':[], 'seconds':[]
                 ,'nyc_front':[],'nyc_back':[],
                 'venice_front':[],'venice_back':[],
                 'wichita_front':[],'wichita_back':[],
                 'orvieto_front':[],'orvieto_back':[],
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
                data_dict['nyc_front'].append( temp_value )
            elif i_temp == '1':
                temp_value = int(split_2[idx_temp+1]) / 100
                data_dict['nyc_back'].append( temp_value )
            elif i_temp == '3':
                temp_value = int(split_2[idx_temp+1]) / 100
                data_dict['venice_front'].append( temp_value )
            elif i_temp == '4':
                temp_value = int(split_2[idx_temp+1]) / 100
                data_dict['venice_back'].append( temp_value )
            elif i_temp == '5':
                temp_value = int(split_2[idx_temp+1]) / 100
                data_dict['wichita_front'].append( temp_value )
            elif i_temp == '6':
                temp_value = int(split_2[idx_temp+1]) / 100
                data_dict['wichita_back'].append( temp_value )
            elif i_temp == '7':
                temp_value = int(split_2[idx_temp+1]) / 100
                data_dict['orvieto_front'].append( temp_value )
            elif i_temp == '8':
                temp_value = int(split_2[idx_temp+1]) / 100
                data_dict['orvieto_back'].append( temp_value )
            elif i_temp == '9':
                temp_value = int(split_2[idx_temp+1]) / 100
                data_dict['control_front'].append( temp_value )
            elif i_temp == '10':
                temp_value = int(split_2[idx_temp+1]) / 100
                data_dict['control_back'].append( temp_value )
            elif i_temp == '11':
                temp_value = int(split_2[idx_temp+1]) / 100
                data_dict['ambient'].append( temp_value )

        g=0

    # --- Temp compare ---
    money_saved_dict = {}
    for key,comare_data in data_dict.items():
        if 'front' in key and 'control' not in key:
            output = money_saved(data_dict['ambient'],comare_data,data_dict['seconds'])
            money_saved_dict[key] = round(output,3)

    # === Plot ===
    fig, ax1 = plt.subplots()

    plot_front = False
    ax1.plot(data_dict['time'],data_dict['ambient'], color='black', label='ambient')
    if plot_front:
        ax1.plot(data_dict['time'],data_dict['nyc_front'], color='blue', label='nyc_front') # 0
        ax1.plot(data_dict['time'],data_dict['venice_front'], color='r', label='venice_front')
        ax1.plot(data_dict['time'],data_dict['wichita_front'], color='orange', label='wichita_front')
        ax1.plot(data_dict['time'],data_dict['orvieto_front'],color='g', label='orvieto_front')
        # ax1.plot(data_dict['time'],data_dict['control_front'], color='peru', label='control_front',linewidth=7.0)
        plt.title("Front side of panel temperatures")

    plot_back = True
    if plot_back:
        ax1.plot(data_dict['time'],data_dict['nyc_back'], color='blue',linestyle = 'dashed', label='nyc_back')
        ax1.plot(data_dict['time'],data_dict['venice_back'], color='r',linestyle = 'dashed', label='venice_back')
        ax1.plot(data_dict['time'],data_dict['wichita_back'], color='orange',linestyle = 'dashed', label='wichita_back') # 5
        ax1.plot(data_dict['time'],data_dict['orvieto_back'], color='g',linestyle = 'dashed', label='orvieto_front')
        ax1.plot(data_dict['time'],data_dict['control_back'], color='peru',linestyle = 'dashed', label='control_back',linewidth=7.0)
        plt.title("Back side of panel temperatures")
    
    
    ax1.legend()
    plt.show()
    g=0

# === Sub functions =====

def money_saved(ambient_data,compare_data,seconds_data):

    # F to C
    theoretical_c = [(fahr - 32) * 5 / 9 for fahr in ambient_data]
    experimental_c =  [(fahr - 32) * 5 / 9 for fahr in compare_data]

    theoretical_power_loss  = [(100 - ((val-72)*0.5))*3.05 for val in theoretical_c]
    experimental_power_loss = [(100 - ((val-72)*0.5))*3.05 for val in experimental_c]

    theoretical_power_inte = integrate.trapezoid(theoretical_power_loss,seconds_data)
    experimental_power_inte = integrate.trapezoid(experimental_power_loss,seconds_data)

    tot_power_diff = experimental_power_inte - theoretical_power_inte
    in_kWh = tot_power_diff/1000/3600
    in_dollars = in_kWh*price_per_kWh*200*5

    b = theoretical_power_inte/1000/3600*200*5
    
    return in_dollars


read_temp_data(filename)
