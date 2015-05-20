# -*- coding: utf-8 -*-
import os 
import sys
import sae
import json
import re

root = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(root, 'site-packages'))

from werobot.robot import werobot
from werobot.session.saekvstorage import SaeKVDBStorage
from werobot.utils  import * 
from douban_client import DoubanClient
from douban import *

session_storage = SaeKVDBStorage()

# user info [guid], uid, access token
wechat_kv = sae.kvdb.Client()

robot = werobot.WeRoBot(token="freesz", enable_session=True,
                        session_storage=session_storage)

client = DoubanClient(API_KEY, API_SECRET, REDIRECT_URI, SCOPE)
       
@robot.filter("大牛")
def person(message, session):
    return "大牛列表,请输入TED牛人序号, 待完成"

# 豆瓣oauth2鉴权   
@robot.filter("豆瓣")
def douban(message, session):
    guid = message.source
    token = get_token(message, session)
    if None == token:
        auth_des = u'请点我完成豆瓣授权'
        auth_url =  client.authorize_url + '&state='+ guid
        auth_html = '<a href="%s">%s</a>' % (auth_url,auth_des)
        return auth_html
    else:
        return u"豆瓣授权成功! " + u"公众号id:" + guid + u'豆瓣token:'+token

# 标记想读 中文正则匹配有问题
@robot.filter(re.compile("\d"))
def wish_read(message, session):
    token = get_token(message, session)
    if (None == token):
        return "输入'豆瓣'完成授权后回到微信"
    else:
        print message.content
        client.auth_with_token(token)
        bookid =  session.get(message.content, 0)
        print bookid
        if 0 == bookid:
            return "输入有误,请重新输入"
        else:
            try:
                client.book.collection(bookid)
            except:
                return "你收藏过这本书啦!"
            else:
                return "设置想读成功!"
 
# 根据关键字查书
@robot.text
def book(message, session):
    token = get_token(message, session)
    if (None == token):
        return "输入'豆瓣'完成授权后回到微信"
    else:
        client.auth_with_token(token)
        res = client.book.search(message.content, '', 0, 3)
        res_str = json.dumps(res)
        print res_str
        count = res['count']
        if count == 0:
            return u"没找到啊，修改下关键字试试~"
        else:
            ret_str = u'作品列表:\n'
            for i in range(count):
                session[str(i)] = res['books'][i]['id']
                print session.get(str(i), 0)
                ret_str +=  str(i) + ' '   \
                            + res['books'][i]['title'] + ' ' \
                            + res['books'][i]['publisher'] + ' ' \
                            + res['books'][i]['pubdate'] + ' ' \
                            + res['books'][i]['pages'] + '\n ' 
                       #     + res['books'][i]['ebook_url'] + '\n'
                  #          + res['books'][i]['author'][0] + '\n'
            ret_str +=  u'输入书序号0,1,2等可标记为想读\n'
            print ret_str
            return ret_str
            
@robot.text
def session_times(message, session):
    count = session.get("count", 0) + 1
    session["count"] = count
    return "你累计发了 %s 条消息" % count

@robot.subscribe
def subscribe(message):
    return "欢迎来到Niubility! 输入任意关键字(书名或作者）查书，输入'大牛'有惊喜哦！"

# get token saved in wechat_kv
def get_token(message, session):
    guid = message.source
    userstr = wechat_kv.get(to_binary(guid))
    if None != userstr:
       user = json.loads(userstr)
       uid = user['uid']
       token = user['token']
       return token
    return None
