import asyncio
import aiohttp
import time
import random
import requests
start = time.time()

async def get(url):
    session = aiohttp.ClientSession()
    header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.164 Safari/537.36 Edg/91.0.864.71'}
    session.headers.update(header)

    response = await session.get(url)
    randomtime = random.randint(1,5)
    time.sleep(randomtime)
    
    # todo: 设置超时时间---try except循环，换header、换ip
    result = await response.text()
    session.close()
    return result

async def request():
    url = 'https://www.tripadvisor.in/'
    print('Waiting for', url)
    result = await get(url)
    print('Get response from', url)


url = 'https://www.tripadvisor.in/'

header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.164 Safari/537.36 Edg/91.0.864.71'}
html = requests.get(url,headers = header).text.replace('<!--red_beg-->','').replace('<!--red_end-->','').replace('<em>','').replace('</em>','')
print('Get response from', url)


tasks = [asyncio.ensure_future(request()) for _ in range(5)]
loop = asyncio.get_event_loop()
loop.run_until_complete(asyncio.wait(tasks))

end = time.time()
print('Cost time:', end - start)