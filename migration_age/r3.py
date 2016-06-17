import libtcodpy as libtcod
import rtiles
import random

class GameObject:
    def __init__(self):
        #GUI and map variables
        self.SCREEN_WIDTH = 80
        self.SCREEN_HEIGHT = 50
        #MAP_X_SIZE and _Y_SIZE are the size of the map in chunks
        self.MAP_X_SIZE = 200
        self.MAP_Y_SIZE = 400
        self.CHUNK_SIZE = 128
        self.MAP_WIDTH = self.MAP_X_SIZE*self.CHUNK_SIZE
        self.MAP_HEIGHT = self.MAP_Y_SIZE*self.CHUNK_SIZE
        self.CAMERA_WIDTH = 80
        self.CAMERA_HEIGHT = 49
        self.LIMIT_FPS = 20
        self.INFOBAR_HEIGHT = 1
        self.ACTIONPANEL_WIDTH = 15
        self.MENU_WIDTH = 20
        self.GAME_FONT = 'arial10x10.png'
        #We begin in the center of this chunk
        self.PLAYER_START_X = 100
        self.PLAYER_START_Y = 200

        #Variable controlling frame interval for certain events
        self.GAMESPEED = 5

        #Minimum number of frames between player movements/actions
        self.MAX_MOVESPEED = self.GAMESPEED/2

        libtcod.console_set_custom_font(self.GAME_FONT, libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD)
        libtcod.console_init_root(self.SCREEN_WIDTH, self.SCREEN_HEIGHT, 'python/libtcod tutorial', False)
        libtcod.sys_set_fps(self.LIMIT_FPS)
        self.con = libtcod.console_new(self.SCREEN_WIDTH, self.SCREEN_HEIGHT)

        #Game state and GUI control variables
        self.show_menu = False
        self.mode = "move"
        self.cursor = None
        self.time = "free"
        self.player_wait = 0

        self.npcs = []
        self.player = None
        self.camera = None
        self.objects = []
        self.map = None

        self.infobar = libtcod.console_new(self.SCREEN_WIDTH, self.INFOBAR_HEIGHT)
        self.menu = libtcod.console_new(self.MENU_WIDTH, self.SCREEN_HEIGHT)

    def start_game(self):
        self.make_map()
        self.make_chunks_near_start()
        self.player = Player(self.CHUNK_SIZE*self.PLAYER_START_X + self.CHUNK_SIZE/2, self.CHUNK_SIZE*self.PLAYER_START_Y + self.CHUNK_SIZE/2)
        #self.birds = [Bird(self.MAP_WIDTH/2, self.MAP_HEIGHT/2), Bird(self.MAP_WIDTH/2, self.MAP_HEIGHT/2), Bird(self.MAP_WIDTH/2, self.MAP_HEIGHT/2), Bird(self.MAP_WIDTH/2, self.MAP_HEIGHT/2)]
        self.camera = game_camera()


        while not libtcod.console_is_window_closed():
 
            #render the screen
            self.render_all()
 
            libtcod.console_flush()
 
            #erase all objects at their old locations, before they move
            for object in self.objects:
                object.clear()
 
            #handle keys and exit game if needed
            exit = game.handle_keys()
            if exit:
                break

    def make_map(self):
        self.map = GameMap(game.MAP_X_SIZE, game.MAP_Y_SIZE)

    def make_chunks_near_start(self):
        self.map.map[self.PLAYER_START_X][self.PLAYER_START_Y] = Chunk()
        print("Starting chunk prepared: " + str(self.PLAYER_START_X)+","+str(self.PLAYER_START_Y))
        for x in range(-1, 2):
            for y in range(-1, 2):
                if x == 0 and y == 0:
                    pass
                else:
                    self.map.map[x+self.PLAYER_START_X][y+self.PLAYER_START_Y] = Chunk()
                    print("Chunk "+str(self.PLAYER_START_X+x)+","+str(self.PLAYER_START_Y+y)+" prepared")
        

    def to_camera_coordinates(self, x, y):
        (x, y) = (x - self.camera.x + self.CAMERA_WIDTH/2, y - self.camera.y + self.CAMERA_HEIGHT/2)
        if (x < 0 or y < 0 or x >= self.CAMERA_WIDTH or y >= self.CAMERA_HEIGHT):
            return (None, None)
        return (x, y)

    def refresh_infobar(self, infobar):
        libtcod.console_clear(infobar)
        infobar_text = ""
        if self.mode == "move":
            chunk_count_x, chunk_count_y, local_x, local_y = self.to_chunk_and_local_coords(self.player.x, self.player.y)
            infobar_text = self.map.map[chunk_count_x][chunk_count_y].chunk[local_x][local_y].name + " "
            for mob in self.active_objects:
                if mob.x == self.player.x and mob.y == self.player.y and hasattr(mob, "name") == True:
                    if mob.name != "Player":
                        infobar_text = infobar_text + mob.name + " "
            libtcod.console_print(infobar, 0, 0, infobar_text)
        if self.mode == "look":
            chunk_count_x, chunk_count_y, local_x, local_y = self.to_chunk_and_local_coords(self.cursor.x, self.cursor.y)
            infobar_text = self.map.map[chunk_count_x][chunk_count_y].chunk[local_x][local_y].name + " "
            for mob in self.active_objects:
                if mob.x == self.cursor.x and mob.y == self.cursor.y and hasattr(mob, "name") == True:
                    infobar_text = infobar_text + mob.name + " "
            libtcod.console_print(infobar, 0, 0, infobar_text)

    def refresh_menu(self, menu):
        libtcod.console_clear(menu)
        libtcod.console_print(menu, 1, 1, "Migration Age test")
        libtcod.console_print(menu, 1, 2, "l: hide this panel")
        libtcod.console_print(menu, 1, 3, "k: look mode")
        libtcod.console_print(menu, 1, 4, "arrow keys: move")
        libtcod.console_print(menu, 1, 5, "-/+: adjust speed")
        libtcod.console_print(menu, 1, 6, "  Current speed:" + str(self.GAMESPEED))
        libtcod.console_print(menu, 1, 7, "esc: quit")
        libtcod.console_print(menu, 1, 15, "Chunks allocated: ")
        libtcod.console_print(menu, 8, 16, str(len(self.map.map)*len(self.map.map[0]) ))
        libtcod.console_print(menu, 1, 17, "Total map size: ")
        libtcod.console_print(menu, 8, 18, str(self.MAP_WIDTH) + "x" + str(self.MAP_HEIGHT))

    def draw_object(self, obj):
        (pos_x, pos_y) = self.to_camera_coordinates(obj.x, obj.y)
        if pos_x is not None and obj.char != " ":
            libtcod.console_set_default_foreground(self.con, obj.color)
            libtcod.console_put_char(self.con, pos_x, pos_y, obj.char, libtcod.BKGND_NONE)
        

    def render_all(self):
        libtcod.console_clear(self.con)

        for y in range(self.CAMERA_HEIGHT):
            for x in range(self.CAMERA_WIDTH):
                #First, get the absolute map coordinates of whatever's in view
                (map_x, map_y) = (self.camera.x + x - self.CAMERA_WIDTH/2, self.camera.y + y - self.CAMERA_HEIGHT/2)
                #Then, get which chunk it's on, and where on that chunk it is
                chunk_count_x, chunk_count_y, local_x, local_y = self.to_chunk_and_local_coords(map_x, map_y)
                #Now, render the appropriate char based on the coords
                libtcod.console_put_char(self.con, x, y, self.map.map[chunk_count_x][chunk_count_y].chunk[local_x][local_y].char, libtcod.BKGND_NONE)
                libtcod.console_set_char_foreground(self.con, x, y, self.map.map[chunk_count_x][chunk_count_y].chunk[local_x][local_y].color)
                    
        #Draw all objects in range of the player to be active
        self.active_objects = self.get_active_objects()
        for object in self.active_objects:
            self.draw_object(object)

        if self.cursor!= None:
            self.draw_object(self.cursor)
     
        #blit the contents of "con" to the root console
        libtcod.console_blit(self.con, 0, 0, self.SCREEN_WIDTH, self.SCREEN_HEIGHT, 0, 0, 0)

        #blit the infobar to the root console
        self.refresh_infobar(self.infobar)
        libtcod.console_blit(self.infobar, 0, 0, self.SCREEN_WIDTH, self.SCREEN_HEIGHT, 0, 0, self.SCREEN_HEIGHT - 1)

        #if we're showing the right-side menu, show it
        if self.show_menu == True:
            self.refresh_menu(self.menu)
            libtcod.console_blit(self.menu, 0, 0, self.SCREEN_WIDTH, self.SCREEN_HEIGHT, 0, self.SCREEN_WIDTH - self.MENU_WIDTH, 0)

    def handle_keys(self):

        for creature in self.active_objects:
            if hasattr(creature, "ai") == True:
                creature.ai()

        if self.player_wait > 0:
            self.player_wait -= 1
        
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

     
        #movement keys
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

    def get_active_objects(self):
        active_objects = []
        player_chunk_x, player_chunk_y = self.to_chunk_coords(self.player.x, self.player.y)
        adjacent_chunks = self.get_adjacent_chunks(player_chunk_x, player_chunk_y)
        for x in adjacent_chunks:
            for y in x:
               active_objects.extend(y.objects)
        return active_objects
        

    def to_abs_coords(self, chunk, chunk_x, chunk_y):
        map_x = chunk_x + game.CHUNK_SIZE*chunk.chunk_coords[0]
        map_y = chunk_y + game.CHUNK_SIZE*chunk.chunk_coords[1]
        return (map_x, map_y)
    def to_local_coords(self, map_x, map_y):
        chunk_x = map_x % CHUNK_SIZE
        chunk_y = map_y % CHUNK_SIZE
        return (chunk_x, chunk_y)
    def to_chunk_and_local_coords(self, map_x, map_y):
        chunk_count_x = map_x/game.CHUNK_SIZE
        chunk_count_y = map_y/game.CHUNK_SIZE
        local_x = map_x % game.CHUNK_SIZE
        local_y = map_y % game.CHUNK_SIZE
        return (chunk_count_x, chunk_count_y, local_x, local_y)
    def to_chunk_coords(self, map_x, map_y):
        chunk_count_x = map_x/game.CHUNK_SIZE
        chunk_count_y = map_y/game.CHUNK_SIZE
        return (chunk_count_x, chunk_count_y)
    #The highest x and y values of the chunk
    def chunk_max_dimensions(self, chunk_x, chunk_y):
        chunk_max_x = (chunk_count_x+1)*game.CHUNK_SIZE-1
        chunk_max_y = (chunk_count_y+1)*game.CHUNK_SIZE-1
        return (chunk_max_x, chunk_max_y)
    #The lowest x and y values of the chunk
    def chunk_min_dimensions(self, chunk_x, chunk_y):
        chunk_min_x = chunk_count_x*game.CHUNK_SIZE+1
        chunk_min_y = chunk_count_y*game.CHUNK_SIZE+1
        return (chunk_min_x, chunk_min_y)

    #Returns the eight chunks around the specified chunks and a None for the middle chunk
    def get_adjacent_chunks(self, chunk_x, chunk_y):
        adjacent_chunks = []
        for x in range(-1, 2):
            row = []
            for y in range(-1, 2):
                if 0 <= chunk_x + x <= game.MAP_X_SIZE and 0 <= chunk_y + y <= game.MAP_Y_SIZE:
                    try:
                        row.append(self.map.map[chunk_x+x][chunk_y+y])
                    except IndexError:
                        print("Run away from the light, Beverly!")
            adjacent_chunks.append(row)
        return adjacent_chunks

class GameMap:
    def __init__(self, x_size, y_size):
        self.map = []
        for x in range(x_size):
            row = []
            for y in range(y_size):
                chunk_coords = [x,y]
                row.append(None)
                #row.append(Chunk(chunk_coords))
                print("Chunk " + str(x) + "," + str(y) + " allocated")
            self.map.append(row)
            print("Map row " + str(y) + " allocated")


class Chunk:
    #A chunk's objects = [] stores the objects (npcs, items, player) in that chunk
    def __init__(self):
        self.size = game.CHUNK_SIZE
        self.objects = []
        self.chunk = []
        for x in range(self.size):
            row = []
            for y in range(self.size):
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

class Object:
    #Generic object class (player, monsters, items, etc.) represented by an onscreen character
    def __init__(self, x, y, objects):
        self.x = x
        self.y = y
        self.char = "@"
        self.color = libtcod.Color(255,255,255)
        self.name = "Object"
        self.chunk_x, self.chunk.y = game.to_chunk_coords(self.x, self.y)
        game.map.map[self.chunk_x][self.chunk_y].objects.append(self)

    def move(self, dx, dy):
        if 0 < self.x + dx < game.MAP_WIDTH - 1 and 0 < self.y + dy < game.MAP_HEIGHT - 1:
            chunk_count_x, chunk_count_y, local_x, local_y = game.to_chunk_and_local_coords(self.x + dx, self.y + dy)
            if not game.map.map[chunk_count_x][chunk_count_y].chunk[local_x][local_y].blocked:
                #Don't want NPCS wandering off onto unloaded chunks
                active_chunk_max_x, active_chunk_max_y = chunk_max_dimensions(game.player.chunk_x+1, game.player.chunk_y+1)
                active_chunk_min_x, active_chunk_min_y = chunk_min_dimensions(game.player.chunk_x-1, game.player.chunk_y-1)
                if active_chunk_min_x < self.x + dx < active_chunk_max_x and active_chunk_min_y < self.y + dy < active_chunk_max_y:
                    self.x += dx
                    self.y += dy
                    self.check_chunk()

    def check_chunk(self):
        # Handoff to new chunk if we cross chunk boundaries
        new_chunk_x, new_chunk_y = game.to_chunk_coords(self.x, self.y)
        if game.map.map[self.chunk_x][self.chunk_y] != game.map.map[new_chunk_x][new_chunk_y]:
            #Player-only elements for check_chunk()
            if self == game.player:
                #First, check if new chunks need to be generated to extend the world
                for x in range(-1, 2):
                    for y in range(-1, 2):
                        if 0 <= new_chunk_x+x <= game.MAP_X_SIZE and 0 <= new_chunk_y+y <= game.MAP_Y_SIZE: 
                            try:                            
                                if game.map.map[new_chunk_x+x][new_chunk_y+y] == None:
                                    print("Making a new chunk...")
                                    game.map.map[new_chunk_x+x][new_chunk_y+y] = Chunk()
                                    print("Chunk complete")
                            except IndexError:
                                print("It's that weird barrier at the end of the galaxy again")
                        else:
                            pass
                #Check which chunks are now inactive (will be used for saving and unloading these chunks)
                for x in range(-2, 3):
                    for y in range(-2, 3):
                        if 0 <= new_chunk_x+x <= game.MAP_X_SIZE and 0 <= new_chunk_y+y <= game.MAP_Y_SIZE: 
                            try:                            
                                if game.map.map[new_chunk_x+x][new_chunk_y+y] != "saved":
                                    #This is where I would put my function for saving chunks... IF I HAD ONE!
                                    pass
                            except IndexError:
                                print("I knew I shouldn't have followed the Ellimist into the Time Vortex.")
                        else:
                            pass
            #Then, pass the player on to the next chunk
            game.map.map[self.chunk_x][self.chunk_y].objects.remove(self)
            self.chunk_x, self.chunk_y = new_chunk_x, new_chunk_y
            game.map.map[self.chunk_x][self.chunk_y].objects.append(self)
            print("Chunk handoff successful")

    def clear(self):
        #erase the character that represents this object
        libtcod.console_put_char(game.con, self.x, self.y, " ", libtcod.BKGND_NONE)

    def remove(self):
        #Remove this object from the list of active objects, make it invisible, and move it off the map.
        self.x = -1
        self.y = -1
        self.char = " " #Remember, draw_object() ignores " " characters
        game.map.map[self.chunk_x][self.chunk_y].objects.remove(self)

class Player(Object):
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.char = "@"
        self.color = libtcod.Color(255,255,255)
        self.name = "Player"
        self.chunk_x, self.chunk_y = game.to_chunk_coords(self.x, self.y)
        print(self.x, self.y, self.chunk_x, self.chunk_y)
        game.map.map[self.chunk_x][self.chunk_y].objects.append(self)
 
    def move(self, dx, dy):
        if 0 < self.x + dx < game.MAP_WIDTH - 1 and 0 < self.y + dy < game.MAP_HEIGHT - 1:
            chunk_count_x, chunk_count_y, local_x, local_y = game.to_chunk_and_local_coords(self.x + dx, self.y + dy)
            if not game.map.map[chunk_count_x][chunk_count_y].chunk[local_x][local_y].blocked and game.mode == "move":
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
        game.map.map[self.chunk_x][self.chunk_y].objects.append(self)
    def ai(self):
        if self.wait == 0:
            self.move(random.randint(-1,1), random.randint(-1,1))
            self.wait = self.speed
        if self.wait > 0:
            self.wait -= 1

class game_camera:
    def __init__(self):
        self.x = game.player.x
        self.y = game.player.y
    def refresh_position(self):
        if game.CAMERA_WIDTH/2 < game.player.x < game.MAP_WIDTH - game.CAMERA_WIDTH/2:
            self.x = game.player.x
        if game.CAMERA_HEIGHT/2 < game.player.y < game.MAP_HEIGHT - game.CAMERA_HEIGHT/2:
            self.y = game.player.y

game = GameObject()
game.start_game()
