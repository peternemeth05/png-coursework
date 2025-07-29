
data = b'\x04\x92'
#print(data.hex())
#print(int.from_bytes(data, byteorder = 'big'))


#print(int(str(data),16))

with open('brainbow.png', 'rb') as file:
    cool = file.read(10)

   
    #print(cool[0:5].hex())


#rb means read bytes, ab means append bytes, wb means write bytes
with open('BRCA1(6).fna', 'r') as f:
        data = f.read()
        offset = data.index(':')
        
        f.seek(offset)
        #print(f.read())

import zlib

decompressed_data = b"\x9c\xab\xac\xad\x00\x00\x01\x05\x01\x02"  # Example compressed data

compressed_data = zlib.compress(decompressed_data)
print(compressed_data)
print(decompressed_data)

#print( decompressed_data[0:4].hex().decode("ascii"))
