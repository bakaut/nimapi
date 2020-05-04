from aiohttp import web
import json
import argparse
from icmplib import ping
import time


async def check_ping(addr, count=10):
    host = ping(addr, count=count, interval=0.2, timeout=2)
    k = 0.8
    if host.transmitted_packets == 0:
        return False
    elif host.received_packets == 0:
        return False
    elif host.received_packets / host.transmitted_packets < k:
        return False
    else:
        return True


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
    response_obj['result'] = await check_ping(response_obj.get('ip'))

    return web.Response(text=json.dumps(response_obj))

if __name__ == '__main__':
    app = web.Application()
    app.router.add_post('/', handle)

    parser = argparse.ArgumentParser()
    parser.add_argument('--port')

    args = parser.parse_args()
    web.run_app(app, port=args.port)
