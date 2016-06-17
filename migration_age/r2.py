, simport libtcodpy as libtcod
import random

SCREEN_WIDTH = 80
SCREEN_HEIGHT = 50
MAP_WIDTH = 400
MAP_HEIGHT = 400
CAMERA_WIDTH = 80
CAMERA_HEIGHT = 49
LIMIT_FPS = 20
INFOBAR_HEIGHT = 1
ACTIONPANEL_WIDTH = 15
MENU_WIDTH = 20
GAME_FONT = 'arial10x10.png'

#This is NOT the speed of the game in general, just how often certain checks and updates fire (e.g., how often animals decide whether to move or not) (higher numbers are slower)
GAMESPEED = 5

#Minimum number of frames between player movement/other actions
MAX_MOVESPEED = GAMESPEED/2

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
            self.variation = "\""
        elif self.variation == 2:
            self.variation = "\'"
        elif self.variation == 3:
            self.variation = "`"
        self.color = libtcod.Color(0, 255, 0)
        self.type = "Grass; outdoor"

class DirtTile:
    def __init__(self):
        self.blocked = False
        self.block_sight = False
        self.variation = random.randint(1, 3)
        if self.variation == 1:
            self.variation = ";"
        elif self.variation == 2:
            self.variation = ","
        elif self.variation == 3:
            self.variation = ":"
        self.color = libtcod.Color(150, 70, 0)
        self.type = "Dirt; outdoor"

class TallGrassTile:
    def __init__(self):
        self.blocked = False
        self.block_sight = False
        self.variation = "i"
        self.color = libtcod.Color(0, 255, 0)
        self.type = "Tall grass; outdoor"


class RockTile:
    def __init__(self):
        self.blocked = True
        self.block_sight = False
        self.variation = "o"
        self.color = libtcod.Color(150, 150, 150)
        self.type = "Large rock; outdoor"

class Object:
    #this is a generic object: the player, a monster, an item, the stairs...
    #it's always represented by a character on screen.
    def __init__(self, x, y, char, color):
        self.x = x
        self.y = y
        self.char = char
        self.color = color
        self.name = "Object"
 
    def move(self, dx, dy):
        #move by the given amount, if the destination is not blocked
        if not map[self.x + dx][self.y + dy].blocked:
            if 50 < self.x + dx < MAP_WIDTH - 50 and 50 < self.y + dy < MAP_HEIGHT - 50:
                self.x += dx
                self.y += dy
 
    def draw(self):
        #set the color and then draw the character that represents this object at its position
        (pos_x, pos_y) = to_camera_coordinates(self.x, self.y)
        if pos_x is not None:
            libtcod.console_set_default_foreground(con, self.color)
            libtcod.console_put_char(con, pos_x, pos_y, self.char, libtcod.BKGND_NONE)
 
    def clear(self):
        #erase the character that represents this object
        libtcod.console_put_char(con, self.x, self.y, ' ', libtcod.BKGND_NONE)

class Player:
    #this is a generic object: the player, a monster, an item, the stairs...
    #it's always represented by a character on screen.
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.char = "@"
        self.color = libtcod.Color(255,255,255)
        self.name = "Player"
 
    def move(self, dx, dy):
        #move by the given amount, if the destination is not blocked
        if not map[self.x + dx][self.y + dy].blocked and mode == "move":
            if 0 < self.x + dx < MAP_WIDTH - 1 and 0 < self.y + dy < MAP_HEIGHT - 1:
                self.x += dx
                self.y += dy
        camera.refresh_position()
 
    def draw(self):
        #set the color and then draw the character that represents this object at its position
        (pos_x, pos_y) = to_camera_coordinates(self.x, self.y)
        if pos_x is not None:
            libtcod.console_set_default_foreground(con, self.color)
            libtcod.console_put_char(con, pos_x, pos_y, self.char, libtcod.BKGND_NONE)
 
    def clear(self):
        #erase the character that represents this object
        libtcod.console_put_char(con, self.x, self.y, ' ', libtcod.BKGND_NONE)

class Cursor:
    def __init__(self):
        self.x = player.x
        self.y = player.y
        self.char = "X"
        self.color = libtcod.Color(0,0,255)
    def move(self, dx, dy):
        #move by the given amount, if the destination is not blocked
        if player.x - CAMERA_WIDTH/2 - 1 < self.x + dx < player.x + CAMERA_WIDTH/2 and player.y - CAMERA_HEIGHT/2 - 1 < self.y + dy < player.y + CAMERA_HEIGHT/2 + 1 and mode == "look":
            self.x += dx
            self.y += dy
    def draw(self):
        #set the color and then draw the character that represents this object at its position
        (pos_x, pos_y) = to_camera_coordinates(self.x, self.y)
        if pos_x is not None:
            libtcod.console_set_default_foreground(con, self.color)
            libtcod.console_put_char(con, pos_x, pos_y, self.char, libtcod.BKGND_NONE)

#Generic land animal for testing purposes
class Bird:
    def __init__(self, x, y, npcs):
        self.x = x
        self.y = y
        self.char = "^"
        self.color = libtcod.Color(175,0,0)
        self.wait = 0
        self.speed = GAMESPEED * 10
        npcs.append(self)
        self.name = "^bird"
    def move(self, dx, dy):
        #move by the given amount, if the destination is not blocked
        if 0 < self.x + dx < MAP_WIDTH - 1 and 0 < self.y + dy < MAP_HEIGHT - 1:
            self.x += dx
            self.y += dy
    def ai(self):
        if self.wait == 0:
            self.move(random.randint(-1,1), random.randint(-1,1))
            self.wait = self.speed
        if self.wait > 0:
            self.wait -= 1
    def draw(self):
        #set the color and then draw the character that represents this object at its position
        (pos_x, pos_y) = to_camera_coordinates(self.x, self.y)
        if pos_x is not None:
            libtcod.console_set_default_foreground(con, self.color)
            libtcod.console_put_char(con, pos_x, pos_y, self.char, libtcod.BKGND_NONE)

    def clear(self):
        #erase the character that represents this object
        libtcod.console_put_char(con, self.x, self.y, ' ', libtcod.BKGND_NONE)

def spawn_bird(x, y):
    objects.append(Bird(x, y, npcs))

class game_camera:
    def __init__(self, x, y):
        self.x = player.x
        self.y = player.y
    def refresh_position(self):
        if CAMERA_WIDTH/2 < player.x < MAP_WIDTH - CAMERA_WIDTH/2:
            self.x = player.x
        if CAMERA_HEIGHT/2 < player.y < MAP_HEIGHT - CAMERA_HEIGHT/2:
            self.y = player.y

def make_map():
    global map
 
    #fill map with tiles
    map = []
    for y in range(MAP_HEIGHT):
        row = []
        for x in range(MAP_WIDTH):
            tileroll = random.randint(1, 1000)
            if tileroll >= 999:
                row.append(RockTile())
                spawn_bird(x, y)
            elif tileroll >= 990:
                row.append(DirtTile())
            elif tileroll >= 980:
                row.append(TallGrassTile())
            else:
                row.append(GrassTile())
        map.append(row)

def to_camera_coordinates(x, y):
    (x, y) = (x - camera.x + CAMERA_WIDTH/2, y - camera.y + CAMERA_HEIGHT/2)
    

    if (x < 0 or y < 0 or x >= CAMERA_WIDTH or y >= CAMERA_HEIGHT):
        return (None, None)

    return (x, y)

def refresh_infobar(infobar):
    libtcod.console_clear(infobar)
    infobar_text = ""
    if mode == "move":
        infobar_text = map[player.x][player.y].type + " "
        for mob in npcs:
            if mob.x == player.x and mob.y == player.y:
                infobar_text = infobar_text + mob.name + " "
        libtcod.console_print(infobar, 0, 0, infobar_text)
    if mode == "look":
        infobar_text = map[cursor.x][cursor.y].type + " "
        for mob in npcs:
            if mob.x == cursor.x and mob.y == cursor.y:
                infobar_text = infobar_text + mob.name + " "
        libtcod.console_print(infobar, 0, 0, infobar_text)

def refresh_menu(menu):
    libtcod.console_clear(menu)
    libtcod.console_print(menu, 1, 1, "Migration Age test")
    libtcod.console_print(menu, 1, 2, "l: hide this panel")
    libtcod.console_print(menu, 1, 3, "k: look mode")
    libtcod.console_print(menu, 1, 4, "arrow keys: move")
    libtcod.console_print(menu, 1, 5, "-/+: adjust speed")
    libtcod.console_print(menu, 1, 6, "  Current speed:" + str(GAMESPEED))
    libtcod.console_print(menu, 1, 7, "esc: quit")

def render_all():
    global color_light_wall
    global color_light_ground

    libtcod.console_clear(con)

    for y in range(CAMERA_HEIGHT):
        for x in range(CAMERA_WIDTH):
            (map_x, map_y) = (camera.x + x - CAMERA_WIDTH/2, camera.y + y - CAMERA_HEIGHT/2)
            libtcod.console_put_char(con, x, y, map[map_x][map_y].variation, libtcod.BKGND_NONE)
            libtcod.console_set_char_foreground(con, x, y, map[map_x][map_y].color)
                
    #draw all objects in the list
    for object in objects:
        object.draw()

    if cursor!= None:
        cursor.draw()
 
    #blit the contents of "con" to the root console
    libtcod.console_blit(con, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0, 0)

    #blit the infobar to the root console
    refresh_infobar(infobar)
    libtcod.console_blit(infobar, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0, SCREEN_HEIGHT - 1)

    #if we're showing the right-side menu, show it
    if show_menu == True:
        refresh_menu(menu)
        libtcod.console_blit(menu, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, SCREEN_WIDTH - MENU_WIDTH, 0)

def handle_keys():
    global show_menu
    global CAMERA_WIDTH
    global mode
    global cursor
    global time
    global player_wait
    global GAMESPEED
    global MAX_MOVESPEED

    for creatures in npcs:
        creatures.ai()

    if player_wait > 0:
        player_wait -= 1

    if time == "free":
        key = libtcod.console_check_for_keypress()  #real-time

    elif time == "step":
        key = libtcod.console_wait_for_keypress(True)  #turn-based
 
    if key.vk == libtcod.KEY_ENTER and key.lalt:
        #Alt+Enter: toggle fullscreen
        libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())
 
    elif key.vk == libtcod.KEY_ESCAPE:
        return True  #exit game

 
    #movement keys
    if libtcod.console_is_key_pressed(libtcod.KEY_UP) and player_wait == 0:
        player.move(0, -1)
        if cursor != None:
            cursor.move(0, -1)
        player_wait = MAX_MOVESPEED
 
    elif libtcod.console_is_key_pressed(libtcod.KEY_DOWN) and player_wait == 0:
        player.move(0, 1)
        if cursor != None:
            cursor.move(0, 1)
        player_wait = MAX_MOVESPEED
 
    elif libtcod.console_is_key_pressed(libtcod.KEY_LEFT) and player_wait == 0:
        player.move(-1, 0)
        if cursor != None:
            cursor.move(-1, 0)
        player_wait = MAX_MOVESPEED
 
    elif libtcod.console_is_key_pressed(libtcod.KEY_RIGHT) and player_wait == 0:
        player.move(1, 0)
        if cursor != None:
            cursor.move(1, 0)
        player_wait = MAX_MOVESPEED

    
    if key.vk == libtcod.KEY_CHAR:
        #Show or hide right-side menu
        if key.c == ord('l') and show_menu == False:
            show_menu = True
            CAMERA_WIDTH = CAMERA_WIDTH - MENU_WIDTH
            #Make sure when we do it, the cursor remains in view
            if mode == "look" and cursor.x > player.x + CAMERA_WIDTH/2:
                cursor.x = player.x + CAMERA_WIDTH/2 - 1
        elif key.c == ord('l') and show_menu == True:
            show_menu = False
            CAMERA_WIDTH = CAMERA_WIDTH + MENU_WIDTH

        #Look mode
        elif key.c == ord('k') and mode == "move":
            mode = "look"
            cursor = Cursor()
        elif key.c == ord('k') and mode == "look":
            mode = "move"
            cursor = None

        elif key.c == ord('=') and GAMESPEED < 9:
            GAMESPEED += 1
            MAX_MOVESPEED = GAMESPEED/2
        elif key.c == ord('-') and GAMESPEED > 0:
            GAMESPEED -= 1
            MAX_MOVESPEED = GAMESPEED/2

        #Switch between turn-based and free input
        elif key.c == ord('t') and time == "free":
            time = "step"
        #A bug in the current version of libtcod means we can't use this mode right now
        #elif key.c == ord('t') and time == "step":
        #    time = "free"
 
#############################################
# Initialization & Main Loop
#############################################
 
libtcod.console_set_custom_font(GAME_FONT, libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD)
libtcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, 'python/libtcod tutorial', False)
libtcod.sys_set_fps(LIMIT_FPS)
con = libtcod.console_new(SCREEN_WIDTH, SCREEN_HEIGHT)

infobar = libtcod.console_new(SCREEN_WIDTH, INFOBAR_HEIGHT)
menu = libtcod.console_new(MENU_WIDTH, SCREEN_HEIGHT)

show_menu = False

mode = "move"
cursor = None
time = "free"

npcs = []
birds = []

player_wait = 0
 
#create object representing the player
player = Player(MAP_WIDTH/2, MAP_HEIGHT/2)

camera = game_camera(player.x, player.y)
 
#create an NPC
npc = Bird(MAP_WIDTH/2 - 5, MAP_HEIGHT/2, npcs)
 
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


