import libtcodpy as libtcod
import random

#Map tiles
class GrassTile:
    def __init__(self):
        self.blocked = False
        self.variations = "\'\"`;.,"
        self.char = self.variations[random.randint(0,len(self.variations)-1)]
        self.color = libtcod.Color(0, random.randint(200, 255), 0)
        self.name = "Grass"
        self.animated = False

class DirtTile:
    def __init__(self):
        self.blocked = False
        self.variations = "\'\"`;.,"
        self.char = self.variations[random.randint(0,len(self.variations)-1)]
        self.color = libtcod.Color(150, 75, 0)
        self.name = "Dirt"
        self.animated = False

class TallGrassTile:
    def __init__(self):
        self.blocked = False
        self.variations = "wv"
        self.char = self.variations[random.randint(0,len(self.variations)-1)]
        self.color = libtcod.Color(0, random.randint(200, 255), 0)
        self.name = "Tall grass"
        self.animated = False


class StonyDirt:
    def __init__(self):
        self.blocked = False
        self.variations = "o8se"
        self.char = self.variations[random.randint(0,len(self.variations)-1)]
        self.color = libtcod.Color(150, 150, 150)
        self.name = "Stony dirt"
        self.animated = False
       
class ShallowWater:
    def __init__(self):
        self.blocked = False
        self.variations = "=-"
        self.char = self.variations[random.randint(0,len(self.variations)-1)]
        self.color = libtcod.Color(100, 100, 255)
        self.name = "Shallow water"
        self.animated = True
    def animate(self):
        self.char = self.variations[random.randint(0,len(self.variations)-1)]
       
class DeepWater:
    def __init__(self):
        self.blocked = True
        self.variations = "=-"
        self.char = self.variations[random.randint(0,len(self.variations)-1)]
        self.color = libtcod.Color(0, 0, 255)
        self.name = "Deep water"
        self.animated = True
    def animate(self):
        self.char = self.variations[random.randint(0,len(self.variations)-1)]
               
class Sand:
    def __init__(self):
        self.blocked = False
        self.variations = "=-"
        self.char = self.variations[random.randint(0,len(self.variations)-1)]
        self.color = libtcod.Color(random.randint(180, 220), random.randint(180, 220), 50)
        self.name = "Sand"
        self.animated = False

class Brush:
    def __init__(self):
        self.blocked = False
        self.variations = "mn"
        self.char = self.variations[random.randint(0,len(self.variations)-1)]
        self.color = libtcod.Color(0, random.randint(200, 255), 0)
        self.name = "Brush"
        self.animated = False

#Map objects: things that don't move, but aren't, strictly speaking, part of the terrain
class PathingBlocker:
    def __init__(self, x, y, chunk_map_objects):
        self.blocked = True
        self.x = x
        self.y = y
        self.variation_type = "random"
        self.variations = " "
        if self.variations == "random":
            self.char = self.variations[random.randint(0,len(self.variations)-1)]
        self.color = libtcod.Color(0, 0, 0)
        self.name = "Pathing blocker"
        self.orientation_type = None
        self.chunk = chunk_map_objects
        self.vulnerable = False
        chunk_map_objects.append(self)
        self.visible = True
        material = None
        mass = None

    def draw(self):
        (pos_x, pos_y) = to_camera_coordinates(self.x, self.y)
        if self.variation_type == "orientation":
            self.char = set_orientation()
        if pos_x is not None and self.visible == True:
            libtcod.console_set_default_foreground(con, self.color)
            libtcod.console_put_char(con, pos_x, pos_y, self.char, libtcod.BKGND_NONE)

    def clear(self):
        libtcod.console_put_char(con, self.x, self.y, ' ', libtcod.BKGND_NONE)
   
    def remove(self):
        self.x = -1
        self.y = -1
        self.visible = False
        chunk_map_objects.remove(self)
        self.chunk = None
       
    def hide(self):
        self.visible = False
       
    def show(self):
        self.visible = True
   
class StoneWall(PathingBlocker):
    def __init__(self, x, y, chunk_map_objects):
        self.blocked = True
        self.x = x
        self.y = y
        self.variation_type = "orientation"
        self.variations = "OI-"
        if self.variations == "random":
            self.char = self.variations[random.randint(0,len(self.variations)-1)]
        else:
            self.char = self.variations[0]
        self.color = libtcod.Color(150, 150, 150)
        self.name = "High stone wall"
        self.orientation_type = "wall"
        self.vulnerable = True
        chunk_map_objects.append(self)
        self.visible = True
        material = "Stone"
        mass = "Very Heavy"
   
#For orienting map tiles whose appearance depends on surrounding tiles
def set_orientation(obj):
    if obj.orientation_type == "wall":
        bIsWestNeighbor = False
        bIsNorthNeighbor = False
        bIsSouthNeighbor = False
        bIsEastNeighbor = False
        for map_object in obj.chunk:
            if map_object.x == obj.x - 1 and map_object.y == obj.y and map_object.orientation_type == obj.orientation_type:
                bIsWestNeighbor = True
            if map_object.x == obj.x + 1 and map_object.y == obj.y and map_object.orientation_type == obj.orientation_type:
                bIsEastNeighbor = True
            if map_object.x == obj.x and map_object.y == obj.y - 1 and map_object.orientation_type == obj.orientation_type:
                bIsNorthNeighbor = True
            if map_object.x == obj.x and map_object.y == obj.y + 1 and map_object.orientation_type == obj.orientation_type:
                bIsSouthNeighbor = True
        if bIsWestNeighbor == True and bIsEastNeighbor == True and bIsNorthNeighbor == False and bIsSouthNeighbor == False:
            obj.char == obj.variations[2]
        elif bIsWestNeighbor == False and bIsEastNeighbor == False and bIsNorthNeighbor == True and bIsSouthNeighbor == False:
            obj.char == obj.variations[1]
        else:
            obj.char == obj.variations[0]
