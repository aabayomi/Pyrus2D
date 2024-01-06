# import argparse
# from time import sleep
# import logging


# import base.main_keepaway_player as kp
# import base.main_coach as main_c
# import multiprocessing as mp


# takers_list = []

# takers = 2
# for i in range(2, takers + 2):
#     proc = mp.Process(target=kp.main, args=("takers", i, False), name="taker")
#     proc.start()
#     # takers_list.append(proc)
#     sleep(0.25)

# sleep(5)


# class QFunction:
#     def __init__(self, scope):
#         self.scope = scope
#         self.domain = [0, 1, 2]  # Simple domain for all variables

#     def __call__(self, *args):
#         return sum(args)  # Simple function that just sums the inputs


# def variable_elimination_thread(agent, lock):
#     with lock:
#         functions_involving_agent = [f for f in Qs if agent in f.scope]

#     # Define new function as max over the agent
#     def new_function(*args):
#         return max(f(*args) for f in functions_involving_agent)

#     max_values = max(
#         (new_function(*args), args)
#         for args in itertools.product(*(range(3) for _ in functions_involving_agent))
#     )

#     with lock:
#         # Write max values to shared memory
#         shared_memory[agent] = max_values


# n = 5  # Number of agents

# agents = [f"a{i}" for i in range(n)]

# Qs = [QFunction([agents[i], agents[(i + 1) % n]]) for i in range(n)]

# print(agents)
# for i in range(n):
#     print(Qs[i].scope)


# from threading import Thread, Lock
# import itertools


# class QFunction:
#     def __init__(self, scope):
#         self.scope = scope
#         self.domain = [0, 1, 2]  # Simple domain for all variables

#     def __call__(self, *args):
#         return sum(args)  # Simple function that just sums the inputs


# def variable_elimination_thread(agent, lock):
#     with lock:
#         functions_involving_agent = [f for f in Qs if agent in f.scope]
#         print(len(functions_involving_agent))
#         # for i in range(len(functions_involving_agent)):
#         #     print(functions_involving_agent[i].scope)

#     # Define new function as max over the agent
#     def new_function(*args):
#         return max(f(*args) for f in functions_involving_agent)

#     max_values = max(
#         (new_function(*args), args)
#         for args in itertools.product(*(range(3) for _ in functions_involving_agent))
#     )

#     with lock:
#         # Write max values to shared memory
#         shared_memory[agent] = max_values


# n = 4  # Number of agents

# agents = [f"a{i}" for i in range(n)]

# Qs = [QFunction([agents[i], agents[(i + 1) % n]]) for i in range(n)]

# for i in range(n):
#     if Qs[i].scope[0] == "a3" or Qs[i].scope[1] == "a3":
#         print(Qs[i].scope)
#     # print(Qs[i].scope)


# shared_memory = {}  # A thread-safe shared memory structure
# lock = Lock()


# threads = []

# for agent in agents:
#     thread = Thread(target=variable_elimination_thread, args=(agent, lock))
#     thread.start()
#     threads.append(thread)

# for thread in threads:
#     thread.join()


# print(shared_memory)


# import numpy as np
# import matplotlib.pyplot as plt
# import matplotlib.animation as animation

# # Set the random seed for reproducibility
# np.random.seed(0)

# # Initialize points
# A = np.random.rand(2) * 100
# B = np.random.rand(2) * 100
# C = np.random.rand(2) * 100


# def update_points(A, B, C):
#     # Choose a random direction to move in
#     direction = np.random.rand(2) - 0.5
#     direction /= np.linalg.norm(direction)  # Normalize to unit vector

#     # Choose a random distance to move
#     distance = np.random.rand() * 10

#     # Move points B and C, keeping A as the anchor
#     B += direction * distance
#     C += direction * distance

#     return A, B, C


# fig, ax = plt.subplots()


# def animate(i):
#     global A, B, C
#     A, B, C = update_points(A, B, C)
#     ax.clear()
#     ax.set_xlim([0, 100])
#     ax.set_ylim([0, 100])
#     ax.plot(*zip(A, B, C, A), marker="o")


# ani = animation.FuncAnimation(fig, animate, frames=100, interval=200)
# plt.show()


# import matplotlib.pyplot as plt
# import random
# import numpy as np


# class Triangle:
#     def __init__(self, p1, p2, p3):
#         self.p1 = np.array(p1, dtype=np.float64)
#         self.p2 = np.array(p2, dtype=np.float64)
#         self.p3 = np.array(p3, dtype=np.float64)

#     def move_point(self, point, new_pos):
#         """Move a point and adjust the other two to maintain triangle shape."""
#         delta = np.array(new_pos) - point
#         if np.array_equal(point, self.p1):
#             self.p1 = new_pos
#             self.p2 += delta
#             self.p3 += delta
#         elif np.array_equal(point, self.p2):
#             self.p2 = new_pos
#             self.p1 += delta
#             self.p3 += delta
#         elif np.array_equal(point, self.p3):
#             self.p3 = new_pos
#             self.p1 += delta
#             self.p2 += delta

#     def random_move(self):
#         """Randomly move one point."""
#         which_point = random.choice([self.p1, self.p2, self.p3])
#         new_x = which_point[0] + random.uniform(-1, 1)
#         new_y = which_point[1] + random.uniform(-1, 1)
#         self.move_point(which_point, (new_x, new_y))

#     def plot(self):
#         """Plot the triangle."""
#         plt.plot([self.p1[0], self.p2[0]], [self.p1[1], self.p2[1]], "ro-")
#         plt.plot([self.p2[0], self.p3[0]], [self.p2[1], self.p3[1]], "ro-")
#         plt.plot([self.p1[0], self.p3[0]], [self.p1[1], self.p3[1]], "ro-")
#         plt.xlim(-10, 10)
#         plt.ylim(-10, 10)
#         plt.gca().set_aspect("equal", adjustable="box")
#         plt.draw()
#         plt.pause(0.1)
#         plt.clf()


# # Initialize a triangle
# triangle = Triangle((0, 0), (1, 0), (0.5, 0.866))

# for _ in range(50):
#     triangle.plot()
#     triangle.random_move()

# plt.show()


# import numpy as np
# import matplotlib.pyplot as plt
# from scipy.spatial import ConvexHull

# def generate_random_points(n, x_range, y_range):
#     """Generate n random points within given x and y range."""
#     x_coords = np.random.uniform(x_range[0], x_range[1], n)
#     y_coords = np.random.uniform(y_range[0], y_range[1], n)
#     return np.array(list(zip(x_coords, y_coords)))

# def plot_convex_hull(points):
#     """Calculate and plot the convex hull for a set of points."""
#     hull = ConvexHull(points)

#     # Plotting the convex hull and the points
#     plt.plot(points[:, 0], points[:, 1], 'o')
#     for simplex in hull.simplices:
#         plt.plot(points[simplex, 0], points[simplex, 1], 'g-')

#     plt.gca().set_aspect('equal', adjustable='box')
#     plt.show()

# # Define the rectangle boundaries
# x_range = (0, 10)
# y_range = (0, 5)

# # Generate random points and plot the convex hull
# points = generate_random_points(100, x_range, y_range)
# plot_convex_hull(points)

# import numpy as np
# import matplotlib.pyplot as plt
# import random


# def are_collinear(p1, p2, p3):
#     """Check if three points are collinear."""
#     area = p1[0] * (p2[1] - p3[1]) + p2[0] * (p3[1] - p1[1]) + p3[0] * (p1[1] - p2[1])
#     return abs(area) < 1e-6


# def adjust_point(p):
#     """Slightly adjust a point's position."""
#     return (p[0] + random.uniform(-0.1, 0.1), p[1] + random.uniform(-0.1, 0.1))


# def random_move(p, x_range, y_range):
#     """Move a point randomly within given ranges."""
#     return (
#         np.clip(p[0] + random.uniform(-1, 1), x_range[0], x_range[1]),
#         np.clip(p[1] + random.uniform(-1, 1), y_range[0], y_range[1]),
#     )


# def plot_points(points):
#     """Plot the points and the triangle they form."""
#     plt.plot(points[:, 0], points[:, 1], "o")
#     plt.plot(
#         [points[0][0], points[1][0], points[2][0], points[0][0]],
#         [points[0][1], points[1][1], points[2][1], points[0][1]],
#         "g-",
#     )
#     plt.xlim(0, 10)
#     plt.ylim(0, 5)
#     plt.gca().set_aspect("equal", adjustable="box")
#     plt.draw()
#     plt.pause(0.1)
#     plt.clf()


# # Define the rectangle boundaries and initialize points
# x_range = (0, 10)
# y_range = (0, 5)
# points = np.array([(2, 2), (8, 2), (5, 4.5)])

# for _ in range(100):
#     # Move each point randomly
#     for i in range(3):
#         points[i] = random_move(points[i], x_range, y_range)

#     # Check and adjust if points become collinear
#     while are_collinear(points[0], points[1], points[2]):
#         points[random.randint(0, 2)] = adjust_point(points[random.randint(0, 2)])

#     plot_points(points)

# plt.show()

import numpy as np
import matplotlib.pyplot as plt
import random
import threading
import queue

# Variables
x_range = (0, 10)
y_range = (0, 5)

# Functions
def are_collinear(p1, p2, p3):
    area = p1[0]*(p2[1] - p3[1]) + p2[0]*(p3[1] - p1[1]) + p3[0]*(p1[1] - p2[1])
    return abs(area) < 1e-6

def adjust_point(p):
    return (p[0] + random.uniform(-0.1, 0.1), p[1] + random.uniform(-0.1, 0.1))

def random_move(p, x_range, y_range):
    return (np.clip(p[0] + random.uniform(-1, 1), x_range[0], x_range[1]),
            np.clip(p[1] + random.uniform(-1, 1), y_range[0], y_range[1]))

def plot_points(points):
    plt.plot(points[:, 0], points[:, 1], 'o')
    plt.plot([points[0][0], points[1][0], points[2][0], points[0][0]], 
             [points[0][1], points[1][1], points[2][1], points[0][1]], 'g-')
    plt.xlim(0, 10)
    plt.ylim(0, 5)
    plt.gca().set_aspect('equal', adjustable='box')
    plt.draw()
    plt.pause(0.1)
    plt.clf()

def point_thread(point, q):
    # Each point moves randomly and then puts its new coordinates in the queue
    new_point = random_move(point, x_range, y_range)
    q.put(new_point)

# Initialize points
points = np.array([(2, 2), (8, 2), (5, 4.5)])

for _ in range(100):
    q = queue.Queue()
    threads = []
    
    # Start threads for each point
    for point in points:
        t = threading.Thread(target=point_thread, args=(point, q))
        threads.append(t)
        t.start()
    
    # Wait for all threads to complete
    for t in threads:
        t.join()
    
    # Retrieve new points from the queue
    for i in range(3):
        points[i] = q.get()
    
    # Check and adjust collinearity
    while are_collinear(points[0], points[1], points[2]):
        points[random.randint(0, 2)] = adjust_point(points[random.randint(0, 2)])
    
    plot_points(points)

plt.show()
