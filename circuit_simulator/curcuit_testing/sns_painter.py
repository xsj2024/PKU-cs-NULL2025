# 读取./output.csv文件并用seaborn画图
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import os
with open('output.csv', 'r') as f:
    lines = f.readlines()
    time = []
    vout = []
    for line in lines:
        t, v = line.strip().split(',')
        time.append(float(t))
        vout.append(float(v))
    time = np.array(time)
    vout = np.array(vout)
    # 画图
    plt.figure(figsize=(10, 5))
    plt.plot(time, vout)
    plt.title('Transient Response of RLC Circuit')
    plt.xlabel('Time (s)')
    plt.ylabel('Output Voltage (V)')
    plt.grid()
    plt.show()