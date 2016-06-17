import random
import shelve
import os.path
#The Doryen Library - Documentation: http://roguecentral.org/doryen/data/libtcod/doc/1.5.1/index2.html
import libtcodpy as libtcod

#Main object for keeping track of game variables, rendering the GUI and objects, handling the game loop and keyboard inputs,
#and generally keeping things tidy.
class GameObject:
    def __init__(self):
        #GUI and map variables
        self.SCREEN_WIDTH = 100
        self.SCREEN_HEIGHT = 60
        #Size of the infobar along the bottom of the screen
        self.INFOBAR_HEIGHT = 1
        #Size of the area visible to the in-game camera
        self.CAMERA_WIDTH = self.SCREEN_WIDTH-2
        self.CAMERA_HEIGHT = self.SCREEN_HEIGHT-self.INFOBAR_HEIGHT-3
        #Size of the right-side hideable in-game menu
        self.MENU_WIDTH = 20
        self.GAME_FONT = 'arial10x10.png'
        #Maximum possible level size
        self.LEVEL_SIZE = 19
        #Maximum game FPS; 1 frame is also the basic unit of in-game time
        self.LIMIT_FPS = 20
        self.PLAYER_START_X = 0
        self.PLAYER_START_Y = 1
        #Directory for savegame files
        self.SAVE_DIRECTORY = "savegame/"
        #Directory for files containing level layouts
        self.LEVEL_DIRECTORY = "levels/"
        #Variable controlling frame interval for certain events
        self.GAMESPEED = 3
        #Minimum number of frames between player movements/actions
        self.MAX_MOVESPEED = self.GAMESPEED/2
        #Minimum number of frames between certain GUI actions
        self.GUI_WAIT = 3
        #Used for setting the appearance of wall tiles
        #In order: vert, horiz, rightT, leftT, downT, upT, X, topL, botL, topR, botR, lone
        self.ASCII_BOX_CHARACTERS = [chr(186), chr(205), chr(204), chr(185), chr(203), chr(202), chr(206), chr(187), chr(188), chr(201), chr(200), chr(79)]
        self.ASCII_BOX_CHARACTERS = "".join(self.ASCII_BOX_CHARACTERS)
        self.PLAYER_CHARACTER = 1

        #Game state and GUI control variables
        #Whether the right-side in-game menu is visible or hidden
        self.show_menu = False
        #Values are "move" or "look"
        self.mode = "move"
        #Used for controlling the cursor in look mode
        self.cursor = None
        #Whether we're using real time or taking turns
        self.time = "free"
        #Input control variables; used to prevent some actions from happening too often
        self.player_wait = 0
        self.gui_wait = 0
        #Main player object
        self.player = None
        #Main camera object
        self.camera = None
        self.paused = False

        #Main libtcod console and parameters
        libtcod.console_set_custom_font(self.GAME_FONT, libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD)
        libtcod.console_init_root(self.SCREEN_WIDTH, self.SCREEN_HEIGHT, "chirality", False)
        libtcod.sys_set_fps(self.LIMIT_FPS)
        self.con = libtcod.console_new(self.SCREEN_WIDTH, self.SCREEN_HEIGHT)
        #Libtcod consoles for managing GUI
        self.game_view = libtcod.console_new(self.CAMERA_WIDTH, self.CAMERA_HEIGHT)
        self.infobar = libtcod.console_new(self.SCREEN_WIDTH, self.INFOBAR_HEIGHT)
        self.menu = libtcod.console_new(self.MENU_WIDTH, self.SCREEN_HEIGHT)
        self.gui_background = libtcod.console_new(self.SCREEN_WIDTH, self.SCREEN_HEIGHT)

    #Start the game and run the main game loop
    def start_game(self):
        self.player = Player(self.PLAYER_START_X, self.PLAYER_START_Y)
        self.level = LevelObject("chiral_test", loaded=True)
        for x in range(len(self.level.map)):
            for y in range(len(self.level.map[x])):
                self.level.map[x][y].char = self.level.map[x][y].set_variation()
        self.level.actors.append(self.player)
        self.camera = GameCamera()

        while not libtcod.console_is_window_closed():
            #Render the screen
            self.render_all()
            libtcod.console_flush()
            #Handle keys and exit game if needed
            exit = game.handle_keys()
            if exit:
                break

    def refresh_infobar(self, infobar):
        libtcod.console_clear(infobar)
        infobar_text = ""
        if self.mode == "look":
            for actor in self.level.actors:
                if actor.x == self.cursor.x and actor.y == self.cursor.y and hasattr(actor, "name") == True:
                    infobar_text = infobar_text + actor.name + " "
            libtcod.console_print(infobar, 0, 0, infobar_text)

    def refresh_main_view(self, main_view):
        libtcod.console_clear(main_view)
        self.camera.refresh_position()
        for y in xrange(self.CAMERA_HEIGHT):
            for x in xrange(self.CAMERA_WIDTH):
                (map_x, map_y) = (self.camera.x+x-self.CAMERA_WIDTH/2, self.camera.y+y-self.CAMERA_HEIGHT/2)
                if 0 <= map_x < len(self.level.map) and 0 <= map_y < len(self.level.map):
                    libtcod.console_put_char(main_view, x, y, self.level.map[map_x][map_y].char, libtcod.BKGND_NONE)
                    libtcod.console_set_char_foreground(main_view, x, y, self.level.map[map_x][map_y].color)
                elif len(self.level.map)*-1 < map_x < 0 and 0 <= map_y < len(self.level.map):
                    libtcod.console_put_char(main_view, x, y, self.level.map[map_x*-1][map_y].char, libtcod.BKGND_NONE)
                    libtcod.console_set_char_foreground(main_view, x, y, self.level.map[map_x*-1][map_y].color)
                else:
                    libtcod.console_put_char(main_view, x, y, " ", libtcod.BKGND_NONE)

        for actor in self.level.actors:
            self.draw_actor(actor, main_view)

        if self.cursor!= None:
            self.draw_actor(self.cursor, main_view)
                

    def refresh_menu(self, menu):
        libtcod.console_clear(menu)
        libtcod.console_print(menu, 1, 1, "chirality test")
        libtcod.console_print(menu, 1, 2, "l: hide this panel")
        libtcod.console_print(menu, 1, 3, "k: look mode")
        libtcod.console_print(menu, 1, 4, "arrow keys: move")
        libtcod.console_print(menu, 1, 5, "-/+: adjust speed")
        libtcod.console_print(menu, 1, 6, "  Current speed:" + str(self.GAMESPEED))
        libtcod.console_print(menu, 1, 7, "esc: quit")
        libtcod.console_print(menu, 1, 15, "Level size: "+str(self.LEVEL_SIZE))

    #While the game is running, render a solid background to use as border between other GUI elements
    def refresh_gui_background(self, gui):
        libtcod.console_clear(gui)
        for x in xrange(self.SCREEN_WIDTH):
            for y in xrange(self.SCREEN_HEIGHT):
                libtcod.console_set_char_background(gui, x, y, libtcod.Color(100, 100, 100))
        if self.paused == True:
            pause_text = "***PAUSED***"
            for x in xrange(12):
                libtcod.console_set_char_background(gui, self.CAMERA_WIDTH-15+x, 0, libtcod.Color(100, 100, 200))
                libtcod.console_put_char(gui, self.CAMERA_WIDTH-15+x, 0, pause_text[x], libtcod.BKGND_NONE)
                libtcod.console_set_char_foreground(gui, self.CAMERA_WIDTH-15+x, 0, libtcod.Color(255, 255, 255))

    def force_gui_refresh(self):
        libtcod.console_clear(self.gui_background)
        self.refresh_gui_background(self.gui_background)
        libtcod.console_blit(self.gui_background, 0, 0, self.SCREEN_WIDTH, self.SCREEN_HEIGHT, 0, 0, 0)
              
    #Method for drawing objects (player, creatures, items)
    def draw_actor(self, actor, console):
        (pos_x, pos_y) = self.to_camera_coordinates(actor.x, actor.y)
        if pos_x != None and actor.char != " ":
            libtcod.console_set_default_foreground(console, actor.color)
            libtcod.console_put_char(console, pos_x, pos_y, actor.char, libtcod.BKGND_NONE)
        
    #Rendering the main view and GUI elements
    def render_all(self):
        #blit the contents of "con" to the root console
        libtcod.console_blit(self.con, 0, 0, self.SCREEN_WIDTH, self.SCREEN_HEIGHT, 0, 0, 0)
        #blit the contents of the GUI background to the root console
        self.refresh_gui_background(self.gui_background)
        libtcod.console_blit(self.gui_background, 0, 0, self.SCREEN_WIDTH, self.SCREEN_HEIGHT, 0, 0, 0)
        #blit the contents of the game_view to the root console
        self.refresh_main_view(self.game_view)
        libtcod.console_blit(self.game_view, 0, 0, self.CAMERA_WIDTH, self.CAMERA_HEIGHT, 0, 1, 1)
        #blit the infobar to the root console
        self.refresh_infobar(self.infobar)
        libtcod.console_blit(self.infobar, 0, 0, self.CAMERA_WIDTH, self.SCREEN_HEIGHT, 0, 1, self.SCREEN_HEIGHT - 2)
        #if we're showing the right-side menu, it as well
        if self.show_menu == True:
            self.refresh_menu(self.menu)
            libtcod.console_blit(self.menu, 0, 0, self.MENU_WIDTH-1, self.SCREEN_HEIGHT-2, 0, self.SCREEN_WIDTH - self.MENU_WIDTH, 1)

    #Handling keys and certain looped elements of game logic
    def handle_keys(self):
  
        key = libtcod.console_check_for_keypress()

        if self.paused == False:
            #Creature AI loop
            for actor in self.level.actors:
                if hasattr(actor, "ai") == True:
                    actor.ai()
            if self.player_wait > 0:
                self.player_wait -= 1
            #Player movement keys
            if libtcod.console_is_key_pressed(libtcod.KEY_UP) and self.player_wait == 0:
                self.player.move(0, -1)
                if self.cursor != None:
                    self.cursor.move(0, -1)
                self.player_wait = game.MAX_MOVESPEED
         
            elif libtcod.console_is_key_pressed(libtcod.KEY_DOWN) and self.player_wait == 0:
                self.player.move(0, 1)
                if self.cursor != None:
                    self.cursor.move(0, 1)
                self.player_wait = game.MAX_MOVESPEED
         
            elif libtcod.console_is_key_pressed(libtcod.KEY_LEFT) and self.player_wait == 0:
                self.player.move(-1, 0)
                if self.cursor != None:
                    self.cursor.move(-1, 0)
                self.player_wait = game.MAX_MOVESPEED
         
            elif libtcod.console_is_key_pressed(libtcod.KEY_RIGHT) and self.player_wait == 0:
                self.player.move(1, 0)
                if self.cursor != None:
                    self.cursor.move(1, 0)
                self.player_wait = game.MAX_MOVESPEED

        if self.gui_wait > 0:
            self.gui_wait -=1
        
        if self.cursor != None:
            self.cursor.blink()
     
        #if key.vk == libtcod.KEY_ENTER and key.lalt:
        #    #Alt+Enter: toggle fullscreen
        #    libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())
     
        elif key.vk == libtcod.KEY_ESCAPE:
            return True  #exit game

        #Pause and unpause the game
        if libtcod.console_is_key_pressed(libtcod.KEY_SPACE):
            if self.gui_wait == 0:
                if self.paused == True:
                    self.paused = False
                elif self.paused == False:
                    self.paused = True
                self.gui_wait = self.GUI_WAIT
        
        if key.vk == libtcod.KEY_CHAR:
            #Show or hide right-side menu
            if key.c == ord('l') and self.show_menu == False:
                self.show_menu = True
                self.CAMERA_WIDTH = self.CAMERA_WIDTH - self.MENU_WIDTH
                #Make sure when we do it, the cursor remains in view
                if self.mode == "look" and self.cursor.x > self.player.x + self.CAMERA_WIDTH/2:
                    self.cursor.x = self.player.x + self.CAMERA_WIDTH/2 - 1
            elif key.c == ord('l') and self.show_menu == True:
                self.show_menu = False
                self.CAMERA_WIDTH = self.CAMERA_WIDTH + self.MENU_WIDTH

            #Look mode
            elif key.c == ord('k') and self.mode == "move":
                self.mode = "look"
                self.cursor = Cursor()
            elif key.c == ord('k') and self.mode == "look":
                self.mode = "move"
                self.cursor = None

            #Adjust game speed
            elif key.c == ord('=') and self.GAMESPEED < 9:
                self.GAMESPEED += 1
                self.MAX_MOVESPEED = self.GAMESPEED/2
            elif key.c == ord('-') and self.GAMESPEED > 0:
                self.GAMESPEED -= 1
                self.MAX_MOVESPEED = self.GAMESPEED/2

    #Converts map x, y to coordinates relative to the game camera
    def to_camera_coordinates(self, x, y):
        (x, y) = (x - self.camera.x + self.CAMERA_WIDTH/2, y - self.camera.y + self.CAMERA_HEIGHT/2)
        if (x < 0 or y < 0 or x >= self.CAMERA_WIDTH or y >= self.CAMERA_HEIGHT):
            return (None, None)
        return (x, y)
    ##Gets us an ASCII character from an int
    #def achr(self, i):
    #    c = chr(i).encode("ascii", "replace")
    #    return c

#An object containing the level's map and actors. Levels can be
#saved an loaded. Loaded levels get their map[] and objects[]
#attributes from a saved text file.
class LevelObject:
    def __init__(self, name, loaded=False):
        self.map = []
        self.actors = []
        self.name = name
        if loaded == False:
            for x in xrange(game.LEVEL_SIZE):
                row = []
                for y in xrange(game.LEVEL_SIZE):
                    i = random.randint(0,6)
                    if i != 0 and y != 0 and x != game.LEVEL_SIZE:
                        row.append(MapTile(x, y))
                    else:
                        row.append(WallTile(x, y))
                self.map.append(row)
        if loaded == True:
            self.gen_from_file(game.LEVEL_DIRECTORY+self.name+".txt")

    def save_level(self):
        file = shelve.open(str(game.SAVE_DIRECTORY)+str(self.name), "n")
        file["map"] = self.map
        file["objects"] = self.objects
        file.close()

    #Used to load a saved in-progress level
    def load_level(self):
        pass

    #Used to load level information from a file, for a new level
    def gen_from_file(self, filename):
        self.map = []
        with open(filename) as f:
            linelist = f.readlines()
        game.LEVEL_SIZE = len(linelist[0])
        for h in xrange(game.LEVEL_SIZE):
            row = []
            for v in xrange(game.LEVEL_SIZE):
                if linelist[v][h] == " ":
                    row.append(MapTile(v, h))
                elif linelist[v][h] == "@":
                    row.append(MapTile(v, h))
                    game.player.y = v
                    game.player.x = h
                else:
                    row.append(WallTile(v, h))
            self.map.append(row)
                    
            

#Generic actor class
class GameActor:
    def __init__(self, x, y, objects):
        self.x = x
        self.y = y
        self.char = "@"
        self.color = libtcod.Color(255,255,255)
        self.name = "Actor"
        #Whether this actor blocks other unit movement onto the same tile
        self.blocks = True

    #Generic actor movement
    def move(self, dx, dy):
        new_x = self.x + dx
        new_y = self.y + dy
        if game.LEVEL_SIZE*-1 < new_x < game.LEVEL_SIZE and 0 < new_y < game.LEVEL_SIZE:
            if new_x >= 0 and game.level.map[new_x][new_y].blocked == False:
                if self.get_blocked(new_x, new_y) == False:
                    self.x += dx
                    self.y += dy
            elif new_x < 0 and  game.level.map[new_x*-1][new_y].blocked == False:
                if self.get_blocked(new_x, new_y) == False:
                    self.x += dx
                    self.y += dy

    def get_blocked(self, x, y):
        for actor in game.level.actors:
            if actor.x == x and actor.y == y and actor.blocks==True:
                return True
            else:
                return False


    #Hide the object; draw_object won't draw objects represented by " ".
    def hide(self):
        self.char = " "

    #Remove references to an object and make it invisible, effectively removing it from the game.
    def remove(self):
        #aka that place in Slice
        self.x = -10000
        self.y = -10000
        self.char = " " #Remember, draw_object() ignores " " characters
        game.level.actors.remove(self)

class Player(GameActor):
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.char = "@"
        self.color = libtcod.Color(255,255,255)
        self.name = "Player"
        self.blocks = True

class Cursor(GameActor):
    def __init__(self):
        self.x = game.player.x
        self.y = game.player.y
        self.char = "X"
        self.color = libtcod.Color(0,0,255)
        self.wait = 5
    def move(self, dx, dy):
        if game.camera.x - game.CAMERA_WIDTH/2 - 1 < self.x + dx < game.camera.x + game.CAMERA_WIDTH/2 and game.camera.y - game.CAMERA_HEIGHT/2 - 1 < self.y + dy < game.camera.y + game.CAMERA_HEIGHT/2 + 1 and game.mode == "look":
            self.x += dx
            self.y += dy
    def blink(self):
        if self.wait > 0:
            self.wait += -1
        elif self.wait == 0 and self.char == "X":
            self.char = " "
            self.wait = 5
        elif self.wait == 0 and self.char == " ":
            self.char = "X"
            self.wait = 5

#Used to keep track of what to render onscreen, and to differentiate the position of the camera from the position of the player, in case we want to move one and not the other
class GameCamera:
    def __init__(self):
        self.x = game.player.x
        self.y = game.player.y
    def refresh_position(self):
        self.x, self.y = game.player.x, game.player.y

#Map tile objects store data about the map at a given x, y coordinate
class MapTile:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.blocked = False
        self.variations = ".,"
        self.variation_type = "random"
        self.char = "?"
        random_gray = random.randint(150, 200)
        self.color = libtcod.Color(random_gray, random_gray, random_gray)
        self.name = ""
        self.animated = False

    #Sets a random variation for tiles with .variation_type = "random", and
    #orients tiles with .variation_type = "wall" according to how many
    #neighbors they possess
    def set_variation(self):
        if self.variation_type == "random":
            char = self.variations[random.randint(0,len(self.variations)-1)]
            return char
        elif self.variation_type == "wall" and len(self.variations) == 12:
            char = "?"
            #Neighbor locations
            bN, bS, bE, bW = False, False, False, False
            for map_tile in game.level.map:
                if self.check_in_bounds(self.x, self.y-1) == True:
                    if game.level.map[self.x][self.y-1].variation_type == "wall":
                        bN = True
                if self.check_in_bounds(self.x, self.y+1) == True:
                    if game.level.map[self.x][self.y+1].variation_type == "wall":
                        bS = True
                if self.check_in_bounds(self.x-1, self.y) == True:
                    if game.level.map[self.x-1][self.y].variation_type == "wall":
                        bW = True
                if self.check_in_bounds(self.x+1, self.y) == True:
                    if game.level.map[self.x+1][self.y].variation_type == "wall":
                        bE = True
            if bN == True and bS == True and bE == False and bW == False:
                char = self.variations[0]
            elif bN == True or bS == True and bE == False and bW == False:
                char = self.variations[0]
            elif bE == True and bW == True and bN == False and bS == False:
                char = self.variations[1]
            elif bE == True or bW == True and bN == False and bS == False:
                char = self.variations[1]
            elif bN == True and bE == True and bS == True and bW == False:
                char = self.variations[2]
            elif bN == True and bW == True and bS == True and bE == False:
                char = self.variations[3]
            elif bS == True and bE == True and bW == True and bN == False:
                char = self.variations[4]
            elif bN == True and bE == True and bW == True and bS == False:
                char = self.variations[5]
            elif bN == True and bE == True and bS == True and bW == True:
                char = self.variations[6]
            elif bS == True and bW == True and bN == False and bE == False:
                char = self.variations[7]
            elif bN == True and bW == True and bE == False and bS == False:
                char = self.variations[8]
            elif bS == True and bE == True and bN == False and bW == False:
                char = self.variations[9]
            elif bN == True and bE == True and bW == False and bS == False:
                char = self.variations[10]
            elif bS == False and bW == False and bN == False and bE == False:
                char = self.variations[11]
            return char

    #Returns "true" if the target x, y coordinates are within the level
    def check_in_bounds(self, x, y):
        if 0 < x < game.LEVEL_SIZE and 0 < y < game.LEVEL_SIZE:
            return True
        else:
            return False

class WallTile(MapTile):
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.blocked = True
        self.variation_type = "wall"
        #In order: vert, horiz, rightT, leftT, downT, upT, X, topL, botL, topR, botR, lone
        #Objects with variation_type "wall" MUST have 12 .variations listed and they
        #MUST be in the above order
        self.variations = game.ASCII_BOX_CHARACTERS
        self.char = "?"
        self.color = libtcod.Color(210, 210, 210)
        self.name = "Wall"
        self.animated = False

game = GameObject()
game.start_game()
