from time import time
import png4  as png

def main():
        t1 = time()
        print('PNG')
        print()
        image = png.PNG()
        '''
		print('data: ', image.data)
        print('info: ', image.info)
        print('width: ', image.width)
        print('height: ', image.height)
        print('bit_depth: ', image.bit_depth)
        print('color_type: ', image.color_type)
        print('compress: ', image.compress)
        print('filter: ', image.filter)
        print('interlace: ', image.interlace)
        print('img: ', image.img)
        print()'''
        
        image.load_file('filter1.png')
        #print(image.data[0:100].hex())
        #print(type(image.data))
        #print(len(image.data))
        print(image.info)
        #print(type(image.info))
        #print(len(image.info))
        #print()
        if image.valid_png():
                print('This is a PNG file')
        else:
                print('This is not a PNG file')
        print()
        image.read_header()
        print('info: ', image.info)
        '''print('width: ', image.width)
        print('height: ', image.height)
        print('bit_depth: ', image.bit_depth)
        print('color_type: ', image.color_type)
        print('compress: ', image.compress)
        print('filter: ', image.filter)
        print('interlace: ', image.interlace)
        print('img: ', image.img)
        print()'''
        image.read_chunks()
        
        # for i in range(5):
        #         for j in range(6):
        #                 print(image.img[i][j], end=' ')
        #         print()
        image.save_rgb('brainbow_r.png', 1)
        image.save_rgb('brainbow_g.png', 2)
        image.save_rgb('brainbow_b.png', 3)

        print(time()-t1)

if __name__ == '__main__':
	main()
