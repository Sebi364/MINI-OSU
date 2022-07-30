#!/bin/python
import pygame
import time
import random
import math
from pygame.math import Vector2
import numpy
from scipy import interpolate
################################################################################
#Display
RESOLUTION = (1920, 1200)
#Circle settings
INNER_CIRCLE_RADIUS = 60
INNER_CIRCLE_WIDTH = 10
OUTER_CIRCLE_START_RADIUS = 200
OUTER_CIRCLE_WIDTH = 1
TIME_FOR_CIRCLE = 1.5
CIRCLE_SCORE = 1000
#Slider settings
SLIDER_SPEED = 300
SLIDER_SCORE = 5000
#Gameplay
MINIMAL_TRAVEL_DISTANCE = 200
MAXIMAL_TRAVEL_DISTANCE = 700
DISTANC_FROM_BORDER = 200
HITT_ACCURACY = 50
DRIFT_SPEED = 0.025
#controls
USE_TABLET = False
TABLET_AREA = 40
TABLET_Y_OFFSET = 0
TABLET_X_OFFSET = 0
#Look
OBJECTS_FROM_FUTURE = 2
BACKGROUND_COLOR = 'black'
MAIN_COLLOR = 'white'
LINE_COLLOR = (50,50,50)
LINE_WIDTH = 2
CURSOR_LINE_COLOR = 'yellow'
CURSOR_LINE_WIDTH = 5
CURSOR_SIZE = 20
CURSOR_COLOR = 'cyan'
SLIDER_COLOR = 'magenta'
FONT_SIZE = 50
################################################################################

# game state
game_state = {
    "objects" : [],
    "current_object" : 0,
    "generated_time" : 0,
    "cursor_pos" : [0,0],
    "running" : True,
    "score" : 1,
    "max_score": 1,
}

#other variables
starttime = time.time()
runtime = 0
last_delta = 0
delta = 0
is_x_pressed = False

#function to check if something is on screen
def clip(val, min, max):
    if val>max:
        return max
    if val<min:
        return min
    return val

# class for the circle
class Circle:
    def __init__(self,
                    pos,
                    time,
                    end_time,
                    drift,
                    drift_turn,
                    res
                    ):
        self.pos = pos
        self.pos1 = pos
        self.pos2 = pos
        self.time = time
        self.end_time = end_time
        self.outer = OUTER_CIRCLE_START_RADIUS
        self.running = True
        self.drift = drift
        self.drift_turn = drift_turn
        self.res = res
        self.score = 0
        self.was_circle_already_pressed = False

    def update(self,screen,drift_speed):
        if self.running == True:
            if runtime < self.end_time:
                self.outer = (OUTER_CIRCLE_START_RADIUS - INNER_CIRCLE_RADIUS) /self.time * (self.end_time - runtime) + INNER_CIRCLE_RADIUS
                if self.outer > OUTER_CIRCLE_START_RADIUS:
                    self.outer = 0

                #calculate drift
                self.drift = self.drift + self.drift_turn
                v = Vector2(drift_speed,0)
                v = v.rotate(self.drift)
                self.pos = self.pos + v
                self.pos[0] = clip(self.pos[0], INNER_CIRCLE_RADIUS, self.res[0] - INNER_CIRCLE_RADIUS)
                self.pos[1] = clip(self.pos[1], INNER_CIRCLE_RADIUS, self.res[1] - INNER_CIRCLE_RADIUS)
                self.pos1 = self.pos
                self.pos2 = self.pos
                if is_key_just_pressed() == True:
                    if self.outer > INNER_CIRCLE_RADIUS and self.outer < INNER_CIRCLE_RADIUS + HITT_ACCURACY:
                        if math.dist(self.pos,game_state["cursor_pos"]) < INNER_CIRCLE_RADIUS + HITT_ACCURACY:
                            if self.was_circle_already_pressed == False:
                                self.score = self.score + CIRCLE_SCORE
                                self.was_circle_already_pressed = True
                self.render(screen)
                return 0
            elif runtime > self.end_time:
                return 1

    def destroy(self):
        self.running = False
        game_state["max_score"] = game_state["max_score"] + CIRCLE_SCORE
        return self.score
    def render(self, screen):
        pygame.draw.circle(screen, MAIN_COLLOR, self.pos, self.outer,OUTER_CIRCLE_WIDTH)
        pygame.draw.circle(screen, MAIN_COLLOR, self.pos, INNER_CIRCLE_RADIUS)
        pygame.draw.circle(screen, BACKGROUND_COLOR, self.pos, INNER_CIRCLE_RADIUS - INNER_CIRCLE_WIDTH)

#class for the slider
class Slider:
    def __init__(self,
                points,
                time_for_slider,
                end_time,
                ):
        self.points = points
        self.point_number = len(points)
        self.running = True
        self.pos = points[-1]
        self.pos0 = points[0]
        self.pos1 = points[0]
        self.pos2 = points[-1]
        self.time_for_slider = time_for_slider - TIME_FOR_CIRCLE
        self.time_for_circle = TIME_FOR_CIRCLE
        self.end_time = end_time
        self.outer = 200
        self.outer_size = 0
        self.on_circle = 0
        self.Max_points = 0
        self.score = 0
        self.was_circle_already_pressed = False

    def destroy(self):
        self.running = False
        self.score = self.score + (SLIDER_SCORE / self.Max_points * self.on_circle)
        game_state["max_score"] = game_state["max_score"] + CIRCLE_SCORE + SLIDER_SCORE
        return self.score

    def update(self,screen,drift_speed):
        if self.running == True:
            pygame.draw.lines(screen, SLIDER_COLOR, False, self.points,10)
            pygame.draw.circle(screen, MAIN_COLLOR, self.pos, 60)
            pygame.draw.circle(screen, BACKGROUND_COLOR, self.pos, 50)
            if runtime > self.end_time - self.time_for_circle - self.time_for_slider and runtime < self.end_time - self.time_for_slider:
                v =  self.time_for_circle - (runtime - (self.end_time - self.time_for_slider - self.time_for_circle))
                self.outer = (140 / self.time_for_circle * v) + 60
                pygame.draw.circle(screen, MAIN_COLLOR, self.pos, self.outer,1)

                if is_key_just_pressed() == True:
                    if self.outer > INNER_CIRCLE_RADIUS and self.outer < INNER_CIRCLE_RADIUS + HITT_ACCURACY:
                        if math.dist(self.pos,game_state["cursor_pos"]) < INNER_CIRCLE_RADIUS + HITT_ACCURACY:
                            if self.was_circle_already_pressed == False:
                                self.score = self.score + CIRCLE_SCORE
                                self.was_circle_already_pressed = True

            if runtime > self.end_time - self.time_for_slider and runtime < self.end_time:
                self.time_on_slider = self.end_time - runtime
                self.pos0 = round(len(self.points)/self.time_for_slider*self.time_on_slider)
                try:
                    pygame.draw.circle(screen, MAIN_COLLOR, self.points[self.pos0], 60)
                    pygame.draw.circle(screen, BACKGROUND_COLOR, self.points[self.pos0], 50)
                    self.pos = self.points[self.pos0]
                except:
                    pass
                if is_key_pressed() == True:
                    if math.dist(self.pos,game_state["cursor_pos"]) < INNER_CIRCLE_RADIUS:
                        self.on_circle = self.on_circle + 1
                        self.Max_points = self.Max_points + 1
                    else:
                        self.Max_points = self.Max_points + 1
                else:
                    self.Max_points = self.Max_points + 1
                return 0
            elif self.end_time < runtime:
                return 1

#Draw Lies
def draw_lines():
    global game_state
    for x in range(1,OBJECTS_FROM_FUTURE + 1):
         pygame.draw.line(screen,
                            LINE_COLLOR,
                            game_state["objects"][game_state["current_object"] +x -1].pos1,
                            game_state["objects"][game_state["current_object"] +x].pos2,
                            LINE_WIDTH
                            )
#draw a line betwen cursor and current object
def draw_cursor_line():
    global game_state
    pygame.draw.line(screen,
                       CURSOR_LINE_COLOR,
                       game_state["objects"][game_state["current_object"]].pos,
                       game_state["cursor_pos"],
                       CURSOR_LINE_WIDTH
                       )

#draw a text onto the screen
def draw_text(position,text,text_color):
    pos_x = position[0]*(RESOLUTION[0] -(FONT_SIZE * len(text)*0.5))
    pos_y = position[1]*(RESOLUTION[1] -FONT_SIZE -40)
    screen.blit(font.render(text, False, text_color), (pos_x,pos_y))

#draw stats
def draw_stats():
    #draw_text([0,0],f"MAX_POSSIBLE: {game_state['max_score']}",'red')
    #draw_text([1,0],f"SCORE: {game_state['score']}",'green')
    draw_text([0.5,0],f"accuracy: {round(100 / game_state['max_score'] * game_state['score'])}%",'white')

def generate_object():
    global game_state
    if random.randint(0,5) > 0:
        pos_x = random.randint(DISTANC_FROM_BORDER, RESOLUTION[0]- DISTANC_FROM_BORDER)
        pos_y = random.randint(DISTANC_FROM_BORDER, RESOLUTION[1] - DISTANC_FROM_BORDER)
        pos = [pos_x,pos_y]
        try:
            while ((math.dist(pos,game_state["objects"][len(game_state["objects"])-1].pos) < MINIMAL_TRAVEL_DISTANCE) or
                    (math.dist(pos,game_state["objects"][len(game_state["objects"])-1].pos) > MAXIMAL_TRAVEL_DISTANCE)):
                pos_x = random.randint(DISTANC_FROM_BORDER, WINDOW_SIZE[0]- DISTANC_FROM_BORDER)
                pos_y = random.randint(DISTANC_FROM_BORDER, WINDOW_SIZE[1] - DISTANC_FROM_BORDER)
                pos = [pos_x,pos_y]
        except Exception as e:
            pass
        time = game_state["generated_time"] + TIME_FOR_CIRCLE
        drift = random.randint(0,360)
        drift_turn = random.randint(-100,100)/2000
        game_state["generated_time"] = game_state["generated_time"] + TIME_FOR_CIRCLE
        game_state["objects"].append(Circle(pos,
                                TIME_FOR_CIRCLE,
                                time,
                                drift,
                                drift_turn,
                                RESOLUTION
                                ))
    else:
        points = []
        for x in range(3):
            pos_x = random.randint(DISTANC_FROM_BORDER, RESOLUTION[0]- DISTANC_FROM_BORDER)
            pos_y = random.randint(DISTANC_FROM_BORDER, RESOLUTION[1] - DISTANC_FROM_BORDER)
            pos = [pos_x,pos_y]
            points.append([pos_x,pos_y])
        points = generate_line_path(points)
        length = calculate_path_length(points)

        while length < 400 and length > 1500:
            points = []
            for x in range(3):
                pos_x = random.randint(DISTANC_FROM_BORDER, RESOLUTION[0]- DISTANC_FROM_BORDER)
                pos_y = random.randint(DISTANC_FROM_BORDER, RESOLUTION[1] - DISTANC_FROM_BORDER)
                pos = [pos_x,pos_y]
                points.append([pos_x,pos_y])
            points = generate_line_path(points)
            length = calculate_path_length(points)


        time = (length/SLIDER_SPEED)+TIME_FOR_CIRCLE
        end_time = game_state["generated_time"] + time
        game_state["generated_time"] = end_time
        game_state["objects"].append(Slider(points,time,end_time))
def calculate_path_length(points):
    length = 0
    for x in range(len(points)-1):
        length = length + math.dist(points[x],points[x+1])
    length = round(length)
    return length


def is_key_just_pressed():
    global is_x_pressed
    keys = pygame.key.get_pressed()
    x = False
    if (keys[pygame.K_x]):
        if is_x_pressed:
            x = False
        else:
            is_x_pressed = True
            x = True
    else:
        is_x_pressed = False

    return x

def is_key_pressed():
    x = False
    keys = pygame.key.get_pressed()
    if (keys[pygame.K_x]):
        x = True
    else:
        x = False
    return x

def get_input():
    global game_state
    if USE_TABLET == True:
        factor = TABLET_AREA/100
        mouse_pos = pygame.mouse.get_pos()
        x = (mouse_pos[0]-(((RESOLUTION[0]*(1-factor))/2)+TABLET_X_OFFSET))/factor
        y = (mouse_pos[1]-(((RESOLUTION[1]*(1-factor))/2)+TABLET_Y_OFFSET))/factor
        x = clip(x, 0, RESOLUTION[0])
        y = clip(y, 0, RESOLUTION[1])
        game_state["cursor_pos"] = [x,y]
        pygame.draw.circle(screen, CURSOR_COLOR, game_state["cursor_pos"], CURSOR_SIZE)
    else:
        game_state["cursor_pos"] = pygame.mouse.get_pos()
        pygame.draw.circle(screen, CURSOR_COLOR, game_state["cursor_pos"], CURSOR_SIZE)
# Setup, runs once at start of programm
def draw_objects():
    global game_state
    if game_state["objects"][game_state["current_object"]].update(screen,DRIFT_SPEED*delta) == 1:
        game_state["score"] = game_state["score"] + int(game_state["objects"][game_state["current_object"]].destroy())
        generate_object()
        game_state["current_object"] = game_state["current_object"] +1
    for x in range(OBJECTS_FROM_FUTURE+1):
        game_state["objects"][game_state["current_object"] + x].update(screen,DRIFT_SPEED*delta*100)

def generate_line_path(points):
    #prepare points for interpolation
    ctr = numpy.array(points)
    #separate x and y points becouse reasons?
    x=ctr[:,0]
    y=ctr[:,1]
    #interpolate points
    (tck,u)= interpolate.splprep([x,y],k=2,s=0)
    u=numpy.linspace(0,1,num=500,endpoint=True)
    out = interpolate.splev(u,tck)
    x = out[0]
    y = out[1]
    v = []
    #merge x and y list back into one list
    for i in range(0,len(x)):
        v.append([x[i],y[i]])
    #round numbers to something normal
    for i in v:
        i[0] = round(i[0])
        i[1] = round(i[1])
    #return final points
    return v

pygame.init()
icon = pygame.image.load('icon.png')
pygame.display.set_icon(icon)
font = pygame.font.Font('font.ttf', FONT_SIZE)
pygame.display.set_caption('MINI-OSU!')
pygame.mouse.set_visible(False)

delta = time.time() - last_delta
last_delta = time.time()
runtime = time.time() - starttime

screen = pygame.display.set_mode(RESOLUTION,pygame.FULLSCREEN)
for x in range(OBJECTS_FROM_FUTURE+1):
    generate_object()

while game_state["running"]:
    delta = time.time() - last_delta
    last_delta = time.time()
    runtime = time.time() - starttime
    screen.fill(BACKGROUND_COLOR)
    draw_lines()
    draw_objects()
    draw_stats()
    draw_cursor_line()
    get_input()
    for event in pygame.event.get():
        keys = pygame.key.get_pressed()
        if (event.type) == (pygame.QUIT) or keys[pygame.K_ESCAPE]:
            game_state["running"] = False
    pygame.display.update()
