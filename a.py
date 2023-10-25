# import base.main_keepaway_player as kp
# import base.main_coach as main_c
# import multiprocessing as mp
# from time import sleep
import time

# players = []
# from lib.player.world_model import WorldModel

# keepers = 3
# for i in range(2, keepers + 2):
#     proc = mp.Process(target=kp.main, args=("keepers", i, False), name="keeper")
#     proc.start()
#     players.append(proc)
#     sleep(0.25)

# sleep(5)


# class Agent():
#     def __init__(
#         self):

#         self._current_time: GameTime = GameTime()

#     def run(self):
#         last_time_rec = time.time()
#         waited_msec: int = 0
#         timeout_count: int = 0
#         while self._client.is_server_alive():
#             # with self._lock:
#             length, message, server_address = self._client.recv_message()
#             if len(message) == 0:
#                 waited_msec += team_config.SOCKET_INTERVAL
#                 timeout_count += 1
#                 if time.time() - last_time_rec > 3:
#                     self._client.set_server_alive(False)
#                     break
#             else:
#                 self.parse_message(message.decode())
#                 last_time_rec = time.time()
#                 waited_msec = 0
#                 timeout_count = 0

#             if ServerParam.i().synch_mode():
#                 if self.think_received():
#                     self.action()
#                     self.debug_players()
#                     self._think_received = False
#             else:
#                 if self.is_decision_time(timeout_count, waited_msec) or (
#                     self._last_decision_time != self._current_time
#                     and self.world().see_time() == self._current_time
#                 ):
#                     self.action()
#             self.flush_logs()
#             if len(message) > 0:
#                 print(pt.get())
#         self.send_bye_command()


# from concurrent import futures
# import functools


# class RunParallel(object):
#     """Run all funcs in parallel."""

#     def __init__(self, timeout=None):
#         self._timeout = timeout
#         self._executor = None
#         self._workers = 0

#     def run(self, funcs):
#         """Run a set of functions in parallel, returning their results.

#         Make sure any function you pass exits with a reasonable timeout. If it
#         doesn't return within the timeout or the result is ignored due an exception
#         in a separate thread it will continue to stick around until it finishes,
#         including blocking process exit.

#         Args:
#           funcs: An iterable of functions or iterable of args to functools.partial.

#         Returns:
#           A list of return values with the values matching the order in funcs.

#         Raises:
#           Propagates the first exception encountered in one of the functions.
#         """
#         funcs = [f if callable(f) else functools.partial(*f) for f in funcs]
#         if len(funcs) == 1:  # Ignore threads if it's not needed.
#             return [funcs[0]()]
#         if len(funcs) > self._workers:  # Lazy init and grow as needed.
#             self.shutdown()
#             self._workers = len(funcs)
#             while True:
#                 try:
#                     # Temporary workaround for "<frozen importlib._bootstrap>", line 110.
#                     # Race condition on import of ThreadPoolExecutor.
#                     self._executor = futures.ThreadPoolExecutor(self._workers)
#                     break
#                 except KeyError:
#                     pass
#         futs = [self._executor.submit(f) for f in funcs]
#         done, not_done = futures.wait(futs, self._timeout, futures.FIRST_EXCEPTION)
#         # Make sure to propagate any exceptions.
#         for f in done:
#             if not f.cancelled() and f.exception() is not None:
#                 if not_done:
#                     # If there are some calls that haven't finished, cancel and recreate
#                     # the thread pool. Otherwise we may have a thread running forever
#                     # blocking parallel calls.
#                     for nd in not_done:
#                         nd.cancel()
#                     self.shutdown(False)  # Don't wait, they may be deadlocked.
#                 raise f.exception()
#         # Either done or timed out, so don't wait again.
#         return [f.result(timeout=0) for f in futs]

#     def shutdown(self, wait=True):
#         if self._executor:
#             self._executor.shutdown(wait)
#             self._executor = None
#             self._workers = 0

#     def __del__(self):
#         self.shutdown()


# def main():
#     """Main function."""

#     import base.main_keepaway_player as kp
#     from base.keepaway_player import KeepawayPlayer
#     import multiprocessing
#     import threading

#     print("Starting")
#     rp = RunParallel()
#     # print(rp.run([time.sleep(0), time.sleep(0), time.sleep(0)]))

#     manager = multiprocessing.Manager()
#     shared_values = manager.list([0, 0, 0])
#     # lock = manager.Lock()
#     event = multiprocessing.Event()
#     num_agents = 3

#     # Initialize a barrier for synchronization
#     lock = threading.Barrier(num_agents)
#     team_name = "keepers"
#     agents = []
#     for i in range(2, 3 + 2):
#         # p = kp.main("keepers", i, False, shared_values, manager, lock, event)
#         p = KeepawayPlayer(team_name,shared_values, manager, lock, event)
#         agents.append(p)

#     print(agents)
#     print(rp.run(a.run for a in agents))
#     print("Done")

# main()


# import multiprocessing
# import time

# def count(barrier, count_list, index):
#     # Wait for all processes to be ready to start
#     barrier.wait()

#     # Each process will increment its count in count_list by 1, 100 times
#     for i in range(1, 101):
#         with count_list.get_lock():
#             count_list[index] += 1
#             print(list(count_list))

# if __name__ == '__main__':
#     # Create a Barrier for three processes
#     barrier = multiprocessing.Barrier(3)

#     # Create a shared list to hold the count for each process
#     count_list = multiprocessing.Array('i', [0, 0, 0])

#     # Create and start three processes, passing the index of count_list each should increment
#     processes = []
#     for i in range(3):
#         p = multiprocessing.Process(target=count, args=(barrier, count_list, i))
#         processes.append(p)
#         p.start()

#     # Wait for all processes to finish
#     for p in processes:
#         p.join()


# import multiprocessing
# import time

# def worker(barrier):
#     print(f"Process {multiprocessing.current_process().name} doing some work")
#     time.sleep(2)  # Simulate work
#     print(f"Process {multiprocessing.current_process().name} waiting at barrier")
#     barrier.wait()
#     # try:
#     #     barrier.wait()
#     # except multiprocessing.BrokenBarrierError:
#     #     print(f"Process {multiprocessing.current_process().name} released from barrier")

# def main():
#     barrier = multiprocessing.Barrier(3)
#     processes = [multiprocessing.Process(target=worker, args=(barrier,)) for _ in range(3)]

#     for p in processes:
#         p.start()

#     while barrier.n_waiting < 3:
#         print("waiting inside the barrier")
#         time.sleep(0.1)  # Poll the barrier to check if all processes are waiting

#     print("All sub-processes are waiting at the barrier. Releasing...")
#     barrier.reset()  # Reset the barrier to release all waiting processes

#     for p in processes:
#         p.join()  # Wait for all processes to complete

#     print("All sub-processes completed.")

# if __name__ == '__main__':
#     main()


# import multiprocessing
# import time

# def worker_function(worker_num, barrier):
#     print(f"Worker {worker_num} started.")
#     time.sleep(2)  # Simulate some work
#     print(f"Worker {worker_num} reached the wait point.")
#     barrier.wait()  # Wait for all processes to reach this point
#     print(f"Worker {worker_num} resumed.")

# if __name__ == "__main__":
#     # Create a Barrier to synchronize the workers and main process
#     barrier = multiprocessing.Barrier(4)  # Main process + 3 workers

#     # Create 3 worker processes
#     workers = []
#     for i in range(3):
#         worker = multiprocessing.Process(target=worker_function, args=(i + 1, barrier))
#         workers.append(worker)
#         worker.start()

#     # Simulate main process doing some work
#     time.sleep(10)
#     print(workers)

#     # Main process also waits at the barrier
#     barrier.wait()

#     # Wait for all worker processes to finish
#     for worker in workers:
#         worker.join()

#     print("Main process completed.")



import time
from multiprocessing import Process, Event

def subprocess_func(proc_id, event_to_set, event_to_wait):
    # Let's simulate a condition where any process (randomly chosen here) can set the wait event
    if proc_id == 0:  # In this case, process with ID 0 sets the event, but you can change this
        print(f"Subprocess {proc_id}: Setting the wait event for other subprocesses.")
        event_to_set.set()

    print(f"Subprocess {proc_id}: Waiting for event from another subprocess...")
    event_to_set.wait()  # Every subprocess waits for the event to be set

    print(f"Subprocess {proc_id}: Waiting for main process event...")
    event_to_wait.wait()
    print(f"Subprocess {proc_id}: Woken up by main process!")

if __name__ == "__main__":
    event_from_subprocess = Event()  # To be set by one of the subprocesses and waited on by others
    main_process_event = Event()     # To be set by main process to wake up all subprocesses

    processes = []

    # Create and start subprocesses using a for loop
    for i in range(3):  # 3 subprocesses
        p = Process(target=subprocess_func, args=(i, event_from_subprocess, main_process_event))
        processes.append(p)
        p.start()

    # Give enough time for subprocesses to start and print their messages
    time.sleep(2)

    # Main process wakes up all subprocesses
    print("Main Process: Waking up all subprocesses!")
    main_process_event.set()

    # Wait for all subprocesses to complete
    for p in processes:
        p.join()

    print("Main Process: All subprocesses have finished!")
