#!/usr/bin/python3
# -*- coding: utf-8 -*-
import json, requests, time

from flask import  Flask, g, request, after_this_request, redirect, render_template, make_response
from flask_restful import Api, Resource, reqparse
from flask_httpauth import HTTPBasicAuth
import  logging, os, json, datetime, time

from redis import Redis
from rq import Queue, registry, use_connection
from rq.registry import FinishedJobRegistry


logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
#app.config['TEMPLATES_AUTO_RELOAD'] = True
#app.config['FLASK_RUN_EXTRA_FILES']="device_registry/templates/error.html"
api = Api(app)

redis = Redis()

q = Queue(connection=Redis(), default_timeout=3600)

auth = HTTPBasicAuth()

USER_DATA = {
    "admin":"admin"}


#Функция проверки камер, вызов стороннего api
def camera_check(id,check,ip,ip_flow,url,longitude,latitude):
    url = url
    data = {"id": id, "check": check,"ip": ip,"ip_flow": ip_flow, "url": url, "longitude": longitude, "latitude": latitude}
    camera_check_request = requests.post(url=url, json=data)
    return camera_check_request.json()

           
@auth.verify_password
def verify(username, password):
    if not (username and password):
        return False
    return USER_DATA.get(username) == password


#Класс отправить проверку, интеграция с другим api 
class CameraCheck(Resource):
    @auth.login_required
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('id', required=True)
        parser.add_argument('check', required=True)
        parser.add_argument('ip', required=True)
        parser.add_argument('ip_flow', required=True)
        parser.add_argument('url', required=True)
        parser.add_argument('longitude', required=True)
        parser.add_argument('latitude', required=True)
        args = parser.parse_args()
        ts = str(int(time.time()))

        r = q.enqueue(camera_check, args['id'], args['check'], args['ip'], args['ip_flow'], args['url'], args['longitude'], args['latitude'], result_ttl=86400)

        r.meta['id'] = args['id']
        r.meta['check'] = args['check']
        r.meta['ip'] = args['ip']
        r.meta['ip_flow'] = args['ip_flow']
        r.meta['latitude'] = args['latitude']
        r.meta['longitude'] = args['longitude']
        r.meta['ts'] = ts
        r.save_meta()
        return {"job-id": r.id ,"ts": str(ts)}, 201


#Класс по id получить из очереди check 
#прочитать все сообщения
#разбить сообщения на группы по типам
#уникальный = id + тип сообщения + last проверка по времени
#- aviability
#- deviation
#- flowstrucrure
#- sound
class CameraResult(Resource):
    def get(self):
        logging.debug("Get query params")
        parser = reqparse.RequestParser()
        parser.add_argument('id', required=True,type=str)
        parser.add_argument('check', required=True,type=str)
        args = parser.parse_args()
        id = args['id']
        check = args['check']
        ts = int(time.time())
        logging.debug("Get query all jobs")
        try:    
            registry = FinishedJobRegistry('default', connection=redis)
            job_ids = registry.get_job_ids()
            tsarr = []
            tmparr = []
            for i in job_ids:
                logging.debug("Get job id " + i)
                joba = q.fetch_job(i)
                try:
                    logging.debug("Check job for conditions  " + i + " id="+ joba.meta['id'] + " check=" + joba.meta['check'] + " ts=" + joba.meta['ts'] )
                    if joba.meta['id'] == id and  joba.meta['check'] == check:
                        logging.debug("Find  job for id=" + joba.meta['id'] + " check=" + joba.meta['check'] + " ts=" + joba.meta['ts'])
                        tsarr.append(int(joba.meta['ts']))
                        tmparr.append({"job": i, "ts": str(joba.meta['ts']) })
                except :
                    pass
            if tsarr:
                logging.debug("Find max time " )
                logging.debug("For array job  " + str(tmparr))
                max_time = max(tsarr)
                logging.debug("Max time "  + str(max_time))
                for j in tmparr:
                    if int(j['ts']) == max_time:
                        job_max_id = j['job']
                        logging.debug("Max time  job "  + str(job_max_id))
                        job_m = q.fetch_job(job_max_id)
                headers = {'Content-Type': 'application/json'}
                data = job_m.result  
                return make_response(data,200,headers)
        except Exception as e:
            print(str(e))
            return "Not found", 404  


api.add_resource(CameraCheck, '/cameras/check')
api.add_resource(CameraResult, '/cameras/result')
