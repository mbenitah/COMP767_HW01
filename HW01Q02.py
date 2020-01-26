import numpy as np
import gym
import argparse
import matplotlib.pyplot as plt
from HW01Q01 import plot_line_variance

SEED = None
RUNS = 5
STEPS_PER_RUN = 100
TRAINING_EPISODES = 10
TESTING_EPISODES = 5


# #############################################################################
#
# Parser
#
# #############################################################################


def get_arguments():
    def _str_to_bool(s):
        '''Convert string to boolean (in argparse context)'''
        if s.lower() not in ['true', 'false']:
            raise ValueError('Argument needs to be a '
                             'boolean, got {}'.format(s))
        return {'true': True, 'false': False}[s.lower()]

    parser = argparse.ArgumentParser(description='Creating a k-armed bandit.')
    parser.add_argument('--seed', type=int, default=SEED,
                        help='Seed for the random number generator.')
    parser.add_argument('-n', '--runs', type=int, default=RUNS,
                        help='Number of runs to be executed. Default: '
                        + str(RUNS))
    parser.add_argument('-s', '--steps', type=int, default=STEPS_PER_RUN,
                        help='Number of steps in each run. One run step is '
                        'the ensemble of training episodes and testing '
                        'episodes. Default: ' + str(STEPS_PER_RUN))
    parser.add_argument('--training_steps', type=int,
                        default=TRAINING_EPISODES,
                        help='Number of runs to be executed. Default: '
                        + str(TRAINING_EPISODES))
    parser.add_argument('--testing_steps', type=int, default=TESTING_EPISODES,
                        help='Number of runs to be executed. Default: '
                        + str(TESTING_EPISODES))

    return parser.parse_args()


# #############################################################################
#
# Plotting
#
# #############################################################################


def plot2(title, cumulative_reward, timesteps):
    '''Creates the two required plots: cumulative_reward and number of timesteps
    per episode.'''

    fig, axs = plt.subplots(nrows=1, ncols=2,
                            constrained_layout=True,
                            figsize=(10, 3))

    fig.suptitle(title, fontsize=12)

    plot_line_variance(axs[0], cumulative_reward)
    axs[0].set_title('Cumulative reward')

    plot_line_variance(axs[1], timesteps)
    axs[1].set_title('Timesteps per episode')



# #############################################################################
#
# Policy
#
# #############################################################################


class Policy():
    def __init__(self, env, gamma=1, tol=1e-6):
        self.env = env
        self.gamma = gamma
        self.tol = tol

        self.counter = 0

        if not isinstance(env.observation_space, gym.spaces.Discrete):
            raise NotImplementedError

        self.V = np.zeros(env.observation_space.n)
        self.pi = np.zeros(env.observation_space.n, dtype=int)

        for s in range(env.observation_space.n):
            self.pi[s] = env.action_space.sample()

    def eval(self, bValueIteration=False):
        '''Evaluates the policy value for each state s in
        env.observation_space'''
        delta = np.infty
        i = 0

        self.counter += 1
        while delta > self.tol:
            delta = 0
            i += 1
            for s in range(self.env.observation_space.n):
                V_old = self.V[s]
                self.V[s] = self._getvalue(s, self.pi[s])
                delta = max(delta, np.abs(V_old - self.V[s]))
        print('Policy evaluation #{} completed in {} steps.\n\nV: {}\n'.format(self.counter, i, self.V))
        self.iterate()
        return self.V, self.pi

    def iterate(self):
        '''Iterates policy evaluation to find an optimal policy and
        optimal value. The algorithm keeps updating the policy until
        it finds a stable policy that cannot be further improved (according
        to the defined tolerance).

        list of outputs:
        V:      optimal value of the policy for each state s in
                env.observation_space
        pi:     the optimal action for each state s'''

        stable = True
        for s in range(self.env.observation_space.n):
            old_action = self.pi[s]

            values = []
            for action in range(self.env.action_space.n):
                values.append(self._getvalue(s, action))

            self.pi[s] = np.argmax(values)
            # self.pi[s] = np.argmax([self._getvalue(s, action) for action in range(self.env.action_space.n)])

            # print('state {} : {}'.format(s, values))

            if old_action != self.pi[s]:
                stable = False
        print('pi: {}'.format(self.pi))

        if not stable:
            self.eval()

    def value_iteration(self):
        '''Returns an estimation of the optimal policy by performing
        only one sweep (one update of each state) of policy evaluation.

        output: an estimation of the optimal policy'''
        # self.eval()

        # for s in range(self.env.observation_space.n):
        #     self.pi[s] = np.argmax([self._getvalue(s, action) for action in self.env.action_space])
        delta = np.infty
        i = 0

        while delta > self.tol:
            delta = 0
            i += 1
            for s in range(self.env.observation_space.n):
                V_old = self.V[s]
                self.V[s] = np.max([self._getvalue(s, action) for action in range(self.env.action_space.n)])
                delta = max(delta, np.abs(V_old - self.V[s]))

        for s in range(self.env.observation_space.n):
            self.pi[s] = np.argmax([self._getvalue(s, action) for action in range(self.env.action_space.n)])

        print('Finished value iteration in {} steps.'.format(i))

        return self.V, self.pi


    def _getvalue(self, state, action):
        '''For a given state and action, returns the value of that
        state according to the current policy iteration.'''

        # for a given state and action, P[state][action] returns a list of
        # tuples in the form (p, s1, r, b) containing respectively the
        # probability, state, return and boolean for all possible states s1
        # originating from s. The boolean determines if the state s1 is
        # terminal or not.
        p, s1, r, _ = zip(*self.env.P[state][action])

        # convert tuples to arrays
        p = np.array(p)
        s1 = np.array(s1, dtype=int)
        r = np.array(r)
        # b = np.array(b, dtype=bool)

        return np.sum(p * (r + self.gamma * self.V[s1]))


def render_policy(env, pi):
    print('=' * 80)
    print('Initial state')
    print('=' * 80)
    env.render()

    cumulative_reward = 0
    for i, action in enumerate(pi):
        print('=' * 80)
        print('Step {}'.format(i+1))
        print('=' * 80)
        observation, reward, done, info = env.step(action)
        cumulative_reward += reward
        env.render()
        if done:
            print("Episode finished after {} timesteps".format(i+1))
            break

    print('Cumulative reward: {}'.format(cumulative_reward))
    env.close()

# #############################################################################
#
# Main
#
# #############################################################################


def main():

    args = get_arguments()

    # sets the seed for random experiments
    np.random.seed(args.seed)

    # env = gym.make('FrozenLake-v0')
    env = gym.make('FrozenLake8x8-v0')
    # env = gym.make('Taxi-v3')
    env.reset()

    pol = Policy(env, gamma=0.9)
    V, pi = pol.eval()
    print('Done. ****************')

    valuepol = Policy(env, gamma=0.9)
    V_val, pi_val = valuepol.value_iteration()
    print('V: {}\n\npi:{}'.format(V_val, pi_val))

    render_policy(env, pi_val)
    print(pi==pi_val)


if __name__ == '__main__':
    main()

# for i_episode in range(20):
#     observation = env.reset()
#     for t in range(100):
#         env.render()
#         print(observation)
#         action = env.action_space.sample()
#         observation, reward, done, info = env.step(action)
#         if done:
#             print("Episode finished after {} timesteps".format(t+1))
#             break

# for i in range(env.observation_space.n):
#     print('observation_space: {}'.format(i))
# print('action_space: {}'.format(env.action_space))