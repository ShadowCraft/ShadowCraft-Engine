# Experimental file to support multithreading for some calculations

import copy
import multiprocessing
import queue
import threading

class CalculatorThread(threading.Thread):
    def __init__(self, calculator, queue):
        threading.Thread.__init__(self)
        self.calculator = copy.copy(calculator)
        self.calculator.stats = copy.deepcopy(calculator.stats)
        #self.calculator.talents = copy.deepcopy(calculator.talents)
        #self.calculator.traits = copy.deepcopy(calculator.traits)
        #self.calculator.buffs = copy.deepcopy(calculator.buffs)
        self.queue = queue
        self.results = {}

    def run(self):
        while True:
            item = [self.queue.get()]
            self.results.update(self.calculator.get_other_ep(item))
            self.queue.task_done()

    def get_results(self):
        return self.results

def get_ep_multithreaded(calculator, items):
    q = queue.Queue()
    threads = []
    for i in range(multiprocessing.cpu_count()):
        t = CalculatorThread(calculator, q)
        t.daemon = True
        t.start()
        threads.append(t)
    for item in items:
        q.put(item)
    q.join()
    results = {}
    for t in threads:
        results.update(t.get_results())
    return results

#TODO get_upgrades_ep_fast_multithreaded():
