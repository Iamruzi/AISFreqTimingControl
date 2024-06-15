# -*- coding: utf-8 -*-
"""
@file
@brief 模拟设备测试main.py

@author Iamruzi
@date 2024-05-30
@version 1.0

"""


import serial
import time
import random

# 串口配置
ser = serial.Serial('COM2', 38400, timeout=1)

# 报文列表
gnss_msgs = [
    "$GPRMC,092725.000,A,4717.11,N,00833.91,E,0.00,89.67,130180,,,A*69",
    "$GPGSV,3,1,09,10,63,137,17,07,61,098,15,05,59,290,20,08,56,157,30*77",
    "$GPGGA,092725.000,4717.11,N,00833.91,E,1,8,1.01,499.6,M,48.0,M,,*58"
]

ais_msg = "!AIVDM,1,1,,B,F03t>:B1r2<2<`0wB4Fr1qp20000,076"

# 发送频率
frequency = 1  # 1 Hz

while True:
    # 随机发送 GNSS 报文
    gnss_msg = random.choice(gnss_msgs)
    ser.write(gnss_msg.encode() + b'\r\n')
    print(f"Sent GNSS message: {gnss_msg}")

    # 随机发送 AIS 报文
    ser.write(ais_msg.encode() + b'\r\n')
    print(f"Sent AIS message: {ais_msg}")

    # 检查是否收到指定报文
    if ser.in_waiting > 0:
        response = ser.readline().decode().strip()
        if response == "$SYDBG,CMD,50,018\r\n":
            response_msg = "$SYDBG,RKOK,mss22,09:08:35,TT=1304,$lotHum=1304,chanB00$SYDBG, Regior LongLat,[120.000 27.000 119.00026.000，txrx-0,power0,zone-400SYDBG,Region,lercator,[13358338 3104078 13247019 2980355]Distx-80,107Nm Disty=86,8058000$SYDBG,0,list len=100SYDBG,O,In Region00$syDBG,Charnel,[2078 2083],000"
            ser.write(response_msg.encode() + b'\r\n')
            print("Received $SYDBG,CMD,50,018 - Sent response")
        elif response == "!AIVDM,1,1,,B,F03t>:B1r2<2<`0wB4Fr1qp20000,076":
            response_msg = "$SYDBG,RKOK,mss22,09:08:35,TT=1304,$lotHum=1304,chanB00$SYDBG, Regior LongLat,[120.000 27.000 119.00026.000，txrx-0,power0,zone-400SYDBG,Region,lercator,[13358338 3104078 13247019 2980355]Distx-80,107Nm Disty=86,8058000$SYDBG,0,list len=100SYDBG,O,In Region00$syDBG,Charnel,[2078 2083],000"
            ser.write(response_msg.encode() + b'\r\n')
            print("Received !AIVDM,1,1,,B,F03t>:B1r2<2<`0wB4Fr1qp20000,076 - Sent response")

    # 延迟以实现 1 Hz 频率
    time.sleep(1)
