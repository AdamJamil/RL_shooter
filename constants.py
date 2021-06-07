draw_offset = (800 - 500) / 2

height, width = 500, 500
speed = (height / 200) * 5
bullet_speed = 2 * speed
min_pos = [width / 10, height / 10]
max_pos = [9 * width / 10, 9 * height / 10]
player_radius = 10
bullet_radius = 4
reload_frames = 3

strafe_reward = 0.0
forward_reward = 0.0
survive_reward = 0.01
dist_mult_penalty = -0.01

lose_penalty = -2
win_reward = 1
time_out_penalty = -0.5
