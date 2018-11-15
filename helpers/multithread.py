import concurrent.futures as cf
import subprocess
import os


def run_processes(commands, worker_count=4):

    with cf.ProcessPoolExecutor(max_workers=worker_count) as executer:
        for c in commands:
            executer.submit(run_batch, command=c)


def run_batch(command):
    subprocess.call([command], stdout=open(os.devnull, 'wb'), stderr=open(os.devnull, 'wb'))
    print('.', end='', flush=True)
