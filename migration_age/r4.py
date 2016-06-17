import random
import shelve
import os.path
#The Doryen Library - Documentation: http://roguecentral.org/doryen/data/libtcod/doc/1.5.1/index2.html
import libtcodpy as libtcod
#Tiles and map objects for Migration Age
import rtiles

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
        #Size of map chunks used by map generator
        self.CHUNK_SIZE = 128
        #The square root of the number of chunks that are active at any given time
        #Used to control the size of active_chunks (always a square)
        self.ACTIVE_CHUNK_SIZE = 3
        #Maximum game FPS; 1 frame is also the basic unit of in-game time
        self.LIMIT_FPS = 20
        #We begin in the center of this chunk
        self.PLAYER_START_X = 100
        self.PLAYER_START_Y = 200
        #Directory for the savegame's map
        self.MAP_DIRECTORY = "map/"
        #Variable controlling frame interval for certain events
        self.GAMESPEED = 3
        #Minimum number of frames between player movements/actions
        self.MAX_MOVESPEED = self.GAMESPEED/2
        #Minimum number of frames between certain GUI actions
        self.GUI_WAIT = 3

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
        #All objects currently being simulated in the game
        self.objects = []
        #All loaded, active map chunks
        self.active_chunks = None
        self.paused = False
        self.loading = -1

        #Main libtcod console and parameters
        libtcod.console_set_custom_font(self.GAME_FONT, libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD)
        libtcod.console_init_root(self.SCREEN_WIDTH, self.SCREEN_HEIGHT, "Migration Age", False)
        libtcod.sys_set_fps(self.LIMIT_FPS)
        self.con = libtcod.console_new(self.SCREEN_WIDTH, self.SCREEN_HEIGHT)
        #Libtcod consoles for managing GUI
        self.game_view = libtcod.console_new(self.CAMERA_WIDTH, self.CAMERA_HEIGHT)
        self.infobar = libtcod.console_new(self.SCREEN_WIDTH, self.INFOBAR_HEIGHT)
        self.menu = libtcod.console_new(self.MENU_WIDTH, self.SCREEN_HEIGHT)
        self.gui_background = libtcod.console_new(self.SCREEN_WIDTH, self.SCREEN_HEIGHT)

    #Start the game and run the main game loop
    def start_game(self):
        self.player = Player(self.CHUNK_SIZE*self.PLAYER_START_X+self.CHUNK_SIZE/2, self.CHUNK_SIZE*self.PLAYER_START_Y+self.CHUNK_SIZE/2)
        self.active_chunks = ActiveChunks()
        self.player.assign_player_to_chunk()
        self.camera = GameCamera()

        while not libtcod.console_is_window_closed():
            #Render the screen
            self.render_all()
            libtcod.console_flush()
            #Erase all objects at their old locations, before they move
            for object in self.objects:
                object.clear()
            #Handle keys and exit game if needed
            exit = game.handle_keys()
            if exit:
                break

    def refresh_infobar(self, infobar):
        libtcod.console_clear(infobar)
        infobar_text = ""
        if self.mode == "move":
            chunk_count_x, chunk_count_y, local_x, local_y = self.to_actv_and_local_coords(self.player.x, self.player.y)
            infobar_text = self.active_chunks.map[chunk_count_x][chunk_count_y].chunk[local_x][local_y].name + " "
            for mob in self.active_objects:
                if mob.x == self.player.x and mob.y == self.player.y and hasattr(mob, "name") == True:
                    if mob.name != "Player":
                        infobar_text = infobar_text + mob.name + " "
            libtcod.console_print(infobar, 0, 0, infobar_text)
        if self.mode == "look":
            chunk_count_x, chunk_count_y, local_x, local_y = self.to_actv_and_local_coords(self.cursor.x, self.cursor.y)
            infobar_text = self.active_chunks.map[chunk_count_x][chunk_count_y].chunk[local_x][local_y].name + " "
            for mob in self.active_objects:
                if mob.x == self.cursor.x and mob.y == self.cursor.y and hasattr(mob, "name") == True:
                    infobar_text = infobar_text + mob.name + " "
            libtcod.console_print(infobar, 0, 0, infobar_text)

    def refresh_main_view(self, main_view):
        libtcod.console_clear(main_view)
        for y in xrange(self.CAMERA_HEIGHT):
            for x in xrange(self.CAMERA_WIDTH):
                #First, get the absolute map coordinates of whatever's in view
                (map_x, map_y) = (self.camera.x+x-self.CAMERA_WIDTH/2, self.camera.y+y-self.CAMERA_HEIGHT/2)
                #Then, get which chunk it's on, and where on that chunk it is
                chunk_count_x, chunk_count_y, local_x, local_y = self.to_chunk_and_local_coords(map_x, map_y)
                #Convert chunk coords to chunk coords relative to the player, offset southeast by 1 (because player is always at 1, 1 in active_chunks)
                #(and what we really want is the index of the chunk in active_chunks)
                active_x, active_y = self.abst_actv_chunk_coords(chunk_count_x, chunk_count_y)
                #Now, render the appropriate char based on the coords
                libtcod.console_put_char(main_view, x, y, self.active_chunks.map[active_x][active_y].chunk[local_x][local_y].char, libtcod.BKGND_NONE)
                libtcod.console_set_char_foreground(main_view, x, y, self.active_chunks.map[active_x][active_y].chunk[local_x][local_y].color)

        self.active_objects = self.get_active_objects()

        for object in self.active_objects:
            self.draw_object(object, main_view)

        if self.cursor!= None:
            self.draw_object(self.cursor, main_view)
                

    def refresh_menu(self, menu):
        libtcod.console_clear(menu)
        libtcod.console_print(menu, 1, 1, "Migration Age test")
        libtcod.console_print(menu, 1, 2, "l: hide this panel")
        libtcod.console_print(menu, 1, 3, "k: look mode")
        libtcod.console_print(menu, 1, 4, "arrow keys: move")
        libtcod.console_print(menu, 1, 5, "-/+: adjust speed")
        libtcod.console_print(menu, 1, 6, "  Current speed:" + str(self.GAMESPEED))
        libtcod.console_print(menu, 1, 7, "esc: quit")
        libtcod.console_print(menu, 1, 15, "Infinite map test")

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
        if self.loading > -1:
            loading_text = "***LOADING***"
            for x in xrange(13):
                libtcod.console_set_char_background(gui, 15+x, 0, libtcod.Color(100, 100, 200))
                libtcod.console_put_char(gui, 15+x, 0, loading_text[x], libtcod.BKGND_NONE)
                libtcod.console_set_char_foreground(gui, 15+x, 0, libtcod.Color(255, 255, 255))

    def force_gui_refresh(self):
        libtcod.console_clear(self.gui_background)
        self.refresh_gui_background(self.gui_background)
        libtcod.console_blit(self.gui_background, 0, 0, self.SCREEN_WIDTH, self.SCREEN_HEIGHT, 0, 0, 0)
              
    #Method for drawing objects (player, creatures, items)
    def draw_object(self, obj, console):
        (pos_x, pos_y) = self.to_camera_coordinates(obj.x, obj.y)
        if pos_x is not None and obj.char != " ":
            libtcod.console_set_default_foreground(console, obj.color)
            libtcod.console_put_char(console, pos_x, pos_y, obj.char, libtcod.BKGND_NONE)
        
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

        if self.paused == False:
            #Creature AI loop
            for creature in self.active_objects:
                if hasattr(creature, "ai") == True:
                    creature.ai()
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

        if self.time == "free":
            key = libtcod.console_check_for_keypress()  #real-time

        elif self.time == "step":
            key = libtcod.console_wait_for_keypress(True)  #turn-based
     
        if key.vk == libtcod.KEY_ENTER and key.lalt:
            #Alt+Enter: toggle fullscreen
            libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())
     
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

            #Switch between turn-based and free input
            elif key.c == ord('t') and self.time == "free":
                self.time = "step"
            #A bug in the current version of libtcod means we can't use this mode right now
            #elif key.c == ord('t') and self.time == "step":
            #    self.time = "free"

    #Get a list of all objects that are considered active in the game world
    def get_active_objects(self):
        active_objects = []
        for x in xrange(self.ACTIVE_CHUNK_SIZE):
            for y in xrange(self.ACTIVE_CHUNK_SIZE):
               active_objects.extend(self.active_chunks.map[x][y].objects)
        return active_objects

    #Mathematical transformations for converting different coordinate systems the game uses between one another
    def to_camera_coordinates(self, x, y):
        (x, y) = (x - self.camera.x + self.CAMERA_WIDTH/2, y - self.camera.y + self.CAMERA_HEIGHT/2)
        if (x < 0 or y < 0 or x >= self.CAMERA_WIDTH or y >= self.CAMERA_HEIGHT):
            return (None, None)
        return (x, y)
    #Converts the absolute coordinates of a chunk to its position in the active_chunks list
    #for accessing values of that chunk
    def abst_actv_chunk_coords(self, abst_chunk_x, abst_chunk_y):
        actv_chunk_x = abst_chunk_x - self.player.chunk_x + 1
        actv_chunk_y = abst_chunk_y - self.player.chunk_y + 1
        return (actv_chunk_x, actv_chunk_y)
    #From x, y coordinates get the location of the chunk at the specified coordinates in active_chunks
    #and the local coordinates on that chunk
    def to_actv_and_local_coords(self, map_x, map_y):
        chunk_x, chunk_y = self.to_chunk_coords(map_x, map_y)
        active_x, active_y = self.abst_actv_chunk_coords(chunk_x, chunk_y)
        local_x = map_x % self.CHUNK_SIZE
        local_y = map_y % self.CHUNK_SIZE
        return (active_x, active_y, local_x, local_y)
    #For x, y coordinates get the location of the chunk in active_chunks
    def to_actv_coords(self, map_x, map_y):
        chunk_x, chunk_y = self.to_chunk_coords(map_x, map_y)
        active_x, active_y = self.abst_actv_chunk_coords(chunk_x, chunk_y)
        return (active_x, active_y)
    #For x, y coordinates get the chunk coordinates of the chunk at that location, and the local
    #coordinates on that chunk
    def to_chunk_and_local_coords(self, map_x, map_y):
        chunk_count_x = map_x/game.CHUNK_SIZE
        chunk_count_y = map_y/game.CHUNK_SIZE
        local_x = map_x % game.CHUNK_SIZE
        local_y = map_y % game.CHUNK_SIZE
        return (chunk_count_x, chunk_count_y, local_x, local_y)
    #For x, y coordinates get the chunk at those coordinates
    def to_chunk_coords(self, map_x, map_y):
        chunk_count_x = map_x/game.CHUNK_SIZE
        chunk_count_y = map_y/game.CHUNK_SIZE
        return (chunk_count_x, chunk_count_y)
    #Get the highest x and y values found on a given chunk
    def chunk_max_dimensions(self, chunk_x, chunk_y):
        chunk_max_x = (chunk_count_x+1)*game.CHUNK_SIZE-1
        chunk_max_y = (chunk_count_y+1)*game.CHUNK_SIZE-1
        return (chunk_max_x, chunk_max_y)
    #Get the lowest x and y values found on a given chunk
    def chunk_min_dimensions(self, chunk_x, chunk_y):
        chunk_min_x = chunk_count_x*game.CHUNK_SIZE+1
        chunk_min_y = chunk_count_y*game.CHUNK_SIZE+1
        return (chunk_min_x, chunk_min_y)

#An object containing all chunks currently loaded and being simulated
class ActiveChunks:
    def __init__(self):
        self.map = []
        for x in xrange(game.ACTIVE_CHUNK_SIZE):
            row = []
            for y in xrange(game.ACTIVE_CHUNK_SIZE):
                row.append(None)
            self.map.append(row)
        #Now, get the chunk coords for the starting chunks
        starting_chunks = self.get_adjacent_chunks(game.player)
        #Check if there's a chunk file for these chunks; if there is, load it. Otherwise, create a new chunk.
        player_active_x, player_active_y = game.to_actv_coords(game.player.x, game.player.y)
        for x in xrange(0-game.ACTIVE_CHUNK_SIZE/2, game.ACTIVE_CHUNK_SIZE/2+1):
            for y in xrange(0-game.ACTIVE_CHUNK_SIZE/2, game.ACTIVE_CHUNK_SIZE/2+1):
                if os.path.isfile(game.MAP_DIRECTORY+str(x+game.player.chunk_x)+"_"+str(y+game.player.chunk_y)) == True:
                    file = shelve.open(str(game.MAP_DIRECTORY)+str(x+game.player.chunk_x)+"_"+str(y+game.player.chunk_y), "r")
                    self.map[x+1][y+1] = Chunk(x+game.player.chunk_x, y+game.player.chunk_y, True)
                    self.map[x+1][y+1].chunk = file["chunk"]
                    self.map[x+1][y+1].objects = file["objects"]
                    file.close()
                else:
                    self.map[x+1][y+1] = Chunk(x+game.player.chunk_x, y+game.player.chunk_y, False)

    #Gets the COORDINATES for the chunk the player is on and the adjacent chunks
    def get_adjacent_chunks(self, player):
        adjacent_chunks = []
        for x in xrange(0-game.ACTIVE_CHUNK_SIZE/2, game.ACTIVE_CHUNK_SIZE/2+1):
            row = []
            for y in xrange(0-game.ACTIVE_CHUNK_SIZE/2, game.ACTIVE_CHUNK_SIZE/2+1):
                adjacent_chunk_x = game.player.chunk_x + x
                adjacent_chunk_y = game.player.chunk_y + y
                row.append((adjacent_chunk_x, adjacent_chunk_y))
            adjacent_chunks.append(row)
        return adjacent_chunks

#An object used to create new chunks and unload chunks we no longer need                
class NewActiveChunks:
    def __init__(self):
        self.map = []
        #Preparing the new .map for the NewActiveChunks
        for x in xrange(game.ACTIVE_CHUNK_SIZE):
            row = []
            for y in xrange(game.ACTIVE_CHUNK_SIZE):
                row.append(None)
            self.map.append(row)
        #Set the "ready for unload" flag on all ActiveChunks
        for x in xrange(game.ACTIVE_CHUNK_SIZE):
            for y in xrange(game.ACTIVE_CHUNK_SIZE):
                game.active_chunks.map[x][y].ready_for_unload = True
        #Converting overlapping chunks from old ActiveChunks to NewActiveChunks
        player_active_x, player_active_y = game.to_actv_coords(game.player.x, game.player.y)
        game.force_gui_refresh()
        for x in range (0-game.ACTIVE_CHUNK_SIZE/2, game.ACTIVE_CHUNK_SIZE/2+1):
            for y in xrange(0-game.ACTIVE_CHUNK_SIZE/2, game.ACTIVE_CHUNK_SIZE/2+1):
                if 0 <= player_active_x+x <= game.ACTIVE_CHUNK_SIZE/2+1 and 0 <= player_active_y+y <= game.ACTIVE_CHUNK_SIZE/2+1:
                    game.active_chunks.map[player_active_x+x][player_active_y+y].ready_for_unload=False
                    self.map[x+1][y+1] = game.active_chunks.map[player_active_x+x][player_active_y+y]
                #If this fails check if there's a chunk file in /map/. If there is, load it. Otherwise, create a new chunk.
                else:
                    if os.path.isfile(str(game.MAP_DIRECTORY)+str(x+game.player.chunk_x)+"_"+str(y+game.player.chunk_y)) == True:
                        new_player_chunk_x, new_player_chunk_y = game.to_chunk_coords(game.player.x, game.player.y)
                        file = shelve.open(str(game.MAP_DIRECTORY)+str(x+game.player.chunk_x)+"_"+str(y+game.player.chunk_y), "r")
                        self.map[x+1][y+1] = Chunk(x+new_player_chunk_x, y+new_player_chunk_y, True)
                        self.map[x+1][y+1].chunk = file["chunk"]
                        self.map[x+1][y+1].objects = file["objects"]
                        file.close()
                    else:
                        self.map[x+1][y+1] = Chunk(x+game.player.chunk_x, y+game.player.chunk_y, False)

        #Now unload all the chunks in ActiveChunks that still have their flag set to True
        for x in xrange(game.ACTIVE_CHUNK_SIZE):
            for y in xrange(game.ACTIVE_CHUNK_SIZE):
                if game.active_chunks.map[x][y].ready_for_unload == True:
                    game.active_chunks.map[x][y].save_chunk()
                    game.active_chunks.map[x][y].unload_chunk()
        #Now copy the NewActiveChunks map to ActiveChunks
        game.active_chunks.map = self.map
        
#The game map is divided into chunks which store terrain information, permitting an infinite world
class Chunk:
    #A chunk's objects = [] stores the objects (npcs, items, player) in that chunk
    def __init__(self, chunk_x, chunk_y, loaded):
        self.size = game.CHUNK_SIZE
        self.objects = []
        self.chunk = []
        self.chunk_x = chunk_x
        self.chunk_y = chunk_y
        self.ready_for_unload = False
        if loaded == False:
            for x in xrange(self.size):
                row = []
                for y in xrange(self.size):
                    tileroll = random.randint(1, 1000)
                    if tileroll >= 999:
                        row.append(rtiles.StonyDirt())
                    elif tileroll >= 990:
                        row.append(rtiles.DirtTile())
                    elif tileroll >= 980:
                        row.append(rtiles.TallGrassTile())
                    else:
                        row.append(rtiles.GrassTile())
                self.chunk.append(row)
            self.save_chunk()

    #This will overwrite any other chunks at these coordinates
    def save_chunk(self):
        file = shelve.open(str(game.MAP_DIRECTORY)+str(self.chunk_x)+"_"+str(self.chunk_y), "n")
        file["chunk"] = self.chunk
        file["objects"] = self.objects
        file.close()
    #Removes a chunk from the list of active chunks, but does NOT save it.
    #If we did it right, this should only be called when it would make the reference count for the chunk 0
    def unload_chunk(self):
        for object in self.objects:
            object.remove()
        active_x, active_y = game.abst_actv_chunk_coords(self.chunk_x, self.chunk_y)
        game.active_chunks.map[active_x][active_y].objects = []
        game.active_chunks.map[active_x][active_y] = None
        

#Generic object class (player, monsters, items, etc.) represented by an onscreen character
class Object:
    def __init__(self, x, y, objects):
        self.x = x
        self.y = y
        self.char = "@"
        self.color = libtcod.Color(255,255,255)
        self.name = "Object"
        self.chunk_x, self.chunk.y = game.to_chunk_coords(self.x, self.y)
        active_x, active_y = abst_actv_chunk_coords(self.chunk_x, self.chunk_y)
        game.active_chunks.map[active_x][active_y].objects.append(self)

    #Generic NPC movement
    def move(self, dx, dy):
        chunk_count_x, chunk_count_y, local_x, local_y = game.to_actv_and_local_coords(self.x + dx, self.y + dy)
        if not game.active_chunks.map[chunk_count_x][chunk_count_y].chunk[local_x][local_y].blocked:
            #Don't want NPCS wandering off onto unloaded chunks
            active_chunk_max_x, active_chunk_max_y = chunk_max_dimensions(game.player.chunk_x+1, game.player.chunk_y+1)
            active_chunk_min_x, active_chunk_min_y = chunk_min_dimensions(game.player.chunk_x-1, game.player.chunk_y-1)
            if active_chunk_min_x < self.x + dx < active_chunk_max_x and active_chunk_min_y < self.y + dy < active_chunk_max_y:
                self.x += dx
                self.y += dy
                self.check_chunk()

    #Function for handing objects off to new chunks when they move over chunk boundaries and, for the player, updating active_chunks
    def check_chunk(self):
        # Handoff to new chunk if we cross chunk boundaries
        new_chunk_x, new_chunk_y = game.to_chunk_coords(self.x, self.y)
        old_active_x, old_active_y = game.abst_actv_chunk_coords(game.player.chunk_x, game.player.chunk_y)
        new_active_x, new_active_y = game.abst_actv_chunk_coords(new_chunk_x, new_chunk_y)
        if game.active_chunks.map[new_active_x][new_active_y] != game.active_chunks.map[old_active_x][old_active_y]:
            #Player-only elements for check_chunk()
            if self == game.player:
                #Create and load chunks as appropriate; unload old chunks (see class NewActiveChunks)
                new_active_chunks = NewActiveChunks()
            #Then, pass the object on to the next chunk
            #If the object is the player, it won't be in the same place in active_chunks
            #Hence the for loop shenanigans
            for x in xrange(game.ACTIVE_CHUNK_SIZE):
                for y in xrange(game.ACTIVE_CHUNK_SIZE):
                    if self in game.active_chunks.map[x][y].objects:
                        game.active_chunks.map[x][y].objects.remove(self)
            new_active_x, new_active_y = game.to_actv_coords(self.x, self.y)
            game.active_chunks.map[new_active_x][new_active_y].objects.append(self)
            self.chunk_x, self.chunk_y = new_chunk_x, new_chunk_y

    #Hide the object; draw_object won't draw objects represented by " ".
    def clear(self):
        libtcod.console_put_char(game.con, self.x, self.y, " ", libtcod.BKGND_NONE)

    #Remove references to an object and make it invisible, effectively removing it from the game.
    def remove(self):
        #aka that place in Slice
        self.x = -10000
        self.y = -10000
        self.char = " " #Remember, draw_object() ignores " " characters
        game.active_chunks.map[self.chunk_x][self.chunk_y].objects.remove(self)

class Player(Object):
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.char = "@"
        self.color = libtcod.Color(255,255,255)
        self.name = "Player"
        self.chunk_x, self.chunk_y = game.to_chunk_coords(self.x, self.y)

    def assign_player_to_chunk(self):
        active_x, active_y = game.abst_actv_chunk_coords(self.chunk_x, self.chunk_y)
        game.active_chunks.map[active_x][active_y].objects.append(self)
 
    def move(self, dx, dy):
        chunk_count_x, chunk_count_y, local_x, local_y = game.to_actv_and_local_coords(self.x + dx, self.y + dy)
        if not game.active_chunks.map[chunk_count_x][chunk_count_y].chunk[local_x][local_y].blocked and game.mode == "move":
            self.x += dx
            self.y += dy
            self.check_chunk()
        game.camera.refresh_position()

class Cursor(Object):
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

#Generic testing critter
class Bird(Object):
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.char = "^"
        self.color = libtcod.Color(175,0,0)
        self.wait = 0
        self.speed = game.GAMESPEED * 10
        self.name = "^bird"
        self.chunk_x, self.chunk_y = game.to_chunk_coords(self.x, self.y)
        active_x, active_y = abst_actv_chunk_coords(self.chunk_x, self.chunk_y)
        game.active_chunks.map[self.chunk_x][self.chunk_y].objects.append(self)
    def ai(self):
        if self.wait == 0:
            self.move(random.randint(-1,1), random.randint(-1,1))
            self.wait = self.speed
        if self.wait > 0:
            self.wait -= 1

#Used to keep track of what to render onscreen, and to differentiate the position of the camera from the position of the player, in case we want to move one and not the other
class GameCamera:
    def __init__(self):
        self.x = game.player.x
        self.y = game.player.y
    def refresh_position(self):
        self.x, self.y = game.player.x, game.player.y

game = GameObject()
game.start_game()
