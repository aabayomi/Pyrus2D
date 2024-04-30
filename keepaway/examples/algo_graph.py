import matplotlib.pyplot as plt

# Define the data
algorithms = ['SARSA + TC', 'Random', 'DynaQ + TC', 'DynaQ+ + TC', 'SARSA + CVF', 'DynaQ + CVF', 'PPO', 'DynaQ+ + CVF']
time_steps = [60, 77, 80, 84, 107, 124, 140, 147]

# Create the bar graph
fig, ax = plt.subplots(figsize=(8, 6))
ax.bar(algorithms, time_steps)

# Customize the graph
ax.set_xlabel('Algorithms')
ax.set_ylabel('Average Duration')
ax.set_title('Comparison of Reinforcement Learning Algorithms')

# Add labels to the bars
for i, v in enumerate(time_steps):
    ax.text(i, v + 1, str(v), ha='center')

# Display the graph
plt.tight_layout()
plt.show()