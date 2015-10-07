import kivy
kivy.require('1.0.9')

import sys

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.relativelayout import RelativeLayout
from kivy.properties import ObjectProperty, StringProperty, NumericProperty
from kivy.properties import ReferenceListProperty, BooleanProperty
from kivy.core.window import Window
from kivy.vector import Vector
from kivy.clock import Clock


class Avatar(Widget):
    rect = ObjectProperty(None)
    source = StringProperty('walrus.png')
    level = NumericProperty(0)
    
    speed = 2.2
    velocity_x = NumericProperty(0)
    velocity_y = NumericProperty(0)
    velocity = ReferenceListProperty(velocity_x, velocity_y)

    user_controllable = BooleanProperty(True)


    def onTiles(self):
        """
        Return a set of the tiles this avatar is on.
        """
        return self.parent.tilesOf(self)
        

    def updatePosition(self):
        if self.user_controllable:
            # try x + y
            new_pos = Vector(*self.velocity) + self.pos
            w = Widget(pos=new_pos, size=self.size)
            if self.parent.isPositionAllowed(w):
                self.pos = new_pos
                return

            # try x
            new_pos = Vector(self.velocity[0], 0) + self.pos
            w = Widget(pos=new_pos, size=self.size)
            if self.parent.isPositionAllowed(w):
                self.pos = new_pos
                return

            # try y
            new_pos = Vector(0, self.velocity[1]) + self.pos
            w = Widget(pos=new_pos, size=self.size)
            if self.parent.isPositionAllowed(w):
                self.pos = new_pos
                return


TILE_SIZE = 64


class Tile(Widget):
    """
    I am a tile on which you might be able to walk or not.
    """
    source = StringProperty('dirt_64.png')
    is_open = True


class Area(RelativeLayout):
    """
    I have a set of tiles associated with me.
    """

    def __init__(self, **kwargs):
        super(RelativeLayout, self).__init__(**kwargs)
        self.tiles = {}


    def posToTileLocation(self, pos):
        """
        Given a pixel position, return the r,c of the tile where that is.
        """
        return int(pos[0]) / TILE_SIZE, int(pos[1]) / TILE_SIZE


    def addTile(self, r, c, tile):
        self.tiles[(r,c)] = tile
        self.add_widget(tile)
        tile.pos = (r * tile.size[0], c * tile.size[1])

    def addForeground(self, r, c, tile):
        self.add_widget(tile)
        tile.pos = (r * tile.size[0], c * tile.size[1])

    def placeThing(self, r, c, thing):
        if thing not in self.children:
            self.add_widget(thing)
        thing.pos = (r * TILE_SIZE, c * TILE_SIZE)


    def tilesOf(self, widget):
        """
        Get a list of tiles the widget overlaps (assuming widget is a square)
        """
        bottom_left = self.posToTileLocation((widget.x, widget.y))
        top_right = self.posToTileLocation((widget.right, widget.top))

        for i in xrange(bottom_left[0], top_right[0]+1):
            for j in xrange(bottom_left[1], top_right[1]+1):
                tile = self.tiles.get((i,j), None)
                if tile:
                    yield tile


    def isPositionAllowed(self, widget):
        for tile in self.tilesOf(widget):
            if not tile.is_open:
                return False
        return True
        
AREA_ROWS = 15
AREA_COLS = 10

class GuffGame(Widget):
    avatar = ObjectProperty(None)


    def __init__(self, control_state):
        super(GuffGame, self).__init__()
        self.control_state = control_state
        self.area = Area()
        self.add_widget(self.area)

        for i in xrange(AREA_ROWS):
            for j in xrange(AREA_COLS):
                tile = Tile()
                tile.is_open = not((i == 0) or (i == AREA_ROWS-1) or (j == 0) or (j == AREA_COLS-1))
                if not(tile.is_open):
                    tile.source = 'stone_64.png'
                self.area.addTile(i, j, tile)

        self.avatar = Avatar()
        self.area.placeThing(2, 2, self.avatar)
        self.area.placeThing(5, 5, Tile(source='roses.png'))

    def plantThing(self, source):
        r = self.avatar.pos[0] / TILE_SIZE
        c = self.avatar.pos[1] / TILE_SIZE
        self.area.placeThing(r, c, Tile(source=source))

    def update(self, dt):
        x = 0
        y = 0
        keys = self.control_state.current()
        if 'up' in keys:
            y += self.avatar.speed
        if 'down' in keys:
            y -= self.avatar.speed
        if 'left' in keys:
            x -= self.avatar.speed
        if 'right' in keys:
            x += self.avatar.speed
        if 'x' in keys:
            for tile in self.avatar.onTiles():
                tile.opacity = 0.5
        if 'b' in keys:
            self.plantThing('roses.png')
        if 't' in keys:
            self.plantThing('tree.png')
        if 'w' in keys:
            for tile in self.avatar.onTiles():
                tile.source = 'water1.jpg'
        if 'd' in keys:
            for tile in self.avatar.onTiles():
                tile.source = 'dirt_64.png'
        if 'q' in keys:
            sys.exit(1)
        
        self.avatar.velocity = Vector(x, y)
        self.avatar.updatePosition()



class ControlState(object):

    def __init__(self):
        self.state = {}

    def current(self):
        return self.state.values()

    def down(self, keycode):
        if keycode not in self.state:
            self.state[keycode] = keycode[1]

    def up(self, keycode):
        self.state.pop(keycode)



class GuffApp(App):

    def __init__(self, **kwargs):
        super(GuffApp, self).__init__(**kwargs)
        self.control_state = ControlState()
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(on_key_down=self._on_keyboard_down)
        self._keyboard.bind(on_key_up=self._on_keyboard_up)


    def _keyboard_closed(self):
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard.unbind(on_key_up=self._on_keyboard_up)
        self._keyboard = None


    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        self.control_state.down(keycode)


    def _on_keyboard_up(self, keyboard, keycode):
        self.control_state.up(keycode)


    def build(self):
        game = GuffGame(self.control_state)
        Clock.schedule_interval(game.update, 1.0/60.0)
        return game


if __name__ == '__main__':
    GuffApp().run()
