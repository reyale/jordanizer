import sys
from PIL import Image, ImageOps, ImageDraw, ImageFont
import cStringIO
import math
from optparse import OptionParser

char_brightness = [(32, 0.0), (96, 1.29), (46, 2.44), (94, 2.96), (126, 2.96), (95, 3.73), (45, 3.86), (39, 4.24), (44, 4.43), (124, 4.5), (40, 4.63), (41, 4.63), (58, 4.88), (42, 5.27), (33, 5.4), (62, 5.46), (60, 5.53), (37, 5.66), (43, 5.66), (47, 5.66), (92, 5.66), (123, 5.66), (125, 5.66), (59, 6.04), (61, 6.17), (91, 6.17), (93, 6.17), (55, 6.43), (105, 6.88), (49, 7.07), (63, 7.07), (108, 7.07), (34, 7.33), (114, 7.45), (99, 7.65), (73, 7.71), (106, 7.71), (116, 7.71), (122, 7.84), (118, 7.97), (50, 8.1), (111, 8.23), (74, 8.35), (51, 8.55), (38, 8.74), (67, 8.74), (117, 8.74), (120, 8.8), (89, 8.87), (48, 8.93), (53, 8.93), (76, 9.0), (115, 9.19), (121, 9.25), (52, 9.38), (110, 9.38), (57, 9.51), (86, 9.51), (102, 9.58), (84, 9.77), (107, 9.77), (54, 9.83), (79, 9.9), (119, 9.96), (56, 10.03), (101, 10.03), (97, 10.15), (90, 10.35), (36, 10.41), (80, 10.41), (83, 10.47), (71, 10.67), (68, 10.73), (88, 10.73), (104, 10.73), (70, 10.8), (85, 10.8), (103, 11.5), (100, 11.82), (98, 11.95), (82, 12.08), (65, 12.15), (75, 12.15), (109, 12.47), (112, 12.53), (113, 12.53), (64, 12.6), (69, 12.72), (81, 12.79), (72, 12.98), (35, 13.37), (66, 13.37), (78, 13.5), (87, 14.91), (77, 15.36)]

#this could be optimized, it does not map one set to another perfectly
#performs the worst if buckets_size becomes *.5
class remaper:
	def __init__(self, min_value, max_value):
		self.min_value = min_value
		self.max_value = max_value
		buckets_size = float(max_value - min_value) / float(len(char_brightness))
		buckets_size = math.ceil(buckets_size)
		self.buckets = { }
		bucket_count = 1
		current_bucket = 0
		for i in range(min_value, max_value + 1):
			if bucket_count == buckets_size and (current_bucket + 1 < len(char_brightness)):
				current_bucket = current_bucket + 1 	
				bucket_count = 1
			else:
				bucket_count = bucket_count + 1
			self.buckets[i] = char_brightness[current_bucket][0]
	def get(self, value):
		return chr(self.buckets[value])
	
class Accessor:
	def __init__(self, data, width, height, width_sample_size, height_sample_size):
		self.data = data
		self.width = width
		self.height = height
		self.width_sample_size = width_sample_size
		self.height_sample_size = height_sample_size
		self.result = [ ]
		for i in range(0, int(height/self.height_sample_size)):
			current_list = []
			self.result.append(current_list)
			for w in range(0, width / self.width_sample_size):
				current_list.append(self.get(w, i))
	
	def get(self, x, y):
		pixels = [ ]
		start = (x * self.width_sample_size) + (y * self.width * self.height_sample_size)
		for w in range(0, int(self.height_sample_size)):
			for i in range(start, start + self.width_sample_size):
				pixels.append(self.data[i])
			start = start + self.width
		#median
		#pixels = sorted(pixels)
		#return pixels[len(pixels)/2]
		return sum(pixels)/len(pixels) # average - seems to peform a bit better
	
	def result_matrix(self):
		return self.result

#this is just a straight up copy of the other accessor - can combine in to one pass
class ColorAccessor:
	def __init__(self, data, width, height, width_sample_size, height_sample_size):
		self.data = data
                self.width = width
                self.height = height
                self.width_sample_size = width_sample_size
                self.height_sample_size = height_sample_size
                self.result = [ ]
		for i in range(0, int(height/self.height_sample_size)):
                        current_list = []
                        self.result.append(current_list)
                        for w in range(0, width / self.width_sample_size):
                                current_list.append(self.get(w, i))
	def get(self, x, y):
		pixels = [ ]
                start = (x * self.width_sample_size) + (y * self.width * self.height_sample_size)
                for w in range(0, int(self.height_sample_size)):
                        for i in range(start, start + self.width_sample_size):
                                pixels.append(self.data[i])
                        start = start + self.width
		return (int(sum(r[0] for r in pixels)/float(len(pixels))), int(sum(g[1] for g in pixels)/float(len(pixels))), int(sum(b[1] for b in pixels)/float(len(pixels))))

	def result_matrix(self):
		return self.result
	

class Jordanize:
	def __init__(self, image_path, destination):
		self.image_path = image_path
		self.destination = destination
		#self.width = width

	def generate_matrix(self):
		image_data = open(self.image_path, 'r').read()	
		img_io = cStringIO.StringIO(image_data)
		image = Image.open(img_io)
		#(width, height) = image.size
		#new_height = self.width * float(height)/float(width)
		#image = image.resize((self.width, int(new_height)))
		image_grayscale = ImageOps.grayscale(image)
		(width, height) = image_grayscale.size

		raw_data = list(image_grayscale.getdata())
		accessor = Accessor(raw_data, width, height, 1, 2)#assuming the ratio 1:2 is bad
		color_raw_data = list(image.getdata())
		color_accessor = ColorAccessor(color_raw_data, width, height, 1, 2)#assuming the ratio 1:2 is bad

		matrix = accessor.result_matrix()
		color_matrix = color_accessor.result_matrix()
		(min_bright, max_bright) = image_grayscale.getextrema()
		remap = remaper(min_bright, max_bright)
		result = [ ]
		for row in matrix:
			current_list = []
			result.append(current_list)
			for item in row:
				current_list.append(remap.get(item))
		return (result, color_matrix)

	#the raw ascii of jordan, if that's your thing	
	def write_ascii(self):
		matrix = self.generate_matrix()
		result = ''
		for row in matrix:
			for character in row:
				result = result + character
			result = result + '\n'
		return result

	def write_image(self):
		(matrix, color_matrix) = self.generate_matrix()	
		font_size = 5 
                font = ImageFont.truetype('/usr/share/fonts/truetype/freefont/FreeMono.ttf', font_size)
		(one_char_width, one_char_height) = font.getsize('T')
                img = Image.new("RGBA", (one_char_width * len(matrix[0]), one_char_height * len(matrix)), (0,0,0))
		draw = ImageDraw.Draw(img)
		height_location = 0
		for i in range(0, len(matrix)):
			x_location = 0
			for j in range(0, len(matrix[i])):
				(width, height) =  font.getsize(matrix[i][j])
				#draw.rectangle(((x_location, height_location), (x_location + width, height_location + height)), fill=color_matrix[i][j])#this basically just makes it look like the original image
				draw.text((x_location, height_location), matrix[i][j], fill=color_matrix[i][j], font=font)
				x_location += width
			(width, height) =  font.getsize(matrix[i][0])
			height_location += height
		#img = img.resize((img.size[0]/3, img.size[1]/3)) #you lose the feel of ascii with this turned on
		img.save(self.destination)

parser = OptionParser()
parser.add_option('-s', '--source', dest='source', default=None, help='source jordan image')
parser.add_option('-d', '--destination', dest='dest', default=None, help='destination jordan image')
(options, args) = parser.parse_args()
if options.source is None or options.dest is None:
	parser.print_help()
	sys.exit(-1)

jordan = Jordanize(options.source, options.dest)
jordan.write_image()
