import numpy
import random
from collections import defaultdict
from constants import *


class Player:
    def __init__(self, init_pos):
        self.init_pos = init_pos
        self.reset()

    def reset(self):
        self.reload = 0
        self.pos = [random.randint(0, width), random.randint(0, height)]
        self.ammo = True
        self.bullet_pos = [-1000, -1000]
        self.bullet_dir = [0, 0]


class MCBot(Player):
    def __init__(self, init_pos):
        # v[0] - self reloading, 10 states
        # v[1] - no ammo
        #    3: enemy reloading (0 means enemy has ammo, 1/2 is reloading progress (1 - more, 2 - less)
        #   20: dist to enemy (max sqrt(height^2 + width^2))
        #   10: 0-8 if own bullet is heading towards enemy, higher means further dist. 9 otherwise
        #   10: same but for enemy bullet
        # v[2] - same as above but have ammo
        super().__init__(init_pos)
        self.v = [
            0.1 * (2 * numpy.random.random((10, 1, 1, 1)) - 1),
            0.1 * (2 * numpy.random.random((3, 20, 10, 10)) - 1),
            0.1 * (2 * numpy.random.random((3, 20, 10, 10)) - 1),
        ]  # so actually i dont use this but lol whatever
        # if ammo/no ammo, five actions. first four are movement, last is either reload or shoot at enemy
        self.q = [
            0.1 * (2 * numpy.random.random((10, 1, 1, 1, 1)) - 1),
            0.1 * (2 * numpy.random.random((3, 20, 10, 10, 5)) - 1),
            0.1 * (2 * numpy.random.random((3, 20, 10, 10, 5)) - 1),
        ]
        self.n = [numpy.zeros_like(x) for x in self.q]
        self.epsilon = 0.02
        self.gamma = 0.9997
        self.alpha = 0.02
        self.greedy = False

    def action(self, state_type, state):
        # 0 - reload/shoot
        # 1234 - move toward/away, strafe left/right
        if state_type == 0:  # reloading
            return 0
        if numpy.random.random(1)[0] < self.epsilon and not self.greedy:  # act randomly
            return random.randint(0, 4)  # inclusive
        return numpy.argmax(self.q[state_type][state])  # argmax will give optimal action

    def update(self, states, actions, rewards):
        cnt = defaultdict(lambda: 0)
        for s, a in zip(states, actions):
            cnt[(s, a)] += 1
        G = 0
        for s, a, r in list(zip(states, actions, rewards))[::-1]:
            G = self.gamma * G + r
            self.q[s[0]][tuple(s[1:])][a] += self.alpha * (G - self.q[s[0]][tuple(s[1:])][a])


class ManualBot(Player):
    def __init__(self, init_pos):
        super().__init__(init_pos)

    def action(self, state_type, state):
        if state_type == 0:
            return 0
        if state[2] != 9:  # if enemy bullet coming
            return 3  # strafe away to safety
        if state[1] <= 10:  # too close, can die
            return 2
        if state_type == 1 and state[1] <= 15:  # no ammo and close
            return 2  # back up to safety
        if state_type == 1:  # reload
            return 0
        if state[0] == 2:  # if enemy reloading, fire
            return 0
        return 3

    def update(self, s, a, r):
        pass