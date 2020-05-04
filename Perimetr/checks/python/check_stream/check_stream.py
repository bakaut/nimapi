from aiohttp import web
import json
import argparse
import rtsp
import time
import asyncio


async def check_stream_connection(addr, sleep_time=1):
    client = rtsp.Client(rtsp_server_uri=addr)
    await asyncio.sleep(sleep_time)
    result = client.read() is not None
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
    response_obj['result'] = await check_stream_connection('rtsp://' + response_obj.get('ip_flow'))

    return web.Response(text=json.dumps(response_obj))

if __name__ == '__main__':
    app = web.Application()
    app.router.add_post('/', handle)

    parser = argparse.ArgumentParser()
    parser.add_argument('--port')

    args = parser.parse_args()
    web.run_app(app, port=args.port)
