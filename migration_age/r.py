import libtcodpy as libtcod
import random
 
#actual size of the window
SCREEN_WIDTH = 80
SCREEN_HEIGHT = 50
 
#size of the map
MAP_WIDTH = 200
MAP_HEIGHT = 200

CAMERA_WIDTH = 80
CAMERA_HEIGHT = 43
 
LIMIT_FPS = 20  #20 frames-per-second maximum
 
 
color_dark_wall = libtcod.Color(0, 0, 100)
color_dark_ground = libtcod.Color(50, 50, 150)
 
 
class Tile:
    #a tile of the map and its properties
    def __init__(self, blocked, block_sight = None):
        self.blocked = blocked
 
        #by default, if a tile is blocked, it also blocks sight
        if block_sight is None: block_sight = blocked
        self.block_sight = block_sight

class GrassTile:
    def __init__(self):
        self.blocked = False
        self.block_sight = False
        self.variation = random.randint(1, 3)
        if self.variation == 1:
            self.variation = "."
        elif self.variation == 2:
            self.variation = ","
        elif self.variation == 3:
            self.variation = ";"
        self.color = libtcod.Color(0, 255, 0)

class RockTile:
    def __init__(self):
        self.blocked = True
        self.block_sight = False
        self.variation = "o"
        self.color = libtcod.Color(150, 150, 150)
 
class Object:
    #this is a generic object: the player, a monster, an item, the stairs...
    #it's always represented by a character on screen.
    def __init__(self, x, y, char, color):
        self.x = x
        self.y = y
        self.char = char
        self.color = color
 
    def move(self, dx, dy):
        #move by the given amount, if the destination is not blocked
        if not map[self.x + dx][self.y + dy].blocked:
            self.x += dx
            self.y += dy
 
    def draw(self):
        #set the color and then draw the character that represents this object at its position
        libtcod.console_set_default_foreground(con, self.color)
        libtcod.console_put_char(con, self.x, self.y, self.char, libtcod.BKGND_NONE)
 
    def clear(self):
        #erase the character that represents this object
        libtcod.console_put_char(con, self.x, self.y, ' ', libtcod.BKGND_NONE)
 
 
 
def make_map():
    global map
 
    #fill map with tiles
    map = []
    for y in range(MAP_HEIGHT):
        row = []
        for x in range(MAP_WIDTH):
            if random.randint(1, 100) < 99:
                row.append(GrassTile())
            else:
                row.append(RockTile())
        map.append(row)


def move_camera(target_x, target_y):
    global camera_x, camera_y, fov_recompute
    x = target_x - CAMERA_WIDTH/2
    y = target_y - CAMERA_HEIGHT/2

    if x < 0: x = 0
    if y < 0: y = 0
    if x > MAP_WIDTH - CAMERA_WIDTH - 1: x = MAP_WIDTH - CAMERA_WIDTH - 1
    if y > MAP_HEIGHT - CAMERA_HEIGHT - 1: y = MAP_HEIGHT - CAMERA_HEIGHT - 1

    if x != camera_x or y != camera_y: fov_recompute = True

    (camera_x, camera_y) = (x, y)

def to_camera_coordinates(x, y):
    (x, y) = (x - camera_x, y - camera_y)

    if (x < 0 or y < 0 or x != CAMERA_WIDTH or y != CAMERA_HEIGHT):
        return (None, None)

    return (x, y) 
 
def render_all():
    global color_light_wall
    global color_light_ground
    global fov_recompute

    move_camera(player.x, player.y)

    if fov_recompute == True:
        fov_recompute = False
        libtcod.console_clear(con)

        for y in range(CAMERA_HEIGHT):
            for x in range(CAMERA_WIDTH):
                (map_x, map_y) = (camera_x + x, camera_y + y)
                libtcod.console_put_char(con, x, y, map[x][y].variation, libtcod.BKGND_NONE)
                
 
    #go through all tiles, and set their variation
#    for y in range(MAP_HEIGHT):
#        for x in range(MAP_WIDTH):
 
    #draw all objects in the list
    for object in objects:
        object.draw()
 
    #blit the contents of "con" to the root console
    libtcod.console_blit(con, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0, 0)
 
def handle_keys():
    #key = libtcod.console_check_for_keypress()  #real-time
    key = libtcod.console_wait_for_keypress(True)  #turn-based
 
    if key.vk == libtcod.KEY_ENTER and key.lalt:
        #Alt+Enter: toggle fullscreen
        libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())
 
    elif key.vk == libtcod.KEY_ESCAPE:
        return True  #exit game
 
    #movement keys
    if libtcod.console_is_key_pressed(libtcod.KEY_UP):
        player.move(0, -1)
        fov_recompute = True
 
    elif libtcod.console_is_key_pressed(libtcod.KEY_DOWN):
        player.move(0, 1)
        fov_recompute = True
 
    elif libtcod.console_is_key_pressed(libtcod.KEY_LEFT):
        player.move(-1, 0)
        fov_recompute = True
 
    elif libtcod.console_is_key_pressed(libtcod.KEY_RIGHT):
        player.move(1, 0)
        fov_recompute = True

 
 
#############################################
# Initialization & Main Loop
#############################################

(camera_x, camera_y) = (0, 0)
fov_recompute = True
 
libtcod.console_set_custom_font('arial10x10.png', libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD)
libtcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, 'python/libtcod tutorial', False)
libtcod.sys_set_fps(LIMIT_FPS)
con = libtcod.console_new(SCREEN_WIDTH, SCREEN_HEIGHT)
 
#create object representing the player
player = Object(10, 10, '@', libtcod.white)
 
#create an NPC
npc = Object(MAP_WIDTH/2 - 5, MAP_HEIGHT/2, '@', libtcod.yellow)
 
#the list of objects with those two
objects = [npc, player]
 
#generate map (at this point it's not drawn to the screen)
make_map()
 
 
while not libtcod.console_is_window_closed():
 
    #render the screen
    render_all()
 
    libtcod.console_flush()
 
    #erase all objects at their old locations, before they move
    for object in objects:
        object.clear()
 
    #handle keys and exit game if needed
    exit = handle_keys()
    if exit:
        break
