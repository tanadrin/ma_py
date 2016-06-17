import libtcodpy as libtcod
import random

class Object:
    #Generic object class (player, monsters, items, etc.) represented by an onscreen character
    def __init__(self, x, y, objects):
        self.x = x
        self.y = y
        self.char = "@"
        self.color = libtcod.Color(255,255,255)
        self.name = "Object"
        objects.append(self)

    def move(self, dx, dy):
        if 0 < self.x + dx < game.MAP_WIDTH - 1 and 0 < self.y + dy < game.MAP_HEIGHT - 1:
            if not game.map[self.x + dx][self.y + dy].blocked:
                self.x += dx
                self.y += dy

    def draw(self):
        #set the color and then draw the character that represents this object at its position
        (pos_x, pos_y) = game.to_camera_coordinates(self.x, self.y)
        if pos_x is not None and self.char != " ":
            libtcod.console_set_default_foreground(game.con, self.color)
            libtcod.console_put_char(game.con, pos_x, pos_y, self.char, libtcod.BKGND_NONE)

    def clear(self):
        #erase the character that represents this object
        libtcod.console_put_char(game.con, self.x, self.y, ' ', libtcod.BKGND_NONE)

class Bird(Object):
    def __init__(self, x, y, objects):
        self.x = x
        self.y = y
        self.char = "^"
        self.color = libtcod.Color(175,0,0)
        self.wait = 0
        self.speed = 50
        objects.append(self)
        self.name = "^bird"
    def ai(self):
        if self.wait == 0:
            self.move(random.randint(-1,1), random.randint(-1,1))
            self.wait = self.speed
        if self.wait > 0:
            self.wait -= 1
