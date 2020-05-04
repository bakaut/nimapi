from aiohttp import web
import json
import rtsp
import time
import cv2
import numpy as np
import argparse
import asyncio


async def check_image_blur(img, low_threshold=100, high_threshold=10000):
    if img is None:
        return False
    gray = cv2.cvtColor(np.array(img), cv2.COLOR_BGR2GRAY)
    blur_value = cv2.Laplacian(gray, cv2.CV_64F).var()
    return low_threshold < blur_value < high_threshold


async def check_image(addr, sleep_time=2):
    client = rtsp.Client(rtsp_server_uri=addr)
    result = False
    for i in range(3):  # необходимо не срабатывать кадры, где камера двигается
        await asyncio.sleep(sleep_time)
        if await check_image_blur(client.read()):
            result = True
            break
    return result


async def handle(request):
    request_json = await request.post()
    response_obj = {
        'id': request_json.get('id', ''),
        'check': request_json.get('check', ''),
        'ip': request_json.get('ip', ''),
        'ip_flow': request_json.get('ip_flow', ''),
        'url': request_json.get('url', ''),
        'ts': str(int(time.time()))
    }
    response_obj['result'] = await check_image('rtsp://' + response_obj.get('ip_flow'))

    return web.Response(text=json.dumps(response_obj))


if __name__ == '__main__':
    app = web.Application()
    app.router.add_post('/', handle)

    parser = argparse.ArgumentParser()
    parser.add_argument('--port')

    args = parser.parse_args()
    web.run_app(app, port=args.port)
