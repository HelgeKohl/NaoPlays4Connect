import socket
import time
import pickle
import os
import struct
from struct import calcsize

TCP_IP = '10.3.141.140' #'192.168.0.176'
TCP_PORT = 9001
BUFFER_SIZE = 1024
ENDPOINT_SERVER = '10.3.141.140'
ENDPOINT_SERVER_PORT = 9001



# send image
filename = '133774_camImage.png'
f = open(filename, 'rb')
nBytes = os.path.getsize(filename)
recieved_f = [-10,-10]
packed_f = struct.pack('!ii',recieved_f[0],recieved_f[1])
print (calcsize('!ii'))

print ("file size:", nBytes, type(nBytes))


s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((TCP_IP, TCP_PORT))


print('CLIENT: nBytes={nBytes}')
# Send 4-byte network order frame size and image
hdr = struct.pack('<i',nBytes)
s.sendall(hdr)
#s.sendall(buffer)

l = f.read(BUFFER_SIZE)
while (l):
    s.send(l)
    #print('Sent ',repr(l))
    l = f.read(BUFFER_SIZE)
    if not l:
        #print ('error sending image file')
        f.close()  
        break

############################################################
print('receiving data...')
data = s.recv(8)
# Decode received data into UTF-8
data = struct.unpack('<ii', data)
# Convert decoded data into list
recieved_f = data
print('obtained response:', recieved_f)
s.close()

#        magic_number = 16777216
state_val = int(recieved_f[0])# / magic_number)
column_val = int(recieved_f[1])# / magic_number)
print 'state: ', state_val
print 'column: ', column_val
############################################################

#print('receiving data...')
#data = s.recv(8)
# Decode received data into UTF-8
#data = struct.unpack('!ii',data)
# Convert decoded data into list
#recieved_f = data
#print('obtained response:',recieved_f)

    
#print('Successfully get the file')


#s.close()
print('connection closed')

