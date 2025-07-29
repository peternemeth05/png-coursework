import time
from functools import wraps
import zlib

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

class PNG:
    def __init__(self):
        # Initialize PNG attributes to default values
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
        # Load the PNG file and store its data, ensure the file exists
        try:
            with open(file_name, 'rb') as file:
                self.data = file.read()
                self.info = file_name
        except FileNotFoundError:
            self.info = 'file not found'

    def valid_png(self) -> bool:
        # Check if the file has a valid PNG signature
        return self.data[0:8].hex() == '89504e470d0a1a0a'

    def read_header(self):
        # Read the header of the PNG file and extract image properties
        pos = 16
        self.width = int.from_bytes(self.data[pos:pos+4], byteorder='big')
        self.height = int.from_bytes(self.data[pos+4:pos+8], byteorder='big')
        self.bit_depth = self.data[pos+8]
        self.color_type = self.data[pos+9]
        self.compress = self.data[pos+10]
        self.filter = self.data[pos+11]
        self.interlace = self.data[pos+12]

        # Ensure the PNG specifications are the ones that can be ran by this code 
        if not (self.bit_depth == 8 and self.color_type == 2 and self.compress == 0 and self.filter == 0 and self.interlace == 0):
            print("The file does not meet the required specifications for bit depth, color type, compression, filter, and interlace.")

    @debug_timer
    def read_chunks(self):
        offset = 8  # Starting from the IHDR chunk 
        idat_data = b''

        # iterate through each chunk and concatonate all the IDAT data together
        while offset < len(self.data):
            chunk_length = int.from_bytes(self.data[offset:offset+4], byteorder='big')
            chunk_type = self.data[offset+4:offset+8]
            chunk_data = self.data[offset+8:offset+8+chunk_length]
            crc = int.from_bytes(self.data[offset+8+chunk_length:offset+12+chunk_length], byteorder='big')
            
            if zlib.crc32(chunk_type + chunk_data) == crc: # Ensure the file is not corrupted
                if chunk_type == b'IDAT':
                    idat_data += chunk_data
                elif chunk_type == b'IEND': # ensure iteration stops at IEND chunk
                    break
            else:
                print(f'{chunk_type.decode("ascii")} chunk is corrupted')

            # Move to the next chunk 
            # 4 bytes of chunk length -> 4 bytes of chunk type -> chunk data -> 4 bytes of CRC
            offset += chunk_length + 12 

        self.img = [[] for _ in range(self.height)]

        # Function used in filter type 4 to determine the correct pixel 
        def paeth_predictor(a, b, c):  
            # a - left byte, b - up byte, c - upper left byte
            p = a + b - c
            pa = abs(p - a)
            pb = abs(p - b)
            pc = abs(p - c)
            if pa <= pb and pa <= pc:
                return a
            elif pb <= pc:
                return b
            else:
                return c

        if idat_data:
            decompressed_data = zlib.decompress(idat_data)
            scanline = 1 + (3 * self.width) # scanline consists of Filter Type and RGB values for each pixel

            for y in range(self.height):
                # Get only the filter type for the scanline
                filter_num = decompressed_data[scanline * y] 
                # Get the scanline without the filter type
                filtered_data = decompressed_data[1 + scanline * y:1 + scanline * y + scanline] 

                # Filter type 0 - none filter
                if filter_num == 0:
                    # the RGB pixel information is just the filtered data
                    self.img[y] = [[filtered_data[3 * x], filtered_data[3 * x + 1], filtered_data[3 * x + 2]] for x in range(self.width)]

                # Filter type 1 - sub filter [(filtered byte + left byte) % 256]
                elif filter_num == 1:
                    # Reconstruct the first pixel (since left bytes are assumed to be 0)
                    self.img[y].append([filtered_data[0], filtered_data[1], filtered_data[2]])
                    
                    # Reconstruct the remaining pixels
                    for x in range(1, self.width):
                        self.img[y].append([(filtered_data[3 * x] + self.img[y][x-1][0]) % 256,
                                            (filtered_data[3 * x + 1] + self.img[y][x-1][1]) % 256,
                                            (filtered_data[3 * x + 2] + self.img[y][x-1][2]) % 256])
                
                # Filter type 2 - up filter [(filtered byte + above byte) % 256]
                elif filter_num == 2:
                    for x in range(self.width):
                        if y == 0:
                            # Reconstruct the pixels in the first scanline (since up bytes are assumed to be 0)
                            self.img[y].append([filtered_data[3 * x], filtered_data[3 * x + 1], filtered_data[3 * x + 2]])
                        else:
                            # Reconstruct the remaining pixels
                            self.img[y].append([(filtered_data[3 * x] + self.img[y - 1][x][0]) % 256,
                                                (filtered_data[3 * x + 1] + self.img[y - 1][x][1]) % 256,
                                                (filtered_data[3 * x + 2] + self.img[y - 1][x][2]) % 256])
                
                # Filter type 3 - average [(filtered byte + ((left Byte + above Byte) // 2)) % 256]
                elif filter_num == 3:
                    for x in range(self.width):
                        above_pixel = self.img[y - 1][x] if y > 0 else [0, 0, 0] # Pixels above the 1st scanline assumed to be 0 
                        left_pixel = self.img[y][x - 1] if x > 0 else [0, 0, 0] # Pixels left the 1st column assumed to be 0 
                        self.img[y].append([(filtered_data[3 * x] + (left_pixel[0] + above_pixel[0]) // 2) % 256,
                                            (filtered_data[3 * x + 1] + (left_pixel[1] + above_pixel[1]) // 2) % 256,
                                            (filtered_data[3 * x + 2] + (left_pixel[2] + above_pixel[2]) // 2) % 256])
                
                # Filter type 4 - Paeth filter [Need to use the paeth_predictor() function to see which byte to add to the current byte]
                elif filter_num == 4:
                    # Get the previous row, if it exists, otherwise assume it is filled with zeros
                    previous_row = self.img[y - 1] if y > 0 else [[0, 0, 0] for _ in range(self.width)]
                    
                    # For the first pixel in each row, left byte and upper left byte are 0
                    first_pixel = [(filtered_data[0] + paeth_predictor(0, previous_row[0][0], 0)) % 256,
                                   (filtered_data[1] + paeth_predictor(0, previous_row[0][1], 0)) % 256,
                                   (filtered_data[2] + paeth_predictor(0, previous_row[0][2], 0)) % 256]
                    self.img[y].append(first_pixel)
                    
                    # Reconstruct the remaining pixels in the row
                    for x in range(1, len(filtered_data) // 3):
                        left_pixel = self.img[y][x - 1]  # Pixel to the left
                        above_pixel = previous_row[x]  # Pixel above
                        upper_left_pixel = previous_row[x - 1]  # Pixel to the upper left
                        
                        # Apply the Paeth predictor to each color channel (R, G, B)
                        self.img[y].append([(filtered_data[3 * x] + paeth_predictor(left_pixel[0], above_pixel[0], upper_left_pixel[0])) % 256,
                                            (filtered_data[3 * x + 1] + paeth_predictor(left_pixel[1], above_pixel[1], upper_left_pixel[1])) % 256,
                                            (filtered_data[3 * x + 2] + paeth_predictor(left_pixel[2], above_pixel[2], upper_left_pixel[2])) % 256])
                else:
                    # Make sure filter_num ranges from 0-4 
                    print(f'No valid filter method for {y}') 
    
    @debug_timer
    def save_rgb(self, file_name: str, rgb_option: int):
        # Initialize offset to start reading chunks after the PNG signature
        offset = 8
 
        # Iterate through the chunks in the PNG file
        # We need to know the IHDR and IEND information when we put the image back together
        while offset < len(self.data):
            chunk_length_bin = self.data[offset:offset+4]
            chunk_length = int.from_bytes(chunk_length_bin, byteorder='big')
            chunk_type = self.data[offset+4:offset+8]
            chunk_data = self.data[offset+8:offset+8+chunk_length]
            crc_bin = self.data[offset+8+chunk_length:offset+12+chunk_length]
            
            # Store the IHDR chunk
            if chunk_type == b'IHDR':
                ihdr_chunk = chunk_length_bin + chunk_type + chunk_data + crc_bin

            # Store the IEND chunk
            elif chunk_type == b'IEND':
                iend_chunk = chunk_length_bin + chunk_type + chunk_data + crc_bin
            
            # Move to the next chunk
            offset += chunk_length + 12

        # Create raw data bytearray to store the specific RGB channels
        raw_data = bytearray()
        for y in range(self.height):
            raw_data.append(0)  # Add filter type byte (0 for no filter)
            for x in range(self.width):
                if rgb_option == 1:
                    raw_data.extend([self.img[y][x][0], 0, 0]) # Only get the R value from img, set G & B to 0
                elif rgb_option == 2:
                    raw_data.extend([0, self.img[y][x][1], 0]) # Only get the G value from img, set R & B to 0
                elif rgb_option == 3:
                    raw_data.extend([0, 0, self.img[y][x][2]]) # Only get the B value from img, set R & G to 0

        rgb_compressed_idat_data = zlib.compress(raw_data)
    
        with open(file_name, 'wb') as file:
            # Write the PNG signature
            file.write(b'\x89PNG\r\n\x1a\n')

            # Write the IHDR chunk
            file.write(ihdr_chunk)

            # Write the IDAT chunk with the new compressed specific RGB channel data
            file.write(len(rgb_compressed_idat_data).to_bytes(4, 'big'))
            file.write(b'IDAT')
            file.write(rgb_compressed_idat_data)
            file.write(zlib.crc32(b'IDAT' + rgb_compressed_idat_data).to_bytes(4, 'big'))

            # Write the IEND chunk
            file.write(iend_chunk)

def main():
    print('PNG\n')
    image = PNG()
    image.load_file('brainbow.png')
    print(image)
    image.read_header()
    print(f'width:      {image.width}')
    print(f'height:     {image.height}')
    print(f'bit_depth:  {image.bit_depth}')
    print(f'color_type: {image.color_type}')
    print(f'compress:   {image.compress}')
    print(f'filter:     {image.filter}')
    print(f'interlace:  {image.interlace}')
    image.read_chunks()
    image.save_rgb('brainbow_r.png', 1)
    image.save_rgb('brainbow_g.png', 2)
    image.save_rgb('brainbow_b.png', 3)

    

if __name__ == '__main__':
    main()
