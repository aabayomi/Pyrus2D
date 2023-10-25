import multiprocessing
import time

# import base.main_keepaway_player as kp
# import base.main_coach as main_c
import multiprocessing as mp

def print_numbers(process_num, shared_values, lock, event):
    while True:
        with lock:
            shared_values[process_num] += 1
            current_values = list(shared_values)
        event.set()  # Signal that the numbers are ready to print

        # Wait for all processes to finish updating
        event.wait()

        # Print the current values as a tuple
        print(current_values)

        event.clear()  # Clear the event for the next iteration


# if __name__ == "__main__":
#     # Create shared variables and synchronization objects
#     manager = multiprocessing.Manager()
#     shared_values = manager.list([0, 0, 0])
#     lock = manager.Lock()
#     event = multiprocessing.Event()

#     # Create three processes
#     processes = []
#     for i in range(3):
#         process = multiprocessing.Process(
#             target=print_numbers, args=(i, shared_values, lock, event)
#         )
#         processes.append(process)

#     # Start the processes
#     for process in processes:
#         process.start()

#     # Wait for a moment to allow some printing
#     time.sleep(5)

#     # Terminate the processes (for demonstration purposes; use appropriate termination logic)
#     for process in processes:
#         process.terminate()

import threading

if __name__ == '__main__':
    manager = multiprocessing.Manager()
    shared_values = manager.list([0, 0, 0])
    # lock = manager.Lock()
    event = multiprocessing.Event()

    print(shared_values)


    num_agents = 3
    
    # Initialize a barrier for synchronization
    lock = threading.Barrier(num_agents)
    
    # Initialize agents
    # agents = [Agent(barrier) for _ in range(num_agents)]
    
    # Create and start threads for each agent
    # agent_threads = [threading.Thread(target=kp.main, args=("keepers", i, False,shared_values,manager,lock,event), name="keeper") for i in range(num_agents)]
    # for thread in agent_threads:
    #     thread.start()

    
    # Wait for threads to finish
    # for thread in agent_threads:
    #     thread.join()

    # Create three processes
    processes = []
    for i in range(3):
        process = multiprocessing.Process(
            target=print_numbers, args=(i, shared_values, lock, event)
        )
        processes.append(process)


    # keepers = 3
    # for i in range(2, keepers + 2):
    #     proc = multiprocessing.Process(target=kp.main, args=("keepers", i, False,shared_values,manager,lock,event), name="keeper")
    #     proc.start()
    #     processes.append(proc)

    # time.sleep(0.25)

    # takers_list = []

    # takers = 2
    # for i in range(2, takers + 2):
    #     # proc = mp.Process(target=kp.main, args=("takers", i, False), name="taker")
    #     proc = mp.Process(target=kp.main, args=("takers", i, False,shared_values,manager,lock,event), name="takers")
    #     proc.start()
    #     # takers_list.append(proc)
    #     time.sleep(0.25)


    # Start the processes
    for process in processes:
        process.start()

    # Wait for a moment to allow some printing
    # time.sleep(5)

    # Terminate the processes (for demonstration purposes; use appropriate termination logic)
    # for process in processes:
    #     process.terminate()

