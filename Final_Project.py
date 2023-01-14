import csv
import pyodbc
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import matplotlib.dates as mdates
import dateutil
import math as math
import os
from scipy import ndimage
import boto3
import botocore
import holidays
import datetime
import tkinter as tk
from tkinter import *
import customtkinter
from tkcalendar import Calendar

root= tk.Tk()
DATA_FILES_DIR = r"C:\Users\Public\Project\Compared"
s3 = boto3.client('s3')
customtkinter.set_appearance_mode("Dark")
customtkinter.set_default_color_theme("blue")

class school:
  def __init__(self, name, student_num , sq_meters ,relig_background ,region):
    self.name = name
    self.student_num = student_num
    self.sq_meters = sq_meters
    self.relig_background=relig_background
    self.region=region

def event_detector(df):
    times = np.arange(0, len(df[0]), 1)
    df = np.array(df)[0]
    filtered = ndimage.median_filter(df, 3)
    plt.plot(times, filtered)
    t_positive = 0.3
    t_negative = -0.3
    delta_p = [np.round(filtered[i + 1] - filtered[i], 2) for i in range(0, len(filtered) - 1)]
    event_up = [i for i in range(0, len(delta_p)) if (delta_p[i] > t_positive)]
    event_down = [i for i in range(0, len(delta_p)) if (delta_p[i] < t_negative)]
    ev = np.zeros(len(df))
    event_2 = np.zeros(len(df))
    ev = [e + 1 if i in event_up else e for i, e in enumerate(ev)]
    ev = [e - 1 if i in event_down else e for i, e in enumerate(ev)]
    # plt.plot(times, ev)
    i = 0
    window_len = 7
    while i < len(ev):
        if ev[i] == 0:
            event_2[i] = 0
        if ev[i] == 1:
            idx = [i for i, e in enumerate(ev[i:i + window_len]) if e == 1]
            for j in range(0, window_len):
                if j == idx[-1]:
                    event_2[i + j] = 1
                else:
                    event_2[i + j] = 0
            i = i + (window_len - 1)
        if ev[i] == -1:
            idx = [i for i, e in enumerate(ev[i:i + window_len]) if e == -1]
            for j in range(0, window_len):
                if j == idx[0]:
                    event_2[i + j] = -1
                else:
                    event_2[i + j] = 0
            i = i + (window_len - 1)
        i = i + 1
    plt.plot(times, event_2)
    plt.show()
    return event_2


def gen_CSV(path, file_name):
    # connect to db
    con = pyodbc.connect(r'Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=' + os.path.join(path, file_name) + ';')
    cur = con.cursor()
    col_desc = list(cur.columns())
    table_names = []
    for b in col_desc:
        if b[2] not in table_names:
            table_names.append(b[2])
    c = [e for e in table_names if e[0:3] == 'RT ']
    # c= table_names[-1]
    # c = table_names[3:]
    rows = []
    for i, c in enumerate([e for e in table_names if e[0:3] == 'RT ']):
        sql = 'SELECT * FROM [{}]'.format(c)
        cur.execute(sql)
        if i == 0:
            rows.append([x[3] for x in col_desc if x[2] == c])  # headers
        for row in cur.fetchall():
            if row[0] != 0.0:
                rows.append(row)
        del rows[1]  # remove first row
    path_for_csv = os.path.join(os.getcwd())
    with open(os.path.join(DATA_FILES_DIR, '{}.csv'.format(file_name.split(".")[0])), 'w',
              newline='') as fou:  # file.split(".")[0]
        csv_writer = csv.writer(fou)  # default field-delimiter is ","
        csv_writer.writerows([e[1:] for e in rows])
    cur.close()
    con.close()


def get_data(path, file_name):  # also adds the Energy colums.
    gen_CSV(path, file_name)
    # with open(os.path.join(path,'{}.csv'.format(file_name.split(".")[0])), newline='') as csvfile:
    #   data = list(csv.reader(csvfile))
    # data = np.array(data)
    # add the energy columns
    # E=np.transpose(calc_energy())
    # E_titels= np.array(['E1','E2','E3'])
    # E_tot= np.vstack( (E_titels , E ))
    # data= np.hstack((data,E_tot))
    #return data



#def calc_phase_energy(df):
#    # phase = phase - 1  # match an index
#    # col_list_power = ["kW L1", "kW L2", "kW L3"]  # ["kW L2"]#["kW L1", "kW L2", "kW L3"]
#    # df = pd.read_csv("data.csv", usecols=col_list_power) #TODO: change to relevane file name instead of data.csv
#    Energ = []
#    sum = 0
#    for x in range(df.shape[0]):
#        sum = sum + df['kw'][x] #the second col is of power
#        Energ.append(sum)
#    return (Energ)

def calc_energy(df):
    sum = 0
    for x in range(df.shape[0]):
        sum = sum + df['kw'][x]
    return sum

def kwh_day_night(df):
    sum_day=0
    sum_night_1=0
    sum_night_2 = 0
    max_p_day=0
    max_p_night_1=0
    max_p_night_2 = 0
    max_i_day=5760
    max_i_night_1=1
    max_i_night_2 = 14400
    flag = 0
    start=0
    end=0
    jump_time=[0,0,0,0,0,0,0,0,0] #first column is night the second is day
    for i in range(df.shape[0]):
        if (i>1 and i<4322): ##(from 00:00:00 until 06:00:00)
            sum_night_1 = sum_night_1 + df['kw'][i]
            if max_p_night_1< df['kw'][i]:
                max_p_night_1 = df['kw'][i]
                max_i_night_1 = i
        if (i > 14800 and i < 17200):  ##(from 20:00 until 23:59)
            sum_night_2 = sum_night_2 + df['kw'][i]
            if max_p_night_2 < df['kw'][i]:
                max_p_night_2 = df['kw'][i]
                max_i_night_2 = i
            if df['kw'][i]>=0 and flag==1:
                flag=0
                end = i
        if i>5760 and i<11600:##(from 08:00 until 16:00)
            sum_day = sum_day + df['kw'][i]
            if max_p_day< df['kw'][i]:
                max_p_day = df['kw'][i]
                max_i_day=i
            if df['kw'][i]<=-2 and flag == 0:
                flag=1
                start = i
            elif df['kw'][i]>=0 and flag==1:
                flag=0
                end = i
    avg_p_night_1 = sum_night_1 / 4321
    avg_p_night_2 = sum_night_2 / 2400
    avg_p_day = sum_day / 5840
    if max_p_night_1>5+avg_p_night_1:
        jump_time[0]=df['timestamp'][max_i_night_1]
        jump_time[2]=1
    if max_p_night_2>7+avg_p_night_2:
        jump_time[7]=df['timestamp'][max_i_night_2]
        jump_time[8]=1
    if (max_p_day> 4*avg_p_day and avg_p_day > 0) or (avg_p_day < 0 and max_p_day> 15 + avg_p_day):
        jump_time[1]=df['timestamp'][max_i_day]
        jump_time[3] = 1
    if start>0:
        jump_time[4]=df['timestamp'][start]
        jump_time[5]=df['timestamp'][end]
        jump_time[6]=1
    return jump_time

def plot_param_2(slave,CSV_FLAG, columns, Ts,num,rep):
    phase_counter =0
    for i in range(1, len(columns)):
        if Ts >= 30:
            if Ts % 60 == 0:
                s_Ts = '{}[min]'.format(int(Ts / 60))
            else:
                s_Ts = '{}[min]'.format(Ts / 60)
        else:
            s_Ts = '{}[sec]'.format(int(Ts))
        files = os.listdir(DATA_FILES_DIR)
        plt.figure()  # for each parameter there is a seperate file
        for file_n, file in enumerate(files):
            if file.split('.')[1] != 'csv':  # if the files were originally mdb, go only over their csv copies
                continue
            with open(os.path.join(DATA_FILES_DIR, '{}.csv'.format(file.split(".")[0])), newline='') as csvfile:
                data = list(csv.reader(csvfile))
                df = pd.DataFrame(data)
                df = df.rename(columns=df.iloc[0, :])
                time = df.iloc[1:, 0]
                # time = [time[i][10:18] for i in range(len(time))]  # keep the '%H:%M:%S' only.
                time = [dateutil.parser.parse(s) for s in time]
                df = df.iloc[1:, 1:].apply(pd.to_numeric)  # the name row appears twice, so remove it
            dfs = df[columns[i]]  # the i'th parameter
            if columns[i] =="PF1" or columns[i] =="PF2" or columns[i] =="PF3":
                dfs= abs(dfs)
            if columns[i]=="Total kW":
                e_vals=[]
                ##dfs = abs(dfs)     some schools with power saving systems so P can be negative and its fine
                energy_df=pd.DataFrame(columns=['timestamp', 'kw'])
                energy_df['timestamp']=time
                energy_df['kw']=dfs.values
                e_vals=calc_energy(energy_df)
                slave.geometry("800x300")
                slave.title("Energy window")
                slave['bg'] = "white"
                temp=float(e_vals / 720)
                rounded=format(temp,".2f")
                label=Label(slave,bg='white',font=('century',12),text='Total Energy on date '+ str(time[0].day) +"-"+str(time[0].month)+ "-" + str(time[0].year)+ ' for school '+str(file[0:5]) +' is :'+ str(rounded) +' [KWH]')
                #label=Label(slave,bg='white',font=('century',12),text='school '+str (file[0:5])+': Energy in kWh for phase #'+str(phase_counter)+' on date '+str(time[0].day) +"-"+str(time[0].month)+ "-" + str(time[0].year)+" is: "+str(np.transpose(e_vals)[-1, :] / 3600))
                label.pack()
                jump_time = kwh_day_night(energy_df)
                if jump_time[2]>0:
                    str1 = str(jump_time[0].minute)
                    if (jump_time[0].minute < 10):
                        str1 = '0' + str(jump_time[0].minute)
                    label2 =Label(slave,bg='white',font=('century',12),fg='red',text='In '+str(file[0:5]) +' school on date '+ str(time[0].day) +"-"+str(time[0].month)+ "-" + str(time[0].year)+' unusual power consumption was encountered around time '+ str(jump_time[0].hour)+":" + str1)
                    label2.pack()
                if jump_time[8]>0 :
                    str2 = str(jump_time[7].minute)
                    if (jump_time[7].minute < 10):
                        str2 = '0' + str(jump_time[7].minute)
                    label2 =Label(slave,bg='white',font=('century',12),fg='red',text='In '+str(file[0:5]) +' school on date '+ str(time[0].day) +"-"+str(time[0].month)+ "-" + str(time[0].year)+' unusual power consumption was encountered around time '+ str(jump_time[7].hour)+":" + str2)
                    label2.pack()
                if jump_time[3]>0:
                    str3 = str(jump_time[1].minute)
                    if (jump_time[1].minute < 10):
                        str3 = '0' + str(jump_time[1].minute)
                    label3 =Label(slave,bg='white',font=('century',12),fg='red',text='In '+str(file[0:5]) +' school on date '+ str(time[0].day) +"-"+str(time[0].month)+ "-" + str(time[0].year)+' unusual power consumption was encountered around time '+ str(jump_time[1].hour)+":" + str3)
                    label3.pack()
                if jump_time[6]>0:
                    str4 = str(jump_time[4].minute)
                    str5 = str(jump_time[5].minute)
                    if (jump_time[4].minute < 10):
                        str4 = '0' + str(jump_time[4].minute)
                    if (jump_time[5].minute < 10):
                        str5 = '0' + str(jump_time[5].minute)
                    label4 =Label(slave,bg='white',font=('century',12),fg='green',text='In '+str(file[0:5]) +' school on date '+ str(time[0].day) +"-"+str(time[0].month)+ "-" + str(time[0].year)+' Energy accumulation was detected between '+ str(jump_time[4].hour)+":" + str4 + " and "+ str(jump_time[5].hour)+":" + str5)
                    label4.pack()
            ax = plt.subplot(len(files), 1, file_n + 1)
            plt.subplots_adjust(hspace=0.8)
            first =file[6:10]+'/' +file[10:12] + '/' + file[12:14] +' ' + file[14:16] + ':'+ file[16:18]
            second =file[19:23]+'/' +file[23:25] + '/' + file[25:27] +' ' + file[27:29] + ':'+ file[29:31]
            if(file !='merged.csv'):
                ax.title.set_text(columns[i] + ' of school ' +file[0:5] +' from '+ first +' to '+ second)
            else:
                ax.title.set_text(columns[i] + ' of ' + file)
            plt.step(time, dfs)  # 'step' is the zero order interpolation plot function.
            # plt.plot(time, dfs, color=colors[i])
            plt.xlabel("Time [h:m]")
            # plt.suptitle("{}".format(suptitle)) #("{}{}".format(suptitle,i))
            ##plt.xticks(time[0:len(time):int(num)*1440])  # how many x values to display 8->800
            ax.xaxis.set_minor_locator(mdates.HourLocator())
            myFmt = mdates.DateFormatter('%H:%M')
            plt.gca().xaxis.set_major_formatter(myFmt)
        # plt.tight_layout()[
    plt.show()



#def gen_plots(file,num, params, phase, CSV_FLAG, columns):
    # update_data(data, Ts)
    #Ts = 1
    #for x in params:
        # plt.figure()
        #if CSV_FLAG == 1:
            #plot_param_2(CSV_FLAG, columns, Ts,num)
        #else:
            #plot_param(file, x, phase, CSV_FLAG, Ts)


def calc_energy_diffs(data):
    E = data[1:, [-3, -2, -1]]
    E = E.astype(float)
    E = np.transpose(E)
    deltas = np.diff(E)
    E[:, 1:E.shape[1]] = deltas
    E[:, 0] = 0
    return (E)




def update_data(data, Ts):  # adds the Energy diff between the sampels & dilutes the sampales
    if (Ts != 1):
        data = dilute_sampales(data, Ts)
    data = np.array(data)
    # calc_energy_deltas
    dE = np.transpose(calc_energy_diffs(data))
    dE_title = np.array(['dE1', 'dE2', 'dE3'])
    dE_tot = np.vstack((dE_title, dE))
    new_data = np.hstack((data, dE_tot))
    with open('data.csv', 'w') as f:
        write = csv.writer(f)
        write.writerows(new_data)




def dilute_sampales(data, new_gap):
    Ts_orig = 1  # the original gap between samples [sec]
    k = int(new_gap / Ts_orig)
    n = int((len(data) - 1) / k)
    new_data = [data[k * i] for i in range(1, n + 1)]
    new_data.insert(0, data[0])
    return new_data




def diff_day():
    def days():
        def holiday_checker(holiday_in):
            valid=0
            for page in content :
                page['Contents'].sort(key=lambda x:x['LastModified'],reverse=True)
                for obj in page['Contents']:
                    if ( obj['Key'][0:5] =="rabin" or obj['Key'][0:6] =="AvneH_" or obj['Key'][0:5] =="zokim" or obj['Key'][0:5] =="mosva")and(obj['Key'][6:14] ==obj['Key'][19:27]) :
                        cp_list.append(obj['Key'])
                        valid = valid + 1
            counter =0
            i=0
            j=0
            while j < len(cp_list):
                date=cp_list[j]
                year = date[6:10]
                month= date[10:12]
                day = date[12:14]
                new_format=  str(month + '-' + day + '-' +year)
                new_format_t = pd.Timestamp(new_format)
                if i< num:
                    mon=selcpy[i].get()
                    if mon== "רבין" :
                        mon="rabin"
                    if mon =="אבני חושן":
                        mon="AvneH"
                    if mon == "צוקים":
                        mon="zokim"
                    if mon == "תיכון המושבה":
                        mon="mosva"
                    day_in = str(week_d1[i].get())
                    j+=1
                    if holiday_in[i] == "holiday":
                        if (new_format_t.day_name() == day_in) and ((new_format_t in holidays.Israel()) or (new_format_t.day_name()=="Friday") or (new_format_t.day_name()=="Saturday")) and (counter < num) and (date[0:5] == mon):
                            s_days.append(date)
                            counter =counter+1
                            i += 1
                            j=0
                    else:
                        if (new_format_t.day_name() == day_in) and (new_format_t not in holidays.Israel()) and (counter < num) and (date[0:5]==mon):
                            s_days.append(date)
                            counter=counter+1
                            i+=1
                            j=0
                else :
                    break

            for target in s_days:
                to_download=target
                to_download_path = str(DATA_FILES_DIR + '\\' + to_download)
                try:
                    s3.download_file("satec-flamiingo", to_download, to_download_path)
                except botocore.exceptions.ClientError as e:
                    if e.response['Error']['Code'] == "404":
                        label = Label(root, text="The requested file does not exist.")
                        label.pack()
                        #exit(1)
            join = os.path.join(DATA_FILES_DIR, "*.csv")
            columns = list(['timestamp'])
            columns = graphs_to_be_plotted(columns)
            button = Button(root, text="Give Me Graphs!", command=lambda: main(num,columns),font=('Helvetica', 12))
            button.pack(padx=5,pady=5)
            return num


        num=int(num_val.get())
        H_day = []
        week_d1 = [0]*num
        selcpy=[0]*num
        for i in range(num):
            week_d1[i] = StringVar(root)
            week_d1[i].set("Choose day ")
            week_menu1 = OptionMenu(root, week_d1[i], "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday","Saturday")
            week_menu1.pack()
            hol = tk.Checkbutton(root, text="Holiday", command=lambda: H_day.append("holiday"))
            wor = tk.Checkbutton(root, text="Workday", command=lambda: H_day.append("workday"))
            hol.pack()
            wor.pack()
            selcpy[i] = StringVar(root)
            selcpy[i].set("Choose a Monitor")
            menu = OptionMenu(root, selcpy[i], "רבין", "אבני חושן","צוקים","תיכון המושבה")
            menu.pack()
        button1 = Button(root, text="Next", command=lambda:holiday_checker(H_day))
        button1.pack()
    label.destroy()
    same_weekday_button.destroy()
    diff_Weekday_button.destroy()
    Dates_button.destroy()
    s3 = boto3.client('s3')
    s_days = []
    cp_list = []
    paginator = s3.get_paginator('list_objects_v2')
    content = paginator.paginate(Bucket='satec-flamiingo')
    label1 = Label(root, text="Please enter number of days :", font=('Helvetica', 12))
    label1.pack(padx=10,pady=10)
    num_val = Entry(root, width=35)
    num_val.pack(padx=5, pady=5)
    button1 = Button(root, text="Next", command=days,font=('Helvetica', 12))
    button1.pack()




def same_day():
    def newfunc():
        def sec_func():
            def checker():
                x=0
                for page in content:
                    page['Contents'].sort(key=lambda x: x['LastModified'], reverse=True)
                    valid_names =0
                    objs = page['Contents']
                    for obj in page['Contents']:
                        if (obj['Key'][0:5] == "zokim" or obj['Key'][0:5] =="mosva" or obj['Key'][0:6] =="AvneH_" or obj['Key'][0:5] =="rabin")and(obj['Key'][6:14] ==obj['Key'][19:27]):
                            s_days.append(obj['Key'])
                    num=int(num_val.get())
                    w_day=str(week_d.get())
                selected = sel.get()
                if selected == "רבין":
                    selected = "rabin"
                if selected == "אבני חושן":
                    selected = "AvneH"
                if selected == "צוקים":
                    selected = "zokim"
                if selected == "תיכון המושבה":
                    selected = "mosva"
                for val in s_days:
                    prep_date = str(val[10:12] + '-' + val[12:14] + '-' + val[6:10])
                    prep_date_format = pd.Timestamp(prep_date)
                    if (prep_date_format.day_name() == w_day) and (x < num) and (val[0:5]==selected):
                        cp_list.append(val)
                        x = x + 1
                        val = 0
                if len(cp_list) == 0:
                    label=Label(root,text="No occurences were found, exiting...")
                    label.pack()
                    exit(1)
                elif len(cp_list) < num:
                    label=Label(root,text="Not enough occurences were found, plotting" +str(x) + "occurences\n")
                for obj in cp_list:
                    to_download = obj
                    to_download_path = str(DATA_FILES_DIR + '\\' + to_download)
                    try:
                        s3.download_file("satec-flamiingo", to_download, to_download_path)
                    except botocore.exceptions.ClientError as e:
                        if e.response['Error']['Code'] == "404":
                            label = Label(root, text="The requested file does not exist.")
                            label.pack()
                            exit(1)
                join = os.path.join(DATA_FILES_DIR, "*.csv")
                columns = list(['timestamp'])
                columns = graphs_to_be_plotted(columns)
                button = Button(root, text="Give Me Graphs!", command=lambda: main(num,columns))
                button.pack(padx=5,pady=5)
                return num

            label = Label(root, text="Please enter number of occurences :",font=('century',12))
            label.pack()
            num_val = Entry(root, width=35)
            num_val.pack(padx=5, pady=5)
            button1 = Button(root, text="Next", command=checker)
            button1.pack()

        week_d = StringVar(root)
        week_d.set("Choose a day")
        week_menu=OptionMenu(root,week_d,"Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday")
        week_menu.pack()
        button1 = Button(root, text="Next ", command=sec_func)
        button1.pack()

    label.destroy()
    same_weekday_button.destroy()
    diff_Weekday_button.destroy()
    Dates_button.destroy()
    s3 = boto3.client('s3')
    s_days = []
    cp_list=[]
    x=0
    valid_names = 0
    paginator =s3.get_paginator('list_objects_v2')
    content =paginator.paginate(Bucket='satec-flamiingo')

    sel = StringVar(root)
    sel.set("Choose a Monitor")
    menu = OptionMenu(root, sel, "רבין", "אבני חושן", "צוקים", "תיכון המושבה")
    menu.pack(padx=10,pady=10)
    newfunc()




class Table:
    def __init__(self, slave,data,rows,cols):

        # code for creating table
        for i in range(rows):
            for j in range(cols):
                self.e = Entry(slave, width=16, fg='black',font=('century', 12, 'bold'))
                self.e.grid(row=i, column=j)
                self.e.insert(END, data[i][j])




def get_reports(slave,rep):
    button_frame = tk.LabelFrame(slave)
    button_frame.pack(padx=6,pady=5)
    rows,cols=(len(rep)+1,5)
    data=[[0 for i in range(cols)] for j in range(rows)]
    for z in range(len(rep)):
        data[z+1][0]=rep[z].name
        data[z+1][1]=rep[z].student_num
        data[z+1][2]=rep[z].sq_meters
        data[z+1][3]=rep[z].relig_background
        data[z+1][4]=rep[z].region
    data[0][0]= "Monitor name"
    data[0][1]="number of students"
    data[0][2]="square meters"
    data[0][3]="religious background"
    data[0][4]="region"
    t=Table(button_frame,data,rows,cols)




def graphs_to_be_plotted(columns):
    mb = Menubutton(root, text="Choose parameters to plot", relief=RAISED)
    mb.pack()
    mb.menu = Menu(mb, tearoff=0)
    mb["menu"] = mb.menu
    p1 = StringVar(root)
    p2 = StringVar(root)
    p3 = StringVar(root)
    a1 = StringVar(root)
    a2 = StringVar(root)
    a3 = StringVar(root)
    v1 = StringVar(root)
    v2 = StringVar(root)
    v3 = StringVar(root)
    pf1 = StringVar(root)
    pf2 = StringVar(root)
    pf3 = StringVar(root)
    mb.menu.add_checkbutton(label="P1", variable=p1, command=lambda: columns.append("P1"))
    mb.menu.add_checkbutton(label="P2", variable=p2, command=lambda: columns.append("P2"))
    mb.menu.add_checkbutton(label="P3", variable=p3, command=lambda: columns.append("P3"))
    mb.menu.add_checkbutton(label="I1", variable=a1, command=lambda: columns.append("I1"))
    mb.menu.add_checkbutton(label="I2", variable=a2, command=lambda: columns.append("I2"))
    mb.menu.add_checkbutton(label="I3", variable=a3, command=lambda: columns.append("I3"))
    mb.menu.add_checkbutton(label="V1", variable=v1, command=lambda: columns.append("V1"))
    mb.menu.add_checkbutton(label="V2", variable=v2, command=lambda: columns.append("V2"))
    mb.menu.add_checkbutton(label="V3", variable=v3, command=lambda: columns.append("V3"))
    mb.menu.add_checkbutton(label="PF1", variable=pf1, command=lambda: columns.append("PF1"))
    mb.menu.add_checkbutton(label="PF2", variable=pf2, command=lambda: columns.append("PF2"))
    mb.menu.add_checkbutton(label="PF3", variable=pf3, command=lambda: columns.append("PF3"))
    return columns


#def pick_date():
#    tkobj = Tk()
#    tkobj.geometry("400x400")
#    tkobj.title("Calendar picker")
#    tkc = Calendar(tkobj,selectmode = "day",year=2022,month=1,date=1)
#    tkc.pack(pady=40)
#    def fetch_date():
#        chosen_date = tkc.get_date()
#    but = Button(tkobj, text="Select Date", command=fetch_date, bg="black", fg='white')
#    # displaying button on the main display
#    but.pack()
#    # Label for showing date on main display
#    date = Label(tkobj, text="", bg='black', fg='white')
#    date.pack(pady=20)
#    return chosen_date

def main(num,columns):
    dont_change = DATA_FILES_DIR  # on your computer open an empty folder called downloads and put here the path
    DATA_FILES_DIR2 = r"C:\Users\Public\Project\merged"
    # if (input("do you want to compare days?: yes/no:")=="yes"):
    # DATA_FILES_DIR = dont_change
    # else:
    # merge_csv_files(DATA_FILES_DIR, DATA_FILES_DIR2)
    # DATA_FILES_DIR = DATA_FILES_DIR2
    files = os.listdir(DATA_FILES_DIR)
    if len(files) == 0:
        quit(0)
    file = files[0]
    rep=[]
    if not file.endswith("csv"):
        for file in files:
            get_data(DATA_FILES_DIR, file)
        columns = list(['timestamp', 'P1', 'P2', 'P3'])
    else:
        for file in files :
            if file[0:5] == "zokim":
                rep.append(school("צוקים",500,2500,"ממלכתי דתי","center"))
            if file[0:5] == "AvneH":
                rep.append(school("חושן אבני",300,1500,"ממלכתי דתי","center"))
            if file[0:5] == "rabin":
                rep.append(school("רבין",200,1200,"ממלכתי דתי","center"))
            if file[0:5] == "mosva":
                rep.append(school("המושבה תיכון",1500,4000,"ממלכתי דתי","Haifa"))
    # gen_plots(file,num, ['mock_param'], -1, CSV_FLAG=1, columns=columns)  # built for csv from dekel
        Ts = 1
        CSV_FLAG = 1
        flag=0
        for x in ['mock_param']:
            slave = tk.Tk()
            if flag==0:
                get_reports(slave,rep)
                flag=1
            columns.append("Total kW")
            plot_param_2(slave,CSV_FLAG, columns, Ts, num,rep)
        os.chdir(dont_change)
        all_files = os.listdir()
        for f in all_files:
            os.remove(f)





def Dates():
    def Dates_after_inputs():
        def myscanner():
            def start_drawing():
                for obj in filenames:
                    to_download = obj
                    to_download_path = str(DATA_FILES_DIR + '\\' + to_download)
                    try:
                        s3.download_file("satec-flamiingo", to_download, to_download_path)
                    except botocore.exceptions.ClientError as e:
                        if e.response['Error']['Code'] == "404":
                            label = Label(root,text="The requested file does not exist.")
                            label.pack()
                            print("The requested file does not exist.")
                            exit(1)
                join = os.path.join(DATA_FILES_DIR, "*.csv")
                main(num1,columns)
                return num1
            filenames = []
            s3 = boto3.client('s3')
            file_name = 'name1_yeardate0000_yeardate2359.csv'
            button1.destroy()
            for j in range(len(c)):
                scanner = str(c[j].get())
                selected =str(sel[j].get())
                to_timestamp = pd.Timestamp(scanner)
                to_format = datetime.datetime.strptime(scanner, '%m-%d-%Y').strftime('%Y%m%d')
                if to_timestamp in holidays.Israel() or to_timestamp.day_name() == "Friday" or to_timestamp.day_name() == "Saturday":
                    label = Label(root, text = scanner + " is a "+ to_timestamp.day_name() + ", this day is a holiday")
                    label.pack()
                else:
                    label = Label(root, text = scanner + " is a " + to_timestamp.day_name() + ", this day is a workday")
                    label.pack()
                file_name = file_name.replace(file_name[6:14], to_format)
                file_name = file_name.replace(file_name[19:27], to_format)
                if selected =="רבין":
                    selected="rabin"
                if selected =="אבני חושן" :
                    selected="AvneH"
                if selected == "צוקים" :
                    selected ="zokim"
                if selected == "תיכון המושבה":
                    selected = "mosva"
                file_name = file_name.replace(file_name[0:5], selected)
                filenames.append(file_name)
            start_drawing()
        label = Label(root,text="Enter dates in order: %MM-%DD-%YYYY format",font=('Helvetica',11))
        label.pack()
        num1 = int(a.get())
        if num1 == 0:
            quit(0)
        button.destroy()
        c = [0]*num1
        sel=[0]*num1
        for i in range(num1):
            label = Label(root,text="Date of day "+str(i+1)+": ")
            label.pack()
            c[i] = Entry(root, width=35)
            c[i].pack(padx=5, pady=5)
            sel[i] = StringVar(root)
            sel[i].set("Choose a Monitor")
            menu= OptionMenu(root, sel[i], "רבין", "אבני חושן", "צוקים", "תיכון המושבה")
            menu.pack()
        columns = list(['timestamp'])
        columns = graphs_to_be_plotted(columns)
        button1 = Button(root, text="Give me graphs", command=myscanner)
        button1.pack()

    same_weekday_button.destroy()
    diff_Weekday_button.destroy()
    Dates_button.destroy()
    label.destroy()
    Label(root, text='Please enter number of days:',font=('Helvetica',13)).pack(padx = 10, pady = 10)
    a = Entry(root, width=35)
    a.pack(padx = 5, pady = 5)
    button = Button(root,text="Next",command =Dates_after_inputs)
    button.pack()


##########################  code starts here ####################################################################
root.geometry("520x650")
root.title("Project Gui")
img = PhotoImage(file=r"C:\Users\Public\Project\background.png")
bg_label=Label(root,image=img)
bg_label.place(x=0, y=0, relwidth=1, relheight=1)
label = tk.Label(root,text = "Choose an option:", font=('Helvetica', 20,"bold"),bg="black",fg="white")
label.pack(padx = 5, pady = 5)
Dates_button = tk.Button(root, text="Dates", font=('Helvetica',14,"bold"),bg="dark blue",fg="white", command=Dates)
Dates_button.pack(padx = 15, pady = (0,500),side=tk.LEFT)
diff_Weekday_button = tk.Button(root, text="Different week days",bg="dark blue",fg="white", font=('Helvetica',14,"bold"),command=diff_day)
diff_Weekday_button.pack(padx = 15, pady = (0,500),side=tk.LEFT)
same_weekday_button = tk.Button(root, text="Same week day",bg="dark blue",fg="white", font=('Helvetica',14,"bold"), command=same_day)
same_weekday_button.pack(padx = 15, pady = (0,500),side=tk.LEFT)
root.mainloop()