import time
import itertools
import requests
import multiprocessing
from rubik.cube import Cube
from concurrent.futures import ProcessPoolExecutor, as_completed

# Setup
solved_cube = lambda: Cube('OOOOOOOOOYYYWWWGGGBBBYYYWWWGGGBBBYYYWWWGGGBBBRRRRRRRRR')
BASE_URL = 'http://localhost:8000/sequences/'
MOVES = ['R', 'Ri', 'L', 'Li', 'U', 'Ui', 'D', 'Di', 'F', 'Fi', 'B', 'Bi']

# Configurable throttle (in seconds)
THROTTLE_DELAY = 0.05  # 50ms

def generate_move_sequences(max_length=1):
    for length in range(1, max_length + 1):
        for sequence in itertools.product(MOVES, repeat=length):
            yield list(sequence)


def compute_order(sequence):
    cube = solved_cube()
    count = 0
    while True:
        count += 1
        for move in sequence:
            getattr(cube, move)()
        if cube.is_solved():
            return count


def already_processed(sequence):
    sequence_str = ', '.join(sequence)
    try:
        r = requests.get(BASE_URL + sequence_str)
        time.sleep(THROTTLE_DELAY)
        return r.status_code == 200
    except requests.RequestException:
        return False

def store_sequence(sequence, order):
    sequence_str = ', '.join(sequence)
    try:
        requests.post(BASE_URL + 'new/', data={'sequence': sequence_str, 'order': order})
        time.sleep(THROTTLE_DELAY)
    except requests.RequestException:
        pass

def worker(sequence):
    if already_processed(sequence):
        return None

    order = compute_order(sequence)
    store_sequence(sequence, order)
    return sequence, order

def run_parallel(max_length=3):
    sequence_gen = generate_move_sequences(max_length)
    print('Starting process pool')

    with ProcessPoolExecutor(max_workers=multiprocessing.cpu_count()) as executor:
        futures = []
        for _ in range(multiprocessing.cpu_count()):
            try:
                sequence_list = next(sequence_gen)
                futures.append(executor.submit(worker, sequence_list))
            except StopIteration:
                break

        print('Looping sequences')
        while futures:
            for future in as_completed(futures):
                futures.remove(future)
                result = future.result()
                if result:
                    seq, order = result
                    print(f"✔ Sequence: {seq} → Order: {order}")

                try:
                    next_seq = next(sequence_gen)
                    futures.append(executor.submit(worker, next_seq))
                except StopIteration:
                    continue


if __name__ == '__main__':
    # move_sequences = generate_move_sequences(2)
    run_parallel(max_length=1)
