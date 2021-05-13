import pygame
import time
import math
import numpy
import random

# constants
height, width = 500, 500
speed = (height / 200) * 5
bullet_speed = 2 * speed
min_pos = [width / 10, height / 10]
max_pos = [9 * width / 10, 9 * height / 10]
player_control = True
show_game = True
player_radius = 10
bullet_radius = 20
reload_frames = 10

# player = ammo, pos, reloading
one_ammo = True
one_pos = min_pos
one_reload = 0

two_ammo = True
two_pos = max_pos
two_reload = 0

# bullet = pos, dir, shooter
one_bullet_pos = [-1000, -1000]
one_bullet_dir = [0, 0]
two_bullet_pos = [-1000, -1000]
two_bullet_dir = [0, 0]

# controls
held = set()

# game shit
running = True
pygame.init()
screen = pygame.display.set_mode([height, width])


class MCBot:
    def __init__(self):
        # v[0] - self reloading, 10 states
        # v[1] - no ammo
        #    3: enemy reloading (0 means enemy has ammo, 1/2 is reloading progress (1 - more, 2 - less)
        #   20: dist to enemy (max sqrt(height^2 + width^2))
        #   10: 0-8 if own bullet is heading towards enemy, higher means further dist. 9 otherwise
        #   10: 0-8 same but for enemy bullet
        # v[2] - same as above but have ammo
        self.v = [numpy.zeros((10, 1, 1, 1)), numpy.zeros((3, 20, 10, 10)), numpy.zeros((3, 20, 10, 10))]
        # if ammo/no ammo, five actions. first four are movement, last is either reload or shoot at enemy
        self.q = [numpy.zeros((10, 1, 1, 1, 1)), numpy.zeros((3, 2, 10, 10, 5)), numpy.zeros((3, 20, 10, 10, 5))]
        self.epsilon = 0.1

    def action(self, state):
        # 0 - nothing
        # 1 - reload/shoot
        # 2345 - move toward/away, strafe left/right
        if state[0] == 0:
            return 0
        if numpy.random.random(1)[0] < self.epsilon:  # act randomly
            return random.randint(1, 5)  # inclusive
        # return self.q[tuple(state)] TODO: figure out how to index a list given iterable of coordinates
                                    # also this should be argmax


one = None if player_control else MCBot()
two = MCBot()

while running:
    if show_game:
        screen.fill((255, 255, 255))
        pygame.draw.circle(screen, (0, 0, 255), one_pos, player_radius)
        pygame.draw.circle(screen, (255, 0, 0), two_pos, player_radius)
        if one_bullet_pos[0] != -1000:
            pygame.draw.circle(screen, (0, 255, 0), one_bullet_pos, bullet_radius)
        if one_bullet_pos[0] != -1000:
            pygame.draw.circle(screen, (0, 255, 255), two_bullet_pos, bullet_radius)
        if one_ammo:
            pygame.draw.circle(screen, (0, 255, 0), one_pos, 5)
        if two_ammo:
            pygame.draw.circle(screen, (0, 255, 255), two_pos, 5)
        pygame.display.flip()
        time.sleep(0.05)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if player_control:
            if player_control and event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d]:
                    held.add(event.key)
                if event.key == pygame.K_r:
                    one_reload = reload_frames
            if player_control and event.type == pygame.KEYUP:
                if event.key in [pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d]:
                    held.remove(event.key)
            if player_control and event.type == pygame.MOUSEBUTTONDOWN:
                if one_ammo:
                    one_ammo = False
                    click = pygame.mouse.get_pos()
                    one_bullet_dir = [click[0] - one_pos[0], click[1] - one_pos[1]]
                    mag = math.sqrt(one_bullet_dir[0] * one_bullet_dir[0] + one_bullet_dir[1] * one_bullet_dir[1])
                    one_bullet_dir[0] /= mag / bullet_speed
                    one_bullet_dir[1] /= mag / bullet_speed
                    one_bullet_pos = [x for x in one_pos]

    # bullet
    one_bullet_pos[0] += one_bullet_dir[0]
    one_bullet_pos[1] += one_bullet_dir[1]
    two_bullet_pos[0] += two_bullet_dir[0]
    two_bullet_pos[1] += two_bullet_dir[1]

    # collision 1->2
    if math.dist(one_bullet_pos, two_pos) < (bullet_radius + player_radius):
        one_bullet_pos = [-1000, -1000]
        one_bullet_dir = [0, 0]
    # collision 2->1
    if math.dist(two_bullet_pos, one_pos) < (bullet_radius + player_radius):
        two_bullet_pos = [-1000, -1000]
        two_bullet_dir = [0, 0]

    # reload
    one_ammo |= one_reload == 1
    one_reload = max(0, one_reload - 1)
    two_ammo |= two_reload == 1
    two_reload = max(0, two_reload - 1)

    # compute states
    # dist (symmetric)
    dist = min(int(math.dist(one_pos, two_pos) * 20 / 710), 19)

    # bullet one check
    one_bullet_dist = 9
    if one_bullet_pos[0] != -1000:
        p1 = one_bullet_pos
        p2 = [one_bullet_pos[0] + one_bullet_dir[0], one_bullet_pos[1] + one_bullet_dir[1]]
        # https://en.wikipedia.org/wiki/Distance_from_a_point_to_a_line#Line_defined_by_two_points
        min_dist = math.fabs((p2[0] - p1[0]) * (p1[1] * two_pos[1]) - (p1[0] - two_pos[0]) * (p2[1] - p1[1]))
        if min_dist < (player_radius + bullet_radius) * bullet_speed:
            one_bullet_dist = min(int(math.dist(one_bullet_pos, two_pos) * 9 / 710), 8)

    # bullet two check
    two_bullet_dist = 9
    if two_bullet_pos[0] != -1000:
        p1 = two_bullet_pos
        p2 = [two_bullet_pos[0] + two_bullet_dir[0], two_bullet_pos[1] + two_bullet_dir[1]]
        min_dist = math.fabs((p2[0] - p1[0]) * (p1[1] * one_pos[1]) - (p1[0] - one_pos[0]) * (p2[1] - p1[1]))
        if min_dist < (player_radius + bullet_radius) * bullet_speed:
            two_bullet_dist = min(int(math.dist(two_bullet_pos, one_pos) * 9 / 710), 8)

    state_one = [0, 0, 0, 0, 0]
    two_reload_chunk = (two_reload + (reload_frames // 2) - 1) / (reload_frames // 2)
    if one_reload == 0:
        state_one = [1 + one_ammo, two_reload_chunk, dist, one_bullet_dist, two_bullet_dist]

    state_two = [0, 0, 0, 0, 0]
    one_reload_chunk = (one_reload + (reload_frames // 2) - 1) / (reload_frames // 2)
    if two_reload == 0:
        state_two = [1 + two_ammo, one_reload_chunk, dist, two_bullet_dist, one_bullet_dist]

    if player_control and one_reload == 0 and len(held) > 0:  # move player
        key = list(held)[0]
        if key == pygame.K_w:
            one_pos[1] -= speed
        elif key == pygame.K_a:
            one_pos[0] -= speed
        elif key == pygame.K_s:
            one_pos[1] += speed
        elif key == pygame.K_d:
            one_pos[0] += speed
        one_pos = [min(max_pos[0], max(min_pos[0], one_pos[0])), min(max_pos[1], max(min_pos[1], one_pos[1]))]





pygame.quit()
