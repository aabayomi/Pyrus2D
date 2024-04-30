import matplotlib.pyplot as plt
import numpy as np

# Extract the duration data from the 4th column
durations = [
    64, 101, 46, 163, 46, 33, 191, 242, 47, 44, 151, 92, 221, 243, 190, 69, 73, 76, 59, 254,
    40, 282, 59, 914, 398, 140, 443, 204, 78, 125, 425, 1945, 53, 443, 68, 39, 91, 53, 76, 152,
    174, 82, 65, 57, 130, 177, 101, 168, 26, 74, 66, 53, 49, 83, 59, 138, 79, 69, 31, 56,
    210, 80, 69, 88, 297, 174, 73, 157, 76, 70, 115, 141, 284, 120, 40, 273, 48, 76, 172, 50,
    100, 873, 40, 71, 104, 111, 42, 228, 69, 105, 52, 77, 230, 863, 86, 62, 72, 77, 77, 32,
    85, 63, 93, 62, 179, 114, 74, 36, 112, 112, 455, 47, 63, 51, 49, 111, 217, 60, 33, 87,
    89, 68, 157, 62, 183, 71, 179, 51, 119, 160, 48, 124, 232, 52, 115, 137, 42, 81, 165, 231,
    75, 192, 45, 157, 230, 92, 176, 51, 189, 140, 70, 152, 55, 90, 123, 88, 74, 214, 67, 196,
    51, 54, 622, 174, 58, 33, 60, 169, 90, 62, 65, 100, 59, 139, 691, 314, 522, 101, 302, 85,
    246, 154, 128, 73, 89, 165, 53, 111, 98, 49, 708, 613, 429, 87, 192, 362, 201, 85, 202, 97,
    65, 58, 163, 67, 85, 54, 48, 45, 76, 77, 75, 38, 63, 68, 557, 39, 220, 45, 53, 136,
    111, 192, 91, 56, 175, 660, 59, 58, 58, 59, 277, 56, 240, 209, 44, 93, 64, 47, 70, 47,
    111, 75, 45, 66, 75, 123, 123, 46, 352, 62, 164, 54, 53, 172, 123, 100, 77, 174, 54, 55,
    35, 184, 39, 71, 163, 108, 54, 527, 232, 167, 90, 98, 468, 1107, 714, 107, 65, 74, 66, 47,
    56, 62, 87, 103, 182, 58, 55, 120, 307, 62, 88, 140, 59, 74, 105, 56, 92, 511, 94, 73,
    96, 168, 55, 49, 81, 41, 127, 44, 59, 96, 340, 154, 41
]


# Bin the episodes by 50 and calculate the average duration for each bin
bin_size = 50
num_bins = len(durations) // bin_size
episode_bins = np.arange(bin_size // 2, len(durations), bin_size)
# duration_avgs = [np.mean(durations[i*bin_size:(i+1)*bin_size]) for i in range(num_bins+1)]
duration_avgs = [np.max(durations[i*bin_size:(i+1)*bin_size]) for i in range(num_bins)]
print(sum(durations)/len(durations))
# Create a line graph
plt.figure(figsize=(10, 6))
plt.plot(episode_bins, duration_avgs, marker='o', markersize=5, linestyle='-', linewidth=2)
plt.xlabel('Episode')
plt.ylabel('Performance Improvement')
plt.title(f'Maximum Duration per {bin_size} Episodes')
plt.xticks(episode_bins)
plt.xlim(0, len(durations))
plt.grid(True)
plt.show()