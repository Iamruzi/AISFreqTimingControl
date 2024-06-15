# AIS频点定时控制-AISFreqTimingControl

## 缘由

> 脚本编写已经尽可能把备注写清楚，此仓库用于备份,，关于打包以及环境自行研究。

本仓库是帮助学校余老师项目编写的一个小工具。

由于他项目中AIS设备24小时恢复默认频点，所以需要定时调节频点，才可以让本地接收机对上，看到设备AIS信息。


## 仓库简要说明

文件结构如下：
.

│  config.ini  // 配置文件（可以自动生成）

│  device_simulate.py // 设备模拟测试脚本，用于测试主程序

│  favicon.ico // 图标

│  main.py // 主程序py

|  AIS定时调频小工具.exe // 打包好的exe



这里说明一下**config.ini**文件，该文件脚本运行会自检，如果没有会自动创建。（要注意的是：项目本就是TCP的，串口模式我额外加的，对于之前需求一般用不着，可以忽略）


```ini
[Serial]
switch = 0 # 串口开关
port = COM1 # 串口号 
baudrate = 38400 # 串口波特率

[TCP]
switch = 1 # 网口开关
ip = 192.168.100.3 # TCP ip
port = 5556 # TCP 端口

[Timing]
interval_minutes = 1 # 定时分钟数
