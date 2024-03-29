import math
import random

import pygame
import os
import config
from itertools import permutations
from queue import PriorityQueue
from util import *


class BaseSprite(pygame.sprite.Sprite):
    images = dict()

    def __init__(self, x, y, file_name, transparent_color=None, wid=config.SPRITE_SIZE, hei=config.SPRITE_SIZE):
        pygame.sprite.Sprite.__init__(self)
        if file_name in BaseSprite.images:
            self.image = BaseSprite.images[file_name]
        else:
            self.image = pygame.image.load(os.path.join(config.IMG_FOLDER, file_name)).convert()
            self.image = pygame.transform.scale(self.image, (wid, hei))
            BaseSprite.images[file_name] = self.image
        # making the image transparent (if needed)
        if transparent_color:
            self.image.set_colorkey(transparent_color)
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)


class Surface(BaseSprite):
    def __init__(self):
        super(Surface, self).__init__(0, 0, 'terrain.png', None, config.WIDTH, config.HEIGHT)


class Coin(BaseSprite):
    def __init__(self, x, y, ident):
        self.ident = ident
        super(Coin, self).__init__(x, y, 'coin.png', config.DARK_GREEN)

    def get_ident(self):
        return self.ident

    def position(self):
        return self.rect.x, self.rect.y

    def draw(self, screen):
        text = config.COIN_FONT.render(f'{self.ident}', True, config.BLACK)
        text_rect = text.get_rect(center=self.rect.center)
        screen.blit(text, text_rect)


class CollectedCoin(BaseSprite):
    def __init__(self, coin):
        self.ident = coin.ident
        super(CollectedCoin, self).__init__(coin.rect.x, coin.rect.y, 'collected_coin.png', config.DARK_GREEN)

    def draw(self, screen):
        text = config.COIN_FONT.render(f'{self.ident}', True, config.RED)
        text_rect = text.get_rect(center=self.rect.center)
        screen.blit(text, text_rect)


class Agent(BaseSprite):
    def __init__(self, x, y, file_name):
        super(Agent, self).__init__(x, y, file_name, config.DARK_GREEN)
        self.x = self.rect.x
        self.y = self.rect.y
        self.step = None
        self.travelling = False
        self.destinationX = 0
        self.destinationY = 0

    def set_destination(self, x, y):
        self.destinationX = x
        self.destinationY = y
        self.step = [self.destinationX - self.x, self.destinationY - self.y]
        magnitude = math.sqrt(self.step[0] ** 2 + self.step[1] ** 2)
        self.step[0] /= magnitude
        self.step[1] /= magnitude
        self.step[0] *= config.TRAVEL_SPEED
        self.step[1] *= config.TRAVEL_SPEED
        self.travelling = True

    def move_one_step(self):
        if not self.travelling:
            return
        self.x += self.step[0]
        self.y += self.step[1]
        self.rect.x = self.x
        self.rect.y = self.y
        if abs(self.x - self.destinationX) < abs(self.step[0]) and abs(self.y - self.destinationY) < abs(self.step[1]):
            self.rect.x = self.destinationX
            self.rect.y = self.destinationY
            self.x = self.destinationX
            self.y = self.destinationY
            self.travelling = False

    def is_travelling(self):
        return self.travelling

    def place_to(self, position):
        self.x = self.destinationX = self.rect.x = position[0]
        self.y = self.destinationX = self.rect.y = position[1]

    # coin_distance - cost matrix
    # return value - list of coin identifiers (containing 0 as first and last element, as well)
    def get_agent_path(self, coin_distance):
        pass


class ExampleAgent(Agent):
    def __init__(self, x, y, file_name):
        super().__init__(x, y, file_name)

    def get_agent_path(self, coin_distance):
        path = [i for i in range(1, len(coin_distance))]
        random.shuffle(path)
        return [0] + path + [0]

class Aki(Agent):
    def __init__(self, x, y, file_name):
        super().__init__(x, y, file_name)

    def get_agent_path(self, coin_distance):
        if len(coin_distance) == 1:
            return [0]
        
        visit = [False for x in range(len(coin_distance))]
        stack = []
        path = []
        start_idx = 0
        
        stack.append(start_idx)
        while len(stack):
            v = stack.pop()
            visit[v] = True
            path.append(v)
            next = find_next_coin_dfs(visit, coin_distance[v])
            if next:
                stack.append(next)
        
        return path + [0]


class Jocke(Agent):
    def __init__(self, x, y, file_name):
        super().__init__(x, y, file_name)

    def get_agent_path(self, coin_distance):
        if len(coin_distance) == 1:
            return [0]

        start_idx = 0
        vertices = [i for i in range(1, len(coin_distance))]
        path = []
    
        min_path_weight = math.inf
        perms = permutations(vertices)
        for i in perms:
            current_path_weight = 0
            current_path = []
            k = start_idx
            for j in i:
                current_path_weight += coin_distance[k][j]
                current_path.append(j)
                k = j
            current_path_weight += coin_distance[k][start_idx]
    
            if(current_path_weight < min_path_weight):
                min_path_weight = current_path_weight
                path = current_path
            
        return [0] + path + [0]


class Uki(Agent):
    def __init__(self, x, y, file_name):
        super().__init__(x, y, file_name)

    def get_agent_path(self, coin_distance):
        q = PriorityQueue()
        curr_pp = PartialPath([0], 0)

        num_of_nodes = len(coin_distance)

        q.put(curr_pp)

        while not q.empty():
            curr_pp = q.get()
            if len(curr_pp.path) == num_of_nodes + 1:
                return curr_pp.path
            
            cost = curr_pp.cost
            partial_path = curr_pp.path
            last_node = curr_pp.path[-1]

            for i in range(len(coin_distance)):
                if i not in partial_path or (i in partial_path and i == 0 and len(partial_path) == num_of_nodes):
                    new_partial_path = partial_path.copy()
                    new_partial_path.append(i)
                    new_cost = cost + coin_distance[last_node][i]
                    pp = PartialPath(new_partial_path, new_cost)
                    q.put(pp)


class Micko(Agent):
    def __init__(self, x, y, file_name):
        super().__init__(x, y, file_name)

    def get_agent_path(self, coin_distance):
        q = PriorityQueue()
        initial_path = [0]
        heuristic = calculate_heuristic(0, set(initial_path[1:-1]), coin_distance)
        curr_pp = PartialPathAStar([0], heuristic, heuristic)
        all_nodes_set = set([x for x in range(0, len(coin_distance))])

        num_of_nodes = len(coin_distance)

        q.put(curr_pp)

        while not q.empty():
            curr_pp = q.get()
            if len(curr_pp.path) == num_of_nodes + 1:
                return curr_pp.path
            
            cost = curr_pp.cost
            partial_path = curr_pp.path
            last_node = curr_pp.path[-1]

            for i in range(len(coin_distance)):
                if i not in partial_path or (i in partial_path and i == 0 and len(partial_path) == num_of_nodes):
                    new_partial_path = partial_path.copy()
                    new_partial_path.append(i)
                    heuristic = calculate_heuristic(i, set(new_partial_path[1:-1]), coin_distance)
                    new_cost = cost + coin_distance[last_node][i] - curr_pp.heuristic + heuristic
                    pp = PartialPathAStar(new_partial_path, new_cost, heuristic)
                    q.put(pp)
