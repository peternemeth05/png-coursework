import time
from functools import wraps

def debug_timer(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"Function '{func.__name__}' executed in {elapsed_time:.5f} seconds")
        return result
    return wrapper

import zlib

class PNG:

    def __init__(self):

        self.data = b''
        self.info = ''

        self.width = 0
        self.height = 0
        

        
        self.bit_depth = 0
        self.color_type = 0
        self.compress = 0
        self.filter = 0
        self.interlace = 0

        self.img = []

        
    def load_file(self, file_name: str):
        try:
            with open(file_name, 'rb') as file:
                self.data = file.read()
                self.info = file_name

        except FileNotFoundError:   
            self.info = 'file not found'

    def valid_png(self) -> bool:

        if self.data[0:8].hex() == '89504e470d0a1a0a':
            return True
        else:
            return False
        
    
    def read_header(self):

        # positioned at the start of the 'chunk data' bytes
        # we know IHDR chunk data bytes start at the 17th byte 
        # (8 signature -> 4 IDHR chunck length -> 4 IDHR chunk type -> CHUNK DATA)
        pos = 16 

        self.width =  int.from_bytes(self.data[pos:pos+4], byteorder = 'big')
        self.height =  int.from_bytes(self.data[pos+4:pos+8], byteorder = 'big')
        print(self.data[0:5])
        self.bit_depth =  self.data[pos+8]
        self.color_type = self.data[pos+9]
        self.compress =  self.data[pos+10]
        self.filter =  self.data[pos+11]
        self.interlace =  self.data[pos+12]
        
        if not (self.bit_depth == 8 and self.color_type == 2 and self.compress == 0 and  self.filter == 0 and self.interlace == 0):
            print("The file does not meet the required specifications for bit depth, color type, compression, filter, and interlace.")
        


    @debug_timer
    def read_chunks(self):
        
        
        offset = 8
        idat_data = b''

        while offset < len(self.data):

            chunk_length = int.from_bytes(self.data[offset: offset + 4], byteorder= 'big')
            chunk_type = self.data[offset+4: offset+8]
            chunk_data = self.data[offset + 8: (offset+chunk_length) + 8]
            crc = int.from_bytes(self.data[ (offset+chunk_length) + 8 : (offset+chunk_length) + 12 ] ,'big')

            print(f'{chunk_type}: {chunk_length}')
            
  
            if zlib.crc32(chunk_type + chunk_data)  == crc: # ensure the file is not corrupted
                
                if chunk_type == b'IDAT':  
                    idat_data += chunk_data # add all the IDAT Data together, just incase there is more than 1 IDAT chunk
                    
            else:
                chunk = chunk_type.decode('ascii')
                print(f'{chunk} chunk is corrupted')
            

                
            offset += chunk_length + 12 #plus 12 to account for 'Chunk length' bytes, 'Chunk Type' bytes, CRC bytes
        
        
        self.img = [ [] for _ in range(self.height)]

  
        if idat_data:
            
            data = zlib.decompress(idat_data)
            #print(data[0:10])
            scanline = 1 + (3 * self.width) 
           # print(data[0:10])

            for y in range(self.height):

                # Determine the filter byte for the current scanline
                filter_num = data[scanline * y ]


                #print(f'y is {y}, with {filter_num}')
                #time.sleep(0.01)
                
                # filter type 0 - none filter
                if filter_num == 0:  
                    filtered_data = data[1 + scanline * y: 1+scanline * y + scanline]
                    # the RGB data are the raw pixel values
                    for x in range(self.width):
                        self.img[y].append([filtered_data[3 * x], 
                                            filtered_data[3 * x + 1], 
                                            filtered_data[3 * x + 2]])


                # filter type 1 - sub filter [(filtered byte + left byte) % 256]
                elif filter_num == 1:
                    
                    filtered_data = data[1+ scanline*y :  1+scanline*y + scanline] 
                    #print(filtered_data[0:9])

                    # reconstruct the first pixel (since left bytes are assumed to be 0)
                    self.img[y].append([filtered_data[0], filtered_data[1], filtered_data[2]]) 
                   # print(self.img[y][1-1][2])
                    

                    # decode the remaining pixels
                    for x in range(1,self.width): 

                        # self.img[y][x] is the same as the left pixel 
                        # reconstructing the rest of the pixels in the scanline in the form: self.img[y].append([R, G, B])
                        self.img[y].append([(filtered_data[3*x] + self.img[y][x-1][0]) % 256, 
                                            (filtered_data[3*x + 1] + self.img[y][x-1][1]) % 256, 
                                            (filtered_data[3*x + 2] + self.img[y][x-1][2]) % 256])
                        

                # filter type 2 - up filter [(filtered byte + above byte) % 256]
                elif filter_num == 2:
                    filtered_data = data[1 + scanline * y: 1+ scanline * y + scanline]
                    for x in range(self.width):
                        
                        # if first row (y==0) assume the bytes above are 0
                        if y == 0:
                            self.img[y].append([filtered_data[3 * x], filtered_data[3 * x + 1], filtered_data[3 * x + 2]])
                        else:
                            self.img[y].append([(filtered_data[3 * x] + self.img[y - 1][x][0]) % 256,
                                                (filtered_data[3 * x + 1] + self.img[y - 1][x][1]) % 256,
                                                (filtered_data[3 * x + 2] + self.img[y - 1][x][2]) % 256])
                            

                # filter type 3 - average [(filtered byte + ((left Byte + above Byte) // 2)) % 256]
                elif filter_num == 3: 
                    filtered_data = data[1 + scanline * y: 1 + scanline * y + scanline]
                    for x in range(self.width):
                        if y == 0:
                            above_pixel = [0, 0, 0]
                        else:
                            above_pixel = self.img[y - 1][x]

                        if x == 0:
                            left_pixel = [0, 0, 0]
                        else:
                            left_pixel = self.img[y][x - 1]

                        self.img[y].append([(filtered_data[3 * x] + (left_pixel[0] + above_pixel[0]) // 2) % 256,
                                            (filtered_data[3 * x + 1] + (left_pixel[1] + above_pixel[1]) // 2) % 256,
                                            (filtered_data[3 * x + 2] + (left_pixel[2] + above_pixel[2]) // 2) % 256])
                
                # filter type 4 - Paeth filter
                elif filter_num == 4:  


                    filtered_data = data[1 + scanline*y : scanline*y + scanline]

                    if y > 0:
                        previous_row = self.img[y - 1]
                    else:
                        previous_row = [ [0, 0, 0] for _ in range (len(filtered_data) // 3)]
                        
                    
                    #decode the first pixel (no left pixel and the upper-left pixel is assumed to be 0)
                    first_pixel = [
                        (filtered_data[0] + self.paeth_predictor(0, previous_row[0][0], 0)) % 256,
                        (filtered_data[1] + self.paeth_predictor(0, previous_row[0][1], 0)) % 256,
                        (filtered_data[2] + self.paeth_predictor(0, previous_row[0][2], 0)) % 256 ]
                    
                    self.img[y].append(first_pixel)

                    # decode the remaining pixels
                    for x in range(1, len(filtered_data) // 3):
                        left_pixel = self.img[y][x - 1]
                        above_pixel = previous_row[x]
                        
                        upper_left_pixel = previous_row[x - 1]

                        R = (filtered_data[3 * x] + self.paeth_predictor(left_pixel[0], above_pixel[0], upper_left_pixel[0])) % 256
                        G = (filtered_data[3 * x + 1] + self.paeth_predictor(left_pixel[1], above_pixel[1], upper_left_pixel[1])) % 256
                        B = (filtered_data[3 * x + 2] + self.paeth_predictor(left_pixel[2], above_pixel[2], upper_left_pixel[2])) % 256

                        self.img[y].append([R, G, B])
                
                else:
                    print(f'No valid filter method for {y}')
                    
                
    @staticmethod
    def paeth_predictor(a, b, c):
        """paeth predictor function.
            used to determine which other pixel to use"""
        
        # a is the byte to the left
        # b is the byte  above
        # c is the byte to the upper left

        # Calculate the initial predictor value
        p = a + b - c
        pa = abs(p - a)
        pb = abs(p - b)
        pc = abs(p - c)

        # return the neighboring pixel with the smallest difference
        if pa <= pb and pa <= pc:
            return a
        elif pb <= pc:
            return b
        else:
            return c
        
    @debug_timer
    def save_rgb(self, file_name: str, rgb_option: int):
        
        offset = 8

        chunks = [] 
        while offset < len(self.data):
            chunk_length_bin = self.data[offset: offset + 4]
            chunk_length = int.from_bytes(self.data[offset: offset + 4], byteorder='big')
            chunk_type = self.data[offset + 4: offset + 8]
            chunk_data = self.data[offset + 8: (offset + chunk_length) + 8]
            crc_bin = self.data[(offset + chunk_length) + 8: (offset + chunk_length) + 12]
                    #         0                  1               2         3          
            chunks.append([chunk_length_bin,  chunk_type,  chunk_data, crc_bin])


            offset += chunk_length + 12  # plus 12 to account for 'Chunk length' bytes, 'Chunk Type' bytes, CRC bytes


        # the information we need to find the 'filter types' in each scanline

        with open(file_name, 'wb') as file:
            file.write(b'\x89PNG\r\n\x1a\n')  # write the PNG signature

            for chunk in chunks:
                if chunk[1] == b'IDAT':
                    #the information needed
                    #decompress_idat_data, scanline = zlib.decompress(chunk[2]), (1 + (3 * self.width))

                    raw_data_str = ''
                    for y in range(self.height):
                        
          
                        raw_data_str += '00'

                        for x in range(self.width):
                            #print(self.img[y][x], end = ' ')

                            if rgb_option == 1:

                                # only adding the 'R' for the pixel setting G and B to 0
                                raw_data_str  += f"{self.img[y][x][0]:02X}0000"

                            elif rgb_option == 2:   
                            
                                # only adding the 'G' for the pixel setting R and B to 0
                                raw_data_str  += f"00{self.img[y][x][1]:02X}00"

                            elif rgb_option == 3:
                                
                                # only adding the 'B' for the pixel setting R and G to 0
                                raw_data_str  += f"0000{self.img[y][x][2]:02X}"

                    rgb_decompressed_idat_data = bytes.fromhex(raw_data_str)
                    rgb_compressed_idat_data = zlib.compress(rgb_decompressed_idat_data)

                    file.write(len(rgb_compressed_idat_data).to_bytes(4, 'big'))
                    file.write(chunk[1])
                    file.write(rgb_compressed_idat_data)
                    file.write(chunk[3])
                    #file.write(zlib.crc32(chunk[1] + chunk[2]).to_bytes(4, 'big'))

                else:

                    file.write(chunk[0])
                    file.write(chunk[1])
                    file.write(chunk[2])
                    file.write(chunk[3])

                        
def main():
    print('PNG')
    print()

    image = PNG()
    image.load_file('brainbow.png')

    image.read_header()

    print('width:      ', image.width)
    print('height:     ', image.height)
    print('bit_depth:  ', image.bit_depth)
    print('color_type: ', image.color_type)
    print('compress:   ', image.compress)
    print('filter:     ', image.filter)
    print('interlace:  ', image.interlace)

    image.read_chunks()


    image.save_rgb('brainbow_r.png', 1)
    image.save_rgb('brainbow_g.png', 2)
    image.save_rgb('brainbow_b.png', 3)






    #image.read_chunks()
    # for i in range(5):
    #     for j in range(6):
    #         print(image.img[i][j], end=' ')
    #     print()

    #print(image.img[700][1100])

    



if __name__ == '__main__':
    main()


