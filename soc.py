#DEV BY VITOR NUNCIATELLI
#ELETROMIDIA - ENGENHARIA DE PROJETOS
#V. 1.1.3 18/12/2023
import socket
from random import randbytes
import hashlib
import requests
import uuid
from datetime import datetime
import time
import struct
from _socket import SOL_SOCKET, SO_LINGER
#import sys

##########################################################################################################################################
#python3 -m venv env
#source env/bin/activate

TCP_IP = socket.gethostbyname(socket.gethostname())
TCP_PORT = 55502
BUFFER_SIZE = 1024
data_e_hora_atuais = datetime.now()
DATAHORA = data_e_hora_atuais.strftime('%Y/%m/%d %H:%M')
csrf = (hashlib.md5(randbytes(32))).hexdigest()
mac_address = uuid.getnode()
mac_address_hex = ''.join(['{:02x}'.format((mac_address >> elements) & 0xff) for elements in range(0,8*6,8)][::-1])
publicIP = requests.get('http://ipinfo.io/json').json()['ip']
#localIP = [(s.connect(('8.8.8.8', 53)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]
source_status = 'err'
mac_rmc = 0    

def log_de_erro(e):
        p = {   'csrf': csrf,
                'nucMac': str(mac_address_hex),
                'publicIP': publicIP,
                'localIP': TCP_IP,
                'rmcIP': 0,
                'data': e,
                'timestamp': DATAHORA,
                'source_status': source_status,
                'rmcMac': 0,
            }            
            
        print(p)
        r = requests.get('http://boe-php.eletromidia.com.br/server.php', params =p)
        print('http://boe-php.eletromidia.com.br/server.php')
        print(r.headers)
        print(r.status_code)

def daq(source_status, conn):
        print('[SOC]','executando DAQ ...')  
        try:
            data = conn.recv(BUFFER_SIZE)
            if not data: 
                print('NO DATA !!!')
                data = 'err'
                
            if len(data) == 0:
                mac_rmc = (data[6:12].hex())
                print('MACrmc:', mac_rmc)   

            if len(data) >=64:
                data = data.hex()
                print('daq_len:', len(data))
                print(data)

                p = {   'csrf': csrf,
                        'nucMac': str(mac_address_hex),
                        'publicIP': publicIP,
                        'localIP': TCP_IP,
                        'rmcIP': 0,
                        'data': data,
                        'timestamp': DATAHORA,
                        'hdmi_status': source_status,
                        'rmcMac': 0,
                    }            
            
                print(p)
                r = requests.get('http://boe-php.eletromidia.com.br/server.php', params =p)
                print('http://boe-php.eletromidia.com.br/server.php')
                print(r.headers)
                print(r.status_code)
                time.sleep(10)  

            else:
                print('[SOC]','raw data fora de comprimento')                     
            
        except (socket.error, Exception) as e:
            print(f"ErroDAQ: {e}")
            print("Tentando reconectar...")
            log_de_erro(e)
            time.sleep(5)  # Intervalo de espera antes da reconexão
            command()

def command(conn):   #ENVIA COMANDO                
        try:
            while conn:
                print('[SOC]','COMMAND ...')  
                source_status = bytes.fromhex('ff 55 04 57 01 01 00 b1') #command HDMI
                conn.send(source_status)
                #print('source_status:', source_status)   
                source_status_ack = conn.recv(BUFFER_SIZE) #RECEBE ACK - 0xFF 0x55 0x04 0x57 0x01 0x01 value checksum 
                if len(source_status_ack) == 8:
                    if (source_status_ack) == bytes.fromhex('ff 55 04 57 01 01 01 b2') :
                        print('TELA LIGADA')
                        #print('source_status leng:', len(source_status_ack),'source_status data:',(source_status_ack))
                        source_status = 'hdmi_on'
                        
                    if (source_status_ack) == bytes.fromhex('ff 55 04 57 01 01 00 b1') :
                        print('TELA DESLIGADA')
                        #print('source_status leng:', len(source_status_ack),'source_status data:',(source_status_ack))
                        source_status = 'hdmi_off'
                        
                    print('[SOC]','proxima funcao...')
                    #time.sleep(3)
                    daq(source_status)

            print('[SOC]','RMC TRAVADA')        
            command()
                
        except (socket.error, Exception) as e:
            print(f"ErroComando: {e}")
            print("Tentando reconectar...")
            log_de_erro(e)
            time.sleep(5)  # Intervalo de espera antes da reconexão
            conexao()

def conexao():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print('[SOC]',s)
        s.setsockopt(SOL_SOCKET, SO_LINGER, struct.pack('ii', 1, 0))
        time.sleep(5) 
        s.bind((TCP_IP, TCP_PORT))
        print('[SOC]',s.bind)
        s.listen(1)
        s.settimeout(1)
        print('[SOC]',s.listen)
        time.sleep(3)   
        #print ('4 - SOCKET ACEITO:', addr)
        conn, addr = s.accept()
        print ('[SOC]', conn)
        clientIP = '0' #s.getpeername()[0]
        print('[SOC]', clientIP)
        print('[SOC]','proxima funcao...')        

    except (socket.error, Exception) as e:
            print(f"ErroConexao: {e}")
            print("Tentando reconectar...")
            log_de_erro(e)
            time.sleep(5)  # Intervalo de espera antes da reconexão
            conexao()

    command(conn)

####################################################################

conexao()           