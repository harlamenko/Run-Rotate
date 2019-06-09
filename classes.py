import pygame
import cv2
import numpy as np
from tkinter import Tk, Scale, HORIZONTAL
from threading import Thread
import time
from math import fabs, cos, sin, pi, atan


class Group(object):
    """
       group class allows keep objects which belong to some group
       for example: moving sprites, danger objects etc
    """
    def __init__(self):
        self._list = set()

    def get(self):
        return self._list

    def add(self, *sprites, t=False):
        """Add objects to this group. 't' uses when we give tuple of objects"""
        if t: 
            self._list = self._list ^ set(t)

            for obj in t:
                obj.add_container(self)
        else:
            self._list.update(sprites)
            
            for obj in sprites:
                obj.add_container(self)

    def remove(self, sprite):
        self._list = self._list^{sprite}

    def draw(self, place):
        for sprite in self._list:
            place.blit(sprite.get_image(), sprite.get_coords())

    def update(self):
        for sprite in self._list:
            sprite.update()


class Object():
    def __init__(self, size, coords, image, danger):
        super(Object, self).__init__()
        self._x = coords[0]
        self._y = coords[1]
        self._size = size
        self._half_size = {'x': self._size[0]//2, 'y': self._size[1]//2}
        self._center = {'x': self._x + self._half_size['x'], 'y': self._y + self._half_size['y']}
        self._on_floor = False
        self._image = pygame.transform.scale(image, self._size)
        self._danger = danger
        self._is_dead = False
        self._containers = []
                
    def add_container(self, container):
        self._containers.append(container)

    def on_floor(self, boool):
        self._on_floor = boool
    
    def get_center(self):
        self._center = {'x': self._x + self._half_size['x'], 'y': self._y + self._half_size['y']}
        return self._center

    def get_half_size(self):
        return self._half_size

    def get_coords(self):
        return self._x, self._y

    def set_coords(self, coords):
        self._x, self._y = coords
        self._center = {'x': self._x + self._half_size['x'], 'y': self._y + self._half_size['y']}

    def set_image(self, image):
        self._image = image

    def get_image(self):
        return self._image

    def check_danger(self):
        return self._danger

    def is_dead(self):
        return self._is_dead

    def update(self):
        pass

class Static(Object):
    """This is a construction that describes a static object"""
    def __init__(self, size, coords, image, danger):
        super(Static, self).__init__(size, coords, image, danger)


class Dynamic(Object):
    """This is a constuction that describes a dynamic object"""
    def __init__(self, xspeed, yspeed, size, coords, image, danger):
        super(Dynamic, self).__init__(size, coords, image, danger)
        self._prev_x = self._x 
        self._prev_y = self._y 
        self._can_be = {'left': False, 'right': False, 'down':False, 'up':False}
        self._ground = self._center['y']
        self._gravity = 0.4
        self._YSPEED = yspeed
        self._xspeed = xspeed
        self._yspeed = yspeed
        self._on_portal = False

    def go(self, side, boool):
        self._can_be[side] = boool

    def die(self):
        for container in self._containers:
            container.remove(self)
            
    def check_barrier(self, sprite):
        if fabs(self.get_center()['x'] - sprite.get_center()['x']) < (self.get_half_size()['x'] + sprite.get_half_size()['x'])\
        and fabs(self.get_center()['y'] - sprite.get_center()['y']) < (self.get_half_size()['y'] + sprite.get_half_size()['y']):
            return True
        else: 
            return False

    def on_portal(self):
        """
            checks the background object, and if it's a portal, 
            it moves the dynamic object onto another portal
        """
        for sprite in all_sprites.get():
            if sprite == self: continue
            elif sprite.__class__ == Portal:
                if self.check_barrier(sprite):
                    if not self._on_portal:
                        self._on_portal = True
                        self.set_coords(sprite.get_twin_coords())

                elif fabs(self.get_center()['x'] - sprite.get_center()['x']) < (self.get_half_size()['x'] + sprite.get_half_size()['x'])\
                and fabs(self.get_center()['y'] - sprite.get_center()['y']) > (self.get_half_size()['y'] + sprite.get_half_size()['y']):
                    self._on_portal = False

    def in_danger(self):
        """
            checks the background object, and if it is danger, 
            it kills dynamic object
        """
        for sprite in all_sprites.get():
            if sprite == self: continue
            if self.check_barrier(sprite) and sprite.check_danger():
                self._is_dead = True
                self.die()

    def update(self):
        self._prev_y = self._y
        self._prev_x = self._x

        if self._can_be['right'] and not self._can_be['up'] :
            self._x += self._xspeed

            for sprite in all_without_bg:
                if sprite == self: continue
                if self.check_barrier(sprite): 
                    self._x = self._prev_x
                    break

        if self._can_be['left'] and not self._can_be['up'] :
            self._x -= self._xspeed

            for sprite in all_without_bg:
                if sprite == self: continue
                if self.check_barrier(sprite): 
                    self._x = self._prev_x
                    break

        if self._can_be['up']:  
            self._y -= self._yspeed
            self._yspeed -= self._gravity

            for sprite in all_without_bg:
                if sprite == self: continue
                if self.check_barrier(sprite): 
                    self._can_be['up'] = False
                    self._yspeed = 0
                    self._y = self._prev_y
                    break

            if self._can_be['left']:
                self._x -= self._xspeed//1.5

                for sprite in all_without_bg:
                    if sprite == self: continue
                    if self.check_barrier(sprite): 
                        self._can_be['left'] = False
                        self._x = self._prev_x

            elif self._can_be['right']:
                self._x += self._xspeed//1.5

                for sprite in all_without_bg:
                    if sprite == self: continue
                    if self.check_barrier(sprite): 
                        self._can_be['right'] = False
                        self._x = self._prev_x
            
        elif self._can_be['down']:
            self._y += self._yspeed
            self._yspeed += self._gravity

            for sprite in all_without_bg:
                if sprite == self:continue
                if self.check_barrier(sprite): 
                    self._on_floor = True
                    self._can_be['down'] = False
                    self._y = self._prev_y
                    self._ground = self.get_center()['y']
                    break

        if not self._can_be['down'] and not self._can_be['up']:
            for sprite in all_without_bg:
                if sprite == self:continue
                if fabs(self.get_center()['y'] - sprite.get_center()['y']) > (self.get_half_size()['y'] + sprite.get_half_size()['y'])\
                and fabs(self.get_center()['x'] - sprite.get_center()['x']) < (self.get_half_size()['x']+ sprite.get_half_size()['x']):
                    self._yspeed = self._YSPEED
                    self._can_be['down'] = True

        if self._yspeed > self._YSPEED: self._yspeed = self._YSPEED

        self.get_center()
        self.on_portal()
        self.in_danger()


class Skull(Static):
    def __init__(self, size, coords, image, danger=True):
        super(Skull, self).__init__(size, coords, image, danger)


class Block(Static):
    def __init__(self,size, coords, image, danger=False):
        super(Block, self).__init__(size, coords, image, danger)
               

class Portal(Static):
    def __init__(self,size, portal_id, twin_coords, coords, image, danger=False):
        super(Portal, self).__init__(size, coords, image, danger)
        self._portal_id = portal_id
        self._twin_coords = twin_coords 

    def get_id(self):
        return self._portal_id

    def get_twin_coords(self):
        return self._twin_coords

    def set_twin_coords(self, twin_coords):
        self._twin_coords = twin_coords
    

class Prize(Block):
    def __init__(self, size, coords, image, danger=False):
        super(Prize, self).__init__(size, coords, image, danger)


class Player(Dynamic):
    def __init__(self,xspeed, yspeed, size, image, coords=(0,0), danger=False):
        super(Player, self).__init__(xspeed, yspeed, size, coords, image, danger)
        self._go_right_img = pygame.image.load('go_right.png')
        self._go_right_img= pygame.transform.scale(self._go_right_img, size)
        self._go_left_img = pygame.image.load('go_left.png')
        self._go_left_img = pygame.transform.scale(self._go_left_img, size)
        self._jump_img = pygame.image.load('jump.png')
        self._jump_img = pygame.transform.scale(self._jump_img, size)
        self._fall_img = pygame.image.load('fall.png')
        self._fall_img = pygame.transform.scale(self._fall_img, size)
        self._stay_img = self._image
        self._on_prize = False

    def check_on_prize(self):
        """checks the background object, and if player on door - level complete"""
        for sprite in all_sprites.get():
            if sprite == self: continue
            if sprite.__class__ == Prize\
            and fabs(self.get_center()['x'] - sprite.get_center()['x']) < (self.get_half_size()['x'] + sprite.get_half_size()['x'])//2\
            and fabs(self.get_center()['y'] - sprite.get_center()['y']) < (self.get_half_size()['y'] + sprite.get_half_size()['y']):
                self._on_prize = True

    def on_prize(self):
        return self._on_prize

    def update(self):
        if self._can_be['right'] and not self._can_be['up']:
            self._image = self._go_right_img

        elif self._can_be['left'] and not self._can_be['up']:
            self._image = self._go_left_img

        elif self._yspeed < 0 or not self._on_floor:
            self._image = self._fall_img

        elif self._can_be['up'] :
            self._image = self._jump_img

        else:
            self._image = self._stay_img
        
        super(Player, self).update()
        self.check_on_prize()


class Box(Dynamic):
    def __init__(self,xspeed, yspeed, size,image,coords, danger=False):
        super(Box, self).__init__(xspeed, yspeed, size, coords, image, danger)

class Cv(object):
    def __init__(self):
        self._hmin = 0
        self._smin = 85
        self._vmin = 141
        self._hmax = 15
        self._smax = 255
        self._vmax = 255

    def show_control_panel(self):
        """function realize sliders for setting HSV"""
        root=Tk()
        s1 = Scale(root,length=600,label='Hmin', from_=0, to=360,orient=HORIZONTAL, command=lambda v: setattr(self, '_hmin', int(v)))
        s1.set(self._hmin)
        s4 = Scale(root,length=600,label='Hmax', from_=0, to=360,orient=HORIZONTAL, command=lambda v: setattr(self, '_hmax', int(v)))
        s4.set(self._hmax)
        s2 = Scale(root,length=600,label='Smin', from_=0, to=255, orient=HORIZONTAL, command=lambda v: setattr(self, '_smin', int(v)))
        s2.set(self._smin)
        s5 = Scale(root,length=600,label='Smax', from_=0, to=255, orient=HORIZONTAL, command=lambda v: setattr(self, '_smax', int(v)))
        s5.set(self._smax)
        s3 = Scale(root,length=600,label='Vmin', from_=0, to=255, orient=HORIZONTAL, command=lambda v: setattr(self, '_vmin', int(v)))
        s3.set(self._vmin)
        s6 = Scale(root,length=600,label='Vmax', from_=0, to=255, orient=HORIZONTAL, command=lambda v: setattr(self, '_vmax', int(v)))
        s6.set(self._vmax)
        s1.pack()
        s2.pack()
        s3.pack()
        s4.pack()
        s5.pack()
        s6.pack()
        root.mainloop()

    def show_video_capture(self,DISPLAY_WIDTH, DISPLAY_HEIGHT):
        global aim_x, aim_y, visio_control, quit_cv
        cap = cv2.VideoCapture(0)

        while True:
            _, frame = cap.read()
            frame_blur = cv2.GaussianBlur(frame, (15,15), 0)
            hsv = cv2.cvtColor(frame_blur, cv2.COLOR_BGR2HSV)
            lower_color = np.array([self._hmin,self._smin,self._vmin])
            upper_color = np.array([self._hmax,self._smax,self._vmax])
            mask = cv2.inRange(hsv, lower_color, upper_color)
            res = cv2.bitwise_and(frame, frame, mask=mask)
            contours, image = cv2.findContours(mask.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)

            if len(contours):
                visio_control = True
                cnt = max(contours, key = cv2.contourArea)
                x, y, w, h = cv2.boundingRect(cnt)

                if x > DISPLAY_WIDTH//2:
                    aim_x = DISPLAY_WIDTH//2 - (x-DISPLAY_WIDTH//2) + w//2
                else:
                    aim_x = DISPLAY_WIDTH//2 + (DISPLAY_WIDTH//2-x) + w//2

                aim_y = y+h//2
                get_center = (x+w//2, y+h//2)
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 5)
                cv2.rectangle(frame, get_center, get_center, (255, 0, 0), 10)
                cv2.imshow('frame',frame)
                # cv2.imshow('mask',mask)
                # cv2.imshow('res',res)                

            else:
                visio_control = False
                cv2.imshow('frame',frame)
                # cv2.imshow('mask',mask)
                # cv2.imshow('res',res)

            k = cv2.waitKey(5) & 0xFF
            if k == 27:
                break

            if quit_cv:
                break
        cv2.destroyAllWindows()
        cap.release()


class Game(object):
    """main object which contain all functions for game interaction"""
    def __init__(self):
        self._DISPLAY_WIDTH = self._DISPLAY_HEIGHT = 700
        self._ADDITIONAL_WIDTH = 50
        self._backgroun_color = 45,58,103
        self._green = 0, 255, 0
        self._red = 255, 0, 0
        self._FPS = 60
        pygame.init()
        self._screen = pygame.display.set_mode((self._DISPLAY_WIDTH+self._ADDITIONAL_WIDTH, self._DISPLAY_HEIGHT))
        pygame.display.set_caption('Run - rotate')
        icon = pygame.image.load("icon.png")
        icon.set_colorkey(self._backgroun_color)
        pygame.display.set_icon(icon)
        self._clock = pygame.time.Clock()
        self._player_img = pygame.image.load('player.png')
        self._block_img = pygame.image.load('block.jpg')
        self._frame_img = pygame.image.load('frame.jpg')
        self._box_img = pygame.image.load('box.jpg')
        self._exit_img = pygame.image.load('exit.jpg')
        self._portal_img = pygame.image.load('portal.jpg')
        self._skull_img = pygame.image.load('skull.jpg')
        self._aim_img = pygame.image.load('aim.png')
        self._win_img = pygame.image.load('pobeda.jpg')
        self._death_img = pygame.image.load('smert.jpg')
        self._aim_img = pygame.transform.scale(self._aim_img, (40,40))
        self._win_img = pygame.transform.scale(self._win_img, (self._DISPLAY_WIDTH+self._ADDITIONAL_WIDTH, self._DISPLAY_HEIGHT))
        self._death_img = pygame.transform.scale(self._death_img, (self._DISPLAY_WIDTH+self._ADDITIONAL_WIDTH, self._DISPLAY_HEIGHT))
        self._pause = Button((self._DISPLAY_WIDTH+self._ADDITIONAL_WIDTH-50, 0), 'pause.png', 'pause.png', (50, 50))

    def quitgame(self):
        global quit_cv
        quit_cv = True

        pygame.quit()
        quit()

    def smooth_movement(self, arr):
        temp_container = {}

        for i in range(len(arr)):
            for j in range(len(arr[0])):
                obj = arr[i][j]
                if obj != '':
                    obj.on_floor(False)
                    x2, y2 = j*self._CELL_SIZE, i*self._CELL_SIZE
                    temp_container[obj] = x2, y2

        for i in range(100):
            t = i/100
            for obj in temp_container:
                x0,y0 = obj.get_coords()
                x2,y2 = temp_container[obj]
                x1 = (1-t)*x0+t*x2
                y1 = (1-t)*y0+t*y2
                obj.set_coords((x1,y1))
        
            self._screen.fill(self._backgroun_color)
            all_sprites.draw(self._screen)
            self._screen.blit(self._pause.get_image(), self._pause.get_coords())
            pygame.display.update()

        try:
            self._portal0.set_twin_coords(self._portal1.get_coords())
            self._portal1.set_twin_coords(self._portal0.get_coords())
        except: pass
    
    def rotate_grid(self,side,grid):
        temp = [['' for j in range(self._DISPLAY_HEIGHT//self._CELL_SIZE)]\
               for i in range(self._DISPLAY_HEIGHT//self._CELL_SIZE)]
        k=0

        if side == "right":
            for j in range(len(grid[0])-1, -1, -1): 
                for i in range(len(grid)):
                    temp[i][k] = grid[j][i]
                k+=1
        
        elif side == "left":
            for j in range(len(grid[0])-1, -1, -1): 
                for i in range(len(grid)):
                    temp[k][i] = grid[i][j]
                k+=1

        self.smooth_movement(temp)
        
    def show_message_of_win(self):
        self._screen.blit(self._win_img, (0,0))
        pygame.display.update()
        time.sleep(2)

    def show_message_of_death(self):
        self._screen.blit(self._death_img, (0,0))
        pygame.display.update()
        time.sleep(2)

    def round_to_cell_size(self, coord):
        if coord % self._CELL_SIZE >= self._CELL_SIZE//2:
            coord += self._CELL_SIZE - coord % self._CELL_SIZE
            return coord

        else:
            coord = coord - coord % self._CELL_SIZE
            return coord

    def place_to_grid(self, group):
        grid = [['' for j in range(self._DISPLAY_HEIGHT//self._CELL_SIZE)]\
                              for i in range(self._DISPLAY_HEIGHT//self._CELL_SIZE)]
        for el in group.get():
            x = self.round_to_cell_size(el.get_coords()[0])
            y = self.round_to_cell_size(el.get_coords()[1])
            el.set_coords((x,y))
            j,i = int(x//self._CELL_SIZE), int(y//self._CELL_SIZE)
            grid[i][j] = el

        return grid
       
    def main(self):
        global visio, aim_x, aim_y, visio_control, quit_cv
        visio_control = False
        quit_cv = False
        aim_x = aim_y = 0
        visio = Cv()

        while True:
            menu = Menu()
            menu.start()
            lvl1 = Level(1)
            lvl1.start()
            lvl2 = Level(2)
            lvl2.start()
            lvl3 = Level(3)
            lvl3.start()

class Button(pygame.sprite.Sprite):
    def __init__(self, coords, image, image_press, size):
        super(Button, self).__init__()
        self._size = {'x': size[0], 'y': size[1]}
        self._x, self._y = coords
        self._rect = {'left': self._x, 'top': self._y, 'right': self._x + self._size['x'], 'bottom': self._y + self._size['y']}
        self._image = pygame.image.load(image)
        self._image_press = pygame.image.load(image_press)
        self._image = pygame.transform.scale(self._image, size)
        self._image_press = pygame.transform.scale(self._image_press, size)
        self._current_img = self._image
        self._pressed = False

    def get_image(self):
        return self._current_img

    def get_coords(self):
        return self._x, self._y

    def add_container(self, obj):
        pass

    def press(self, boool=False):
        self._pressed = boool

        if self._pressed:
            self._current_img = self._image_press

        else:
            self._current_img = self._image


    def is_aim(self, coords):
        if self._rect['left'] < coords[0] < self._rect['right']\
        and self._rect['top'] < coords[1] < self._rect['bottom']:
            return True
        return False


class Menu(Game):
    def __init__(self):
        super(Menu, self).__init__()
        self._menu_play = Button((200+self._ADDITIONAL_WIDTH//2,110), 'menu_game.png', 'menu_game_press.png', (300,100))
        self._menu_options = Button((200+self._ADDITIONAL_WIDTH//2,310), 'menu_options.png', 'menu_options_press.png', (300,100))
        self._menu_exit = Button((200+self._ADDITIONAL_WIDTH//2,510), 'menu_exit.png', 'menu_exit_press.png', (300,100))

    def start(self):
        global visio_control

        buttons = Group()
        buttons.add(self._menu_play,self._menu_options,self._menu_exit)

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quitgame()

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if self._menu_play.is_aim(event.pos):
                        self._menu_play.press(True)

                    elif self._menu_options.is_aim(event.pos):
                        self._menu_options.press(True)

                    elif self._menu_exit.is_aim(event.pos):
                        self._menu_exit.press(True)

                elif event.type == pygame.MOUSEBUTTONUP:
                    if self._menu_play.is_aim(event.pos):
                        self._menu_play.press()
                        return 0

                    elif self._menu_options.is_aim(event.pos):
                        self._menu_options.press()
                        Thread(target=visio.show_video_capture, args=(self._DISPLAY_WIDTH, self._DISPLAY_HEIGHT)).start()
                        # Thread(target=visio.show_control_panel).start()
                        visio_control = True

                    elif self._menu_exit.is_aim(event.pos):
                        self._menu_exit.press()
                        self.quitgame()

            self._screen.fill(self._backgroun_color)
            buttons.draw(self._screen)
            buttons.update()
            pygame.display.update()


class Level(Game):
    def __init__(self, lvl_num):
        super(Level, self).__init__()
        self._lvl_num = lvl_num
        self._all_sprites = Group()
        self._static_sprites = Group()
        self._static_bg_sprites = Group()
        self._dynamic_sprites = Group()

        if self._lvl_num == 1:
            self._CELL_SIZE = 100
            percent = self._CELL_SIZE // 100 * 10
            self._OBJ_SIZE = (self._CELL_SIZE,self._CELL_SIZE)
            self._PLAYER_SIZE = (self._CELL_SIZE-percent,self._CELL_SIZE-percent)
            self._XSPEED=6
            self._YSPEED=10
            self.create_objects(crds_of_player=(300,300),
                                crds_of_boxes=[(100,200),(200,200)],
                                crds_of_blocks=[(100,100),(100,300),(300,400),(100,500),(200,500),(300,500)],
                                crds_of_prize=(500,100),
                                crds_of_skulls=[(500,500),(400,500),(100,400)])

        elif self._lvl_num == 2:
            self._CELL_SIZE = 100
            percent = self._CELL_SIZE // 100 * 10
            self._OBJ_SIZE = (self._CELL_SIZE,self._CELL_SIZE)
            self._PLAYER_SIZE = (self._CELL_SIZE-percent,self._CELL_SIZE-percent)
            self._XSPEED=6
            self._YSPEED=10
            self.create_objects(crds_of_player=(100,500),
                                crds_of_boxes=[(100,100),(400,100)],
                                crds_of_blocks=[(200,200),(500,100),(300,400),(500,500)],
                                crds_of_prize=(400,100),
                                crds_of_skulls=[(500,400)],
                                crds_of_portals=[(400,500),(500,200)])

        elif self._lvl_num == 3:
            self._CELL_SIZE = 50
            percent = self._CELL_SIZE // 100 * 10
            self._OBJ_SIZE = (self._CELL_SIZE,self._CELL_SIZE)
            self._PLAYER_SIZE = (self._CELL_SIZE-percent,self._CELL_SIZE-percent)
            self._XSPEED=4
            self._YSPEED=10
            self.create_objects(crds_of_player=(50,300),
                                crds_of_boxes=[(350,400),(350,350),(50,250),(100,100),(100,150),(150,100),(150,150),(150,50),(300,100),\
                                              (300,50),(450,250),(450,200),(450,150),(550,50),(600,50),(550,100),(600,100)],
                                crds_of_blocks=[(350,300),(100,50),(150,100),(200,400),(500,250),(50,350),(50,400),(50,450)],
                                crds_of_prize=(300,250),
                                crds_of_skulls=[(250,300),(250,250),(400,300),(500,400),(50,550),(300,150),(300,100),(600,600),(550,600),(500,600),(200,350)],
                                crds_of_portals=[(400,500),(500,200)])
            self._player._gravity = 0.7

    def track_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quitgame()

            if event.type == pygame.KEYDOWN:
                if event.key == 97: # a
                    self._player.go('left', True)
                
                elif event.key == 100: # d
                    self._player.go('right', True)
                
                elif event.key == 119\
                and self._player.get_center()['y'] == self._player._ground : # w
                    self._player.go('up', True)

            if event.type == pygame.KEYUP:
                if event.key == 97:
                    self._player.go('left', False)
                
                elif event.key == 100:
                    self._player.go('right', False)

                elif event.key == pygame.K_LEFT or event.key == 122: # <- or z
                    grid = self.place_to_grid(all_sprites)
                    self.rotate_grid('left',grid)

                elif event.key == pygame.K_RIGHT or event.key == 120: # -> or x
                    grid = self.place_to_grid(all_sprites)
                    self.rotate_grid('right',grid)

            if event.type == pygame.MOUSEBUTTONUP:
                if self._pause.is_aim(event.pos):
                    menu = Menu()
                    menu.start()

        if visio_control:
            global aim_x, aim_y

            if aim_x > self._DISPLAY_WIDTH//2 and aim_y > self._DISPLAY_HEIGHT//2: # ->
                self._player.go('left', False)
                self._player.go('right', True)

            if aim_x < self._DISPLAY_WIDTH//2 and aim_y > self._DISPLAY_HEIGHT//2: # <-
                self._player.go('right', False)
                self._player.go('left', True)

            if aim_x < self._DISPLAY_WIDTH//2 and aim_y < self._DISPLAY_HEIGHT//3\
            and self._player.get_center()['y'] == self._player._ground:  
                self._player.go('right', False)
                self._player.go('up', True)
                self._player.go('left', True)

            if aim_x > self._DISPLAY_WIDTH//2 and aim_y < self._DISPLAY_HEIGHT//3\
            and self._player.get_center()['y'] == self._player._ground:
                self._player.go('left', False)
                self._player.go('up', True)
                self._player.go('right', True)

    def create_objects(self, crds_of_player, crds_of_blocks, crds_of_prize, crds_of_boxes=(), crds_of_skulls=(), crds_of_portals=()):
        self._player = Player(xspeed=self._XSPEED, yspeed=self._YSPEED, size=self._PLAYER_SIZE,image=self._player_img,coords=crds_of_player)
        self._prize = Prize(size=self._OBJ_SIZE,image=self._exit_img,coords=crds_of_prize)
        self._static_bg_sprites.add(self._prize)
        self._dynamic_sprites.add(self._player)

        if crds_of_portals:
            self._portal0 = Portal(size=self._OBJ_SIZE, portal_id=0,image=self._portal_img,coords=crds_of_portals[0],twin_coords=crds_of_portals[1])
            self._portal1 = Portal(size=self._OBJ_SIZE, portal_id=1,image=self._portal_img,coords=crds_of_portals[1],twin_coords=crds_of_portals[0])
            self._static_bg_sprites.add(self._portal0, self._portal1)

        for coords in crds_of_boxes:
            box = Box(xspeed=self._XSPEED,yspeed=self._YSPEED,size=self._OBJ_SIZE,image=self._box_img,coords=coords)
            self._dynamic_sprites.add(box)

        for coords in crds_of_blocks:
            block = Block(size=self._OBJ_SIZE,image=self._block_img,coords=coords)
            self._static_sprites.add(block)

        for coords in crds_of_skulls:
            skull = Skull(size=self._OBJ_SIZE,image=self._skull_img,coords=coords)
            self._static_bg_sprites.add(skull)

        coords = set()

        for j in range(self._DISPLAY_HEIGHT//self._CELL_SIZE):
            coords.add((j*self._CELL_SIZE,0)) 
            coords.add((j*self._CELL_SIZE,self._DISPLAY_HEIGHT-self._CELL_SIZE))
            coords.add((0,j*self._CELL_SIZE))
            coords.add((self._DISPLAY_WIDTH-self._CELL_SIZE,j*self._CELL_SIZE))

        for c in coords: 
            self._static_sprites.add(Block(size=self._OBJ_SIZE,image=self._frame_img,coords=c))

        self._all_sprites.add(t=tuple(self._dynamic_sprites.get()^self._static_bg_sprites.get()^self._static_sprites.get()))

    def start(self):
        global all_sprites, all_without_bg
        
        while True:
            all_sprites = self._all_sprites
            all_without_bg = self._all_sprites.get()^self._static_bg_sprites.get() 

            if self._player.on_prize():
                self.show_message_of_win()
                return                       

            elif self._player.is_dead():
                self.show_message_of_death()
                self.__init__(self._lvl_num)
                self.start()
                return

            else:
                self.track_events()
                self._screen.fill(self._backgroun_color)
                self._static_sprites.draw(self._screen)
                self._static_bg_sprites.draw(self._screen)
                self._dynamic_sprites.draw(self._screen)
                self._static_sprites.update()
                self._static_bg_sprites.update()
                self._dynamic_sprites.update()

                if visio_control: self._screen.blit(self._aim_img, (aim_x, aim_y))

                self._screen.blit(self._pause.get_image(), self._pause.get_coords())
                pygame.display.update()
                self._clock.tick(self._FPS)
