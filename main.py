# -*- coding: utf-8 -*-
"""
@file
@brief 定时调节AIS频点小工具

@details 由用户自主配置TCP\串口模式，定时xx分钟调节AIS频点

@author Iamruzi
@date 2024-05-30
@version 1.0

"""

# 导入库
import logging
import serial
import time
import configparser
import os
import signal
import threading
import socket
import sys

# 日志配置
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

#-------------------一些工具函数定义------------------------------#
def app_exit():
    """
    @brief 应用退出

    """
    input("脚本已关闭，请按下任意键退出...")
    sys.exit(1)

def signal_handler(sig, frame):
    """
    @brief 信号处理函数，用于触发手动关闭信号

    @param arg1 sig 信号
    @param arg2 frame 帧
    """
    print('您按下了 Ctrl+C!')
    try:
        serial_receive_thread.stop()
        serial_comm.close_connection()
        tcp_receive_thread.stop()
        tcp_client.close()
        pass
    except Exception as e:
        logging.error(f"退出脚本时发生错误: {e}")
    print('您已退出脚本...')
    app_exit()

def generate_default_config():
    """
    @brief 生成默认配置文件

    """
    config = configparser.ConfigParser()
    config['Serial'] = {
        'switch': '0',
        'port': 'COM1',
        'baudrate': '38400'
    }
    config['TCP'] = {
        'switch': '1',
        'ip': '192.168.1.8',
        'port': '5556'
    }
    config['Timing'] = {
        'interval_minutes': '1'
    }
    with open('config.ini', 'w') as configfile:
        config.write(configfile)



def sleep_countdown(seconds):
    """
    @brief 延时倒计时

    """
    for i in range(seconds, 0, -1):
        print('\x1b[2K', end='')  # 清除当前行
        print(i, end='\r')  # 在同一行上输出数字
        time.sleep(1)
    print('\x1b[2K', end='')  # 清除最后一行



#-------------------类定义------------------------------#
class CustomizeTimer:
    """
    @brief 自定义定时器类

    """
    def __init__(self, target_interval):
        self.start_time = 0
        self.target_interval = target_interval

    def start(self):
        self.start_time = time.perf_counter()

    def is_elapsed(self):
        elapsed_time = time.perf_counter() - self.start_time
        if elapsed_time >= self.target_interval:
            self.start_time += self.target_interval
            return True
        else:
            return False
        
class SerialCommunication:
    """
    @brief 串口通信类

    """
    def __init__(self, port, baudrate):
        self.port = port
        self.baudrate = baudrate
        self.ser = None

    def open_connection(self):
        try:
            self.ser = serial.Serial(self.port, self.baudrate)
            logging.info(f'已打开串口{self.port}')
        except serial.SerialException as e:
            logging.error(f"打开串口 {self.port} 失败: {e}")
            raise

    def send_command(self, command):
        try:
            command = command + '\r\n'
            self.ser.write(command.encode())
        except serial.SerialException as e:
            logging.error(f"发送命令 '{command}' 失败: {e}")
            raise

    def receive_data(self):
        try:
            data = self.ser.readline().decode('ascii', errors='replace')
            return data.strip()
        except serial.SerialException as e:
            logging.error(f"读取串口数据失败: {e}")
            raise

    def close_connection(self):
        try:
            logging.info('关闭串口连接')
            self.ser.close()
        except serial.SerialException as e:
            logging.error(f"关闭串口连接失败: {e}")
            raise


class TCPClient:
    """
    @brief TCP网口通信类

    """
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.client_socket = None

    def connect(self):
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_address = (self.host, self.port)
            logging.info(f'TCP连接到服务端 {server_address}')
            self.client_socket.connect(server_address)
        except socket.error as e:
            logging.error(f'无法连接到服务端， 发生错误：{e}')
            raise

    def send(self, message):
        try:
            # logging.info(f'发送: {message}')
            message = message  + '\r\n'
            self.client_socket.sendall(message.encode())
        except socket.error as e:
            logging.error(f'发送消息时发生错误: {e}')
            raise

    def receive(self):
        try:
            data = self.client_socket.recv(1024)
            # logging.info(f'收到: {data.decode()}')
            return data.decode('ascii', errors='replace')
        except socket.error as e:
            logging.error(f'接收消息时发生错误: {e}')
            raise

    def close(self):
        try:
            logging.info('关闭TCP连接')
            self.client_socket.close()
        except socket.error as e:
            logging.error(f'关闭TCP连接时发生错误: {e}')
            raise


class SerialReceiveThread(threading.Thread):
    """
    @brief 串口接收线程类

    """
    def __init__(self, serial_comm):
        super(SerialReceiveThread, self).__init__()
        self.serial_comm = serial_comm
        self.running = threading.Event()

    def run(self):
        response_set_ok = "$SYDBG,RKOK"
        self.running.set()
        while self.running.is_set():
            try:
                data = self.serial_comm.receive_data()
                if data:
                    check_data = data[:11]
                    if check_data == response_set_ok:
                        logging.info("AIS频率设置OK!")
            except Exception as e:
                logging.error(f"接收线程发生错误: {e}")

    def stop(self):
        self.running.clear()

class TcpReceiveThread(threading.Thread):
    """
    @brief TCP网口接收线程类

    """
    def __init__(self, tcp_client):
        super(TcpReceiveThread, self).__init__()
        self.tcp_client = tcp_client
        self.running = threading.Event()

    def run(self):
        self.running.set()
        while self.running.is_set():
            try:
                data = self.tcp_client.receive()
                # logging.info(data)
                if data:
                    self.process_received_data(data)
            except Exception as e:
                logging.error(f"接收线程发生错误: {e}")

    def process_received_data(self, data):
        response_set_ok = "$SYDBG,RKOK,msg22"
        if data.startswith("$SYDBG"):
            msg_type = data[12:17]
            # logging.info(f"msg_type:{msg_type}")
            if msg_type == "msg22": 
                # logging.info(f"收到反馈：{data}")
                logging.info(f"[TCP接收] 收到反馈,本次AIS {msg_type} 频率设置OK!")
            
    def stop(self):
        self.running.clear()



#-------------------主函数------------------------------#
if __name__ == '__main__':
    
    print("***********************************************************************************")
    print(f"******                    AIS 定时调频小工具 v0.0.2 by Iamruzi               ******")
    print(f"****** v0.0.2 update 完善异常捕获；在config中新增加 串口 网口 模式开关选择   ******")
    print("***********************************************************************************")

    command1 = "$SYDBG,CMD,50,0*18"
    command2 = "!AIVDM,1,1,,B,F03t>:B1r2<2<`0wB4Fr1qp20000,0*76"
    
    signal.signal(signal.SIGINT, signal_handler)

    config = configparser.ConfigParser()
    config_path = 'config.ini'
    config.read(config_path)
    logging.warning(f"读取本地配置文件{config_path}")
    # 检查本地是否有config文件，没有则生成默认
    if not config.sections():
        generate_default_config()
        logging.warning("未检测到配置文件'config.ini',为您生成默认的配置文件...")
        sleep_countdown(3)
        
    try:
        config_path = 'config.ini'
        config.read(config_path)
        logging.warning(f"已检测到配置文件{config_path}")
        serial_port = config.get('Serial', 'port')
        serial_baudrate = config.getint('Serial', 'baudrate')
        serial_stwitch = config.getint('Serial', 'switch')

        tcp_ip  = config.get('TCP', 'ip')
        tcp_port = config.getint('TCP', 'port')
        tcp_stwitch = config.getint('TCP', 'switch')

        interval_minutes = config.getint('Timing', 'interval_minutes')
        logging.warning(f"读取配置文件{config_path} OK")

    except (configparser.Error, KeyError) as e:
        logging.error(f"读取配置文件失败: {e}")
        app_exit()


    if serial_stwitch == 1 and  tcp_stwitch == 1:
        logging.info("您选择了打开串口与网口模式")
        logging.info(f"当前需打开串口{serial_port} 波特率为：{serial_baudrate}，发送间隔为{interval_minutes}分钟.参数修改请打开config.ini（！不能删！）")
        logging.info(f"当前需连接TCP服务端 {tcp_ip}:{tcp_port}，发送间隔为{interval_minutes}分钟.参数修改请打开config.ini（！不能删！）")
        try:
            serial_comm = SerialCommunication(serial_port, serial_baudrate)
            serial_comm.open_connection()
        except Exception as e:
            logging.error(f"初始化串口通信失败: {e}")
            app_exit()

        try:
            tcp_client = TCPClient(tcp_ip, tcp_port)
            tcp_client.connect()
        except Exception as e:
            logging.error(f"初始化TCP通信失败: {e}")
            app_exit()

        serial_receive_thread = SerialReceiveThread(serial_comm)
        tcp_receive_thread = TcpReceiveThread(tcp_client)
        serial_receive_thread.start()
        tcp_receive_thread.start()
        timer = CustomizeTimer(interval_minutes * 60)

        while True:
            try:
                if timer.is_elapsed():
                    serial_comm.send_command(command1)
                    logging.info(f"[SEND] {command1}")
                    time.sleep(0.1)
                    serial_comm.send_command(command2)
                    logging.info(f"[SEND] {command2}")
                    tcp_client.send(command1)
                    logging.info(f"[TCP发送] {command1}")
                    time.sleep(0.1)
                    tcp_client.send(command2)
                    logging.info(f"[TCP发送] {command2}")
                    timer.start()
            except Exception as e:
                logging.error(f"主循环发生错误: {e}")
                break


        serial_comm.close_connection()
        tcp_client.close()

    elif serial_stwitch == 1 and  tcp_stwitch == 0:
        logging.info("您选择了打开串口模式")
        logging.info(f"当前需打开串口{serial_port} 波特率为：{serial_baudrate}，发送间隔为{interval_minutes}分钟.参数修改请打开config.ini（！不能删！）")
        try:
            serial_comm = SerialCommunication(serial_port, serial_baudrate)
            serial_comm.open_connection()
        except Exception as e:
            logging.error(f"初始化串口通信失败: {e}")
            app_exit()


        serial_receive_thread = SerialReceiveThread(serial_comm)
        serial_receive_thread.start()
        timer = CustomizeTimer(interval_minutes * 60)

        while True:
            try:
                if timer.is_elapsed():
                    serial_comm.send_command(command1)
                    logging.info(f"[SEND] {command1}")
                    time.sleep(0.1)
                    serial_comm.send_command(command2)
                    logging.info(f"[SEND] {command2}")
                    timer.start()
            except Exception as e:
                logging.error(f"主循环发生错误: {e}")
                break


        serial_comm.close_connection()

    elif serial_stwitch == 0 and  tcp_stwitch == 1:
        logging.info("您选择了打开网口模式")
        logging.info(f"当前需连接TCP服务端 {tcp_ip}:{tcp_port}，发送间隔为{interval_minutes}分钟.参数修改请打开config.ini（！不能删！）")
        try:
            tcp_client = TCPClient(tcp_ip, tcp_port)
            tcp_client.connect()
        except Exception as e:
            logging.error(f"初始化TCP通信失败: {e}")
            app_exit()

        tcp_receive_thread = TcpReceiveThread(tcp_client)
        tcp_receive_thread.start()
        timer = CustomizeTimer(interval_minutes * 60)

        while True:
            try:
                if timer.is_elapsed():
                    tcp_client.send(command1)
                    logging.info(f"[TCP发送] {command1}")
                    time.sleep(0.1)
                    tcp_client.send(command2)
                    logging.info(f"[TCP发送] {command2}")
                    timer.start()
            except Exception as e:
                logging.error(f"主循环发生错误: {e}")
                break

        tcp_client.close()
    
    else:
        logging.warning("您未选择模式开关请检查config中'switch'参数! 5秒后关闭脚本")
        sleep_countdown(5)
        app_exit()

