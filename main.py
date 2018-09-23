from PIL import Image, ImageFilter
import numpy as np
import sys


# Clase principal que contiene los atributos de los objetos que se comparan
class C_Object: 

    def __init__(self, file, min_size = 20):
        self.file = file
        self.printed = False
        self.best_match = None
        self.matched_with = None
        o_image = Image.open(file)
        self.width, self.height = o_image.size
        ar = self.width/self.height
        self.width = min_size
        self.height = int(self.width/ar)
        self.f_image = o_image.resize((self.width, self.height), Image.ANTIALIAS)
        self.rgb = self.f_image.convert('RGB')
        self.img_array = np.zeros([self.height, self.width, 3],dtype=np.uint8)
        self.filter()
        self.detect_colors()
        self.subfigure_dimensions()

    def filter(self):
        rgb = self.f_image.convert('RGB')
        for i in range(self.width):
            for j in range(self.height):
                r,g,b = rgb.getpixel((i, j))
                r = self.convert_to_CGA(r)
                g = self.convert_to_CGA(g)
                b = self.convert_to_CGA(b)
                self.img_array[j,i] = [r,g,b]
        self.f_image = Image.fromarray(self.img_array)
        
    def save(self):
        self.f_image.save(self.file+"__filtered.png")

    def detect_colors(self):
        colors = {}
        for i in range(self.width):
            for j in range(self.height):
                r,g,b = self.rgb.getpixel((i, j))
                color = str(self.convert_to_CGA(r))+str(self.convert_to_CGA(g))+str(self.convert_to_CGA(b))
                if color in colors:
                    colors[color]["quantity"] = colors[color]["quantity"]+1
                    colors[color]["coords"].append((i,j))
                else:
                    colors[color] = {}
                    colors[color]["quantity"] = 1
                    colors[color]["coords"] = []
                    colors[color]["coords"].append((i,j))
        self.colors = colors

    def subfigure_dimensions(self):
        self.delete_bg()
        self.f_image = self.f_image.crop(self.get_box())
        self.width, self.height = self.f_image.size
        self.detect_colors()

    def delete_bg(self):
        quantity = 0
        bg = ""
        for key in list(self.colors.keys()):
            current = self.colors[key]["quantity"]
            if quantity < current:
                quantity = current
                bg = key
        self.forbidden = bg
        self.colors.pop(bg)

    def get_box(self):
        min_x = None
        min_y = None
        max_x = None
        max_y = None
        for key in list(self.colors.keys()):
            for coord in self.colors[key]["coords"]:
                if min_x == None:
                    min_x = coord[0]
                elif min_x > coord[0]:
                    min_x = coord[0]

                if min_y == None:
                    min_y = coord[1]
                elif min_y > coord[1]:
                    min_y = coord[1]

                if max_x == None:
                    max_x = coord[0]
                elif max_x < coord[0]:
                    max_x = coord[0]

                if max_y == None:
                    max_y = coord[1]
                elif max_y < coord[1]:
                    max_y = coord[1]

        return ((min_x, min_y, max_x, max_y))

    def edges(self):
        self.f_image = self.f_image.filter(ImageFilter.FIND_EDGES)

    def convert_to_CGA(self, v):
        if v >= 0 and v <= 85:
            v = 85
        elif v >= 86 and v <=170:
            v = 170
        else:
            v = 0xFF
        return self.convert_to_CGA_2(v)

    def convert_to_CGA_2(self, v):
        if v >= 0 and v <= 170:
            v = 0x55
        else:
            v = 0xFF
        return v

    def best_matches(self, objects):
        matches = objects
        matches = self.c_by_size(matches)
        matches = self.c_by_color(matches)
        if len(matches) != len(objects):
            matches = self.c_by_position(matches)
            for match in matches:
                if match != None:
                    self.best_match = match
                    match.matched_with = self

    def c_by_color(self, objects):
        matches = []
        for obj in objects:
            if self != obj:
                self_color = self.color_relation()
                obj_color = obj.color_relation()
                if len(self_color) == len(obj_color):
                    candidate = True
                    for i in range(len(self_color)):
                        if abs(self_color[i] - obj_color[i]) <= 15:
                            candidate = False
                            break
                    if candidate:
                        if obj not in matches:
                            matches.append(object)
                else:
                    obj_size = len(obj_color)
                    if len(self_color) == obj_size-1:
                        candidate = True
                        for i in range(len(self_color)):
                            if abs(self_color[i] - (obj_color[i] + (obj_color[-1]/obj_size-1))) <= 15:
                                candidate = False
                                break
                        if candidate:
                            if obj not in matches:
                                matches.append(obj)
        if len(matches) != 0:
            return matches
        else:
            return objects

    def color_relation(self):
        total = 0
        totals = []
        values = []
        for key in list(self.colors.keys()):
            quantity = self.colors[key]["quantity"]
            total += quantity
            totals.append(quantity)
        percent = total/100
        for value in totals:
            values.append(value/percent)
        values.sort(reverse=True)
        return values
    
    def c_by_size(self, objects):
        matches = []
        for obj in objects:
            if self != obj:
                if self.width == obj.width and self.height == obj.height:
                    matches.append(obj)
        if len(matches) != 0:
            return matches
        else:
            return objects

    def c_by_position(self, objects):
        matches = []
        bg_c = 0
        match = None
        for obj in objects:
            if self != obj:
                self_bg = self.colors[self.forbidden]["quantity"]
                self_pos = self.colors[self.forbidden]["coords"]
                
                obj_bg = obj.colors[obj.forbidden]["quantity"]
                obj_pos = obj.colors[obj.forbidden]["coords"]
                
                c = 0
                if self_bg > obj_bg:
                    for pos in self_pos:
                        if pos in obj_pos:
                            c+=1
                else:
                    for pos in obj_pos:
                        if pos in self_pos:
                            c+=1
                if bg_c < c:
                    bg_c = c
                    match = obj
        matches.append(match)
        return matches

    def is_reciprocal(self):
        if self.best_match != None:
            if self.best_match.best_match == self:
                self.printed = True
                self.best_match.printed = True
                print("Best match for: " + self.file + " -> " + self.best_match.file + " (Perfect match)")
                return True
            else:
                print("Best match for: " + self.file + " -> " + self.best_match.file)
        else:
            print("Best match for: " + self.file + " -> (No match)")

objects = []
for arg in sys.argv[1:]:
    object = C_Object(arg, 7)
    object.save()
    objects.append(object)

for obj in objects:
    obj.best_matches(objects)

for obj in objects:
    if not obj.printed:
        obj.is_reciprocal()
