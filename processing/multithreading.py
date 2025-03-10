import time
import random
from concurrent.futures import ThreadPoolExecutor

def worker(number,id, extra_info):
    result = number **2

    print(f"Showing test id: {id}")
    print(f"Calculating square root of {number}")
    print(f"Showing extra info: {extra_info}")

    time.sleep(3)
    print(result)
    return result

start_time = time.time()
with ThreadPoolExecutor(max_workers=50) as executor:
    futures_ = [executor.submit(worker, i, 9, 'Extra_info') for i in range(50)]
end_time = time.time()

duration = end_time - start_time

print(f"Task completed in {duration} seconds")