import time


def benchmark(func):
    async def wrapper(*args, **kwargs):
        start = time.time()
        return_value = await func(*args, **kwargs)
        end = time.time()
        print('[*] Time: {} sec.'.format(end - start))
        return return_value
    return wrapper
