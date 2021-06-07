import pygame
import time
import math
import numpy
import random
from collections import defaultdict
from bots import ManualBot, MCBot
from constants import *


class Simulator:
    def __init__(self):
        self.player_control = False
        self.show_game = False

        # game shit
        self.running = True
        pygame.init()
        self.screen = pygame.display.set_mode([800, 800])

        self.players = [None if self.player_control else MCBot([width / 3, height / 3]), MCBot([2 * width / 3, 2 * height / 3])]

    def episode(self, ):
        self.players[0].reset()
        self.players[1].reset()

        SAR = ([], [], []), ([], [], [])

        for _ in range(200):
            # compute states
            # dist (symmetric)
            dist = min(int(math.dist(self.players[0].pos, self.players[1].pos) * 20 / 710), 19)

            bullet_dist = [9, 9]
            # bullet check
            for i, player in enumerate(self.players):
                if player.bullet_pos[0] != -1000 and math.dist(player.bullet_pos, player.pos) < math.dist(self.players[1 - i].pos, player.pos):
                    p0 = self.players[1 - i].pos
                    p1 = player.bullet_pos
                    p2 = [player.bullet_pos[0] + player.bullet_dir[0], player.bullet_pos[1] + player.bullet_dir[1]]
                    # https://en.wikipedia.org/wiki/Distance_from_a_point_to_a_line#Line_defined_by_two_points
                    min_dist = abs(p1[0] * (p2[1] - p0[1]) + p2[0] * (p0[1] - p1[1]) + p0[0] * (p1[1] - p2[1]))
                    if min_dist < (player_radius + bullet_radius) * bullet_speed:
                        bullet_dist[i] = min(int(math.dist(player.bullet_pos, self.players[1 - i].pos) * 9 / 710), 8)

            states = [(0, (0, 0, 0, 0)), (0, (0, 0, 0, 0))]

            for i in range(2):
                if self.players[i].reload == 0:
                    enemy_reload_chunk = (self.players[1 - i].reload + reload_frames // 2 - 1) // (reload_frames // 2)
                    states[i] = (1 + self.players[i].ammo, (enemy_reload_chunk, dist, bullet_dist[1 - i], bullet_dist[i]))
                SAR[i][0].append((states[i][0], *states[i][1]))

            # action

            # player controlled actions
            # if player_control:
            #     for event in pygame.event.get():
            #         if event.type == pygame.KEYDOWN:
            #             if event.key in [pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d]:
            #                 held.add(event.key)
            #             if event.key == pygame.K_r:
            #                 one_reload = reload_frames
            #         if event.type == pygame.KEYUP:
            #             if event.key in [pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d]:
            #                 held.remove(event.key)
            #         if event.type == pygame.MOUSEBUTTONDOWN:
            #             if one_ammo:
            #                 one_ammo = False
            #                 click = pygame.mouse.get_pos()
            #                 one_bullet_dir = [click[0] - one_pos[0], click[1] - one_pos[1]]
            #                 mag = math.sqrt(
            #                     one_bullet_dir[0] * one_bullet_dir[0] + one_bullet_dir[1] * one_bullet_dir[1])
            #                 one_bullet_dir[0] /= mag / bullet_speed
            #                 one_bullet_dir[1] /= mag / bullet_speed
            #                 one_bullet_pos = [one_pos[0], one_pos[1]]

                # if one_reload == 0 and len(held) > 0:  # move player
                #     key = list(held)[0]
                #     if key == pygame.K_w:
                #         one_pos[1] -= speed
                #     elif key == pygame.K_a:
                #         one_pos[0] -= speed
                #     elif key == pygame.K_s:
                #         one_pos[1] += speed
                #     elif key == pygame.K_d:
                #         one_pos[0] += speed
            # else:
            pygame.event.get()

            # bot actions
            for i in range(2):
                this, other = self.players[i], self.players[1 - i]
                SAR[i][2].append(0)
                action = this.action(*states[i])
                SAR[i][1].append(action)
                if this.reload == 0:
                    enemy_dir = (other.pos[0] - this.pos[0], other.pos[1] - this.pos[1])
                    mag = max(0.001, math.sqrt(enemy_dir[0] * enemy_dir[0] + enemy_dir[1] * enemy_dir[1]))
                    enemy_dir = (enemy_dir[0] / mag, enemy_dir[1] / mag)
                    if action == 0:
                        if this.ammo:
                            this.ammo = False
                            this.bullet_dir = (enemy_dir[0] * bullet_speed, enemy_dir[1] * bullet_speed)
                            this.bullet_pos = [this.pos[0], this.pos[1]]
                            # one_SAR[2][-1] -= 0.5
                        else:
                            this.reload = reload_frames
                    elif action == 1:  # move toward enemy
                        this.pos[0] += enemy_dir[0] * speed
                        this.pos[1] += enemy_dir[1] * speed
                        SAR[i][2][-1] += forward_reward
                    elif action == 2:  # move away from enemy
                        this.pos[0] -= enemy_dir[0] * speed
                        this.pos[1] -= enemy_dir[1] * speed
                    elif action == 3:  # strafe left
                        this.pos[0] += enemy_dir[1] * speed
                        this.pos[1] -= enemy_dir[0] * speed
                        SAR[i][2][-1] += strafe_reward
                    else:  # action == 4, strafe right
                        this.pos[0] -= enemy_dir[1] * speed
                        this.pos[1] += enemy_dir[0] * speed
                        SAR[i][2][-1] += strafe_reward

                # this.pos = [min(max_pos[0], max(min_pos[0], this.pos[0])), min(max_pos[1], max(min_pos[1], this.pos[1]))]

                # bullet
                this.bullet_pos[0] += this.bullet_dir[0]
                this.bullet_pos[1] += this.bullet_dir[1]

            center = [(self.players[0].pos[0] + self.players[1].pos[0]) / 2, (self.players[0].pos[1] + self.players[1].pos[1]) / 2]
            offset = [400 - center[0], 400 - center[1]]
            for i in range(2):
                self.players[i].pos[0] += offset[0]
                self.players[i].pos[1] += offset[1]
                self.players[i].bullet_pos[0] += offset[0]
                self.players[i].bullet_pos[1] += offset[1]

            # reward

            for i in list(range(2)):
                this, other = self.players[i], self.players[1 - i]
                if math.dist(this.bullet_pos, other.pos) < (bullet_radius + player_radius):
                    SAR[1-i][2][-1] += lose_penalty
                    SAR[i][2][-1] += win_reward

                    if self.show_game:
                        self.draw(bullet_dist)

                    return SAR[0], SAR[1], i

            # reward for surviving
            SAR[0][2][-1] += survive_reward
            SAR[1][2][-1] += survive_reward

            # penalty for being far apart
            SAR[0][2][-1] += dist_mult_penalty * dist
            SAR[1][2][-1] += dist_mult_penalty * dist

            # reload
            for i in range(2):
                self.players[i].ammo |= self.players[i].reload == 1
                self.players[i].reload = max(0, self.players[i].reload - 1)

            if self.show_game:
                self.draw(bullet_dist)

        # timed out
        SAR[0][2][-1] += time_out_penalty
        SAR[1][2][-1] += time_out_penalty
        return SAR[0], SAR[1], 2
    # ~def episode()

    def draw(self, bullet_dist):
        self.screen.fill((255, 255, 255))
        if bullet_dist[1] != 9:  # bullet going towards first player
            pygame.draw.circle(self.screen, (255, 0, 255), self.players[0].pos, player_radius + 6)
        if bullet_dist[0] != 9:
            pygame.draw.circle(self.screen, (255, 0, 255), self.players[1].pos, player_radius + 6)
        if self.players[0].reload == 0:
            pygame.draw.circle(self.screen, (0, 0, 255), self.players[0].pos, player_radius)
        else:
            pygame.draw.circle(self.screen, (0, 0, 0), self.players[0].pos, player_radius)
        if self.players[1].reload == 0:
            pygame.draw.circle(self.screen, (255, 0, 0), self.players[1].pos, player_radius)
        else:
            pygame.draw.circle(self.screen, (0, 0, 0), self.players[1].pos, player_radius)
        if self.players[0].bullet_pos[0] != -1000:
            pygame.draw.circle(self.screen, (0, 255, 0), self.players[0].bullet_pos, bullet_radius)
        if self.players[1].bullet_pos[0] != -1000:
            pygame.draw.circle(self.screen, (0, 255, 255), self.players[1].bullet_pos, bullet_radius)
        if self.players[0].ammo:
            pygame.draw.circle(self.screen, (0, 255, 0), self.players[0].pos, 5)
        if self.players[1].ammo:
            pygame.draw.circle(self.screen, (0, 255, 255), self.players[1].pos, 5)

        pygame.display.flip()
        time.sleep(0.05)


simul = Simulator()

for i in range(1000):
    if i == 10:
        simul.players[0].greedy = True
        simul.players[1].greedy = True
    simul.show_game = True
    simul.episode()
    simul.show_game = False

    wins = 0
    ties = 0
    games = 0

    f, s = 0., 0.

    for _ in range(1000):
        start = time.time()
        e1, e2, w = simul.episode()
        f += time.time() - start
        games += 1
        wins += w == 1
        ties += w == 2
        simul.players[0].update(*e1)
        start = time.time()
        simul.players[1].update(*e2)
        s += time.time() - start
    # print(f, s)

    print("win rate: ", wins / games)
    print("tie rate: ", ties / games)
    print()



pygame.quit()
