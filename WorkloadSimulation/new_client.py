'''
File: new_client.py
Aim: Start several clients
'''
import os

num = 3

for _ in range(num):
    os.system('start python TCP_client_interface.py')
