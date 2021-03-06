import random

import matplotlib.pyplot as plt
import numpy as np

from htm_rl.gridworld_agent.agent import Agent
from htm_rl.gridworld_agent.list_sdr_encoder import ListSdrEncoder, Dim2d
from htm_rl.gridworld_agent.minigrid import make_minigrid
from htm_rl.gridworld_agent.planner import Planner
from htm_rl.gridworld_agent.sar import Sar, SarSuperpositionFormatter
from htm_rl.gridworld_agent.sar_sdr_encoder import SarSdrEncoder
from htm_rl.representations.int_sdr_encoder import IntSdrEncoder
from htm_rl.representations.temporal_memory import TemporalMemory


def render_env(env, render: bool, pause: float = None):
    if not render:
        return

    plt.imshow(env.render('rgb_array'))
    if pause is None or pause < .01:
        plt.show(block=True)
    else:
        plt.show(block=False)
        plt.pause(.1)


def print_debug_sar(sar, encoder, sar_formatter):
    indices = encoder.encode(sar)
    print(encoder.format(indices))
    sar_superposition = encoder.decode(indices)
    print(sar_formatter.format(sar_superposition))


def train_for(n_steps, observation, reward, a_ind, print_enabled):
    for _ in range(n_steps):
        if np.random.rand() < .2:
            action = np.random.choice(3)
        else:
            action = actions[a_ind % len(actions)]
        a_ind += 1

        render_env(env, render, pause)
        sar = Sar(observation, action, reward)
        proximal_input = encoder.encode(sar)
        agent.train_one_step(proximal_input, print_enabled)
        # print_debug_sar(sar, encoder, sar_formatter)

        next_observation, reward, done, info = env.step(action)
        if reward > 0:
            reward = 1
            print("===")
        # obs_sdr = encode_data(merge_data(obs, action, reward))

        observation = next_observation

        if done:
            action = np.random.choice(3) # any next action
            render_env(env, render, pause)
            sar = Sar(observation, action, reward)
            proximal_input = encoder.encode(sar)
            agent.train_one_step(proximal_input, print_enabled)
            # print_debug_sar(sar, encoder, sar_formatter)

            a_ind = 0
            observation = env.reset()
            agent.tm.reset()


if __name__ == '__main__':
    plt.figure(figsize=(2.5, 2.5))
    random.seed(1337)
    np.random.seed(1337)

    size, view_size = 5, 3
    env = make_minigrid(size, view_size)
    n_dims = Dim2d(view_size, view_size)

    k = (size - 2 - 1) // 2 + 1
    actions, a_ind = ([2, 0, 1, 2, 1, 0] * k + [1, 2, 1] + [2, 0, 1, 2, 1, 0] * k + [0, 2, 0])*k, 0
    observation, reward, done = env.reset(), 0, False

    encoder = SarSdrEncoder((
        ListSdrEncoder(IntSdrEncoder('state_elem', 4, 4, 3), n_dims),
        IntSdrEncoder('action', 3, 5, 4),
        IntSdrEncoder('reward', 2, 5, 4)
    ))
    sar_formatter = SarSuperpositionFormatter(n_dims.rows, n_dims.cols)

    activation_threshold = encoder.activation_threshold
    learning_threshold = int(0.66*activation_threshold)
    print(encoder.total_bits, activation_threshold, learning_threshold)

    tm = TemporalMemory(
        n_columns=encoder.total_bits,
        cells_per_column=10,
        activation_threshold=activation_threshold, learning_threshold=learning_threshold,
        initial_permanence=.5, connected_permanence=.5,
        maxNewSynapseCount=int(1.1 * encoder.value_bits)
    )
    agent = Agent(tm, encoder, sar_formatter.format)

    render, pause = False, .1
    for _ in range(40):
        train_for(40, observation, reward, 0, False)
        tm.reset()
        observation = env.reset()
        reward = 0

    # train_for(10, observation, reward, 10, True)

    initial_sar = Sar(observation, 2, 0)
    initial_proximal_input = encoder.encode(initial_sar)
    # agent.predict_cycle(initial_proximal_input, 20, True)

    planner = Planner(agent, 10, print_enabled=True)
    planner.plan_actions(initial_sar)
