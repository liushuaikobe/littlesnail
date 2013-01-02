# -*- coding: utf-8 -*-
from django.http import HttpResponse
from django.template import RequestContext, Template
from django.views.decorators.csrf import csrf_exempt
from django.utils.encoding import smart_str, smart_unicode

import xml.etree.ElementTree as ET
import urllib,urllib2,time

TOKEN = "lovezlp"

YOUDAO_KEY = 909053810
YOUDAO_KEY_FROM = "little-snail"
YOUDAO_DOC_TYPE = "xml"

@csrf_exempt
def handleRequest(request):
	if request.method == 'GET':
		#response = HttpResponse(request.GET['echostr'],content_type="text/plain")
		response = HttpResponse(checkSignature(request),content_type="text/plain")
		return response
	elif request.method == 'POST':
		#c = RequestContext(request,{'result':responseMsg(request)})
		#t = Template('{{result}}')
		#response = HttpResponse(t.render(c),content_type="application/xml")
		response = HttpResponse(responseMsg(request),content_type="application/xml")
		return response
	else:
		return None

def checkSignature(request):
	global TOKEN
	signature = request.GET.get("signature", None)
	timestamp = request.GET.get("timestamp", None)
	nonce = request.GET.get("nonce", None)
	echoStr = request.GET.get("echostr",None)

	token = TOKEN
	tmpList = [token,timestamp,nonce]
	tmpList.sort()
	tmpstr = "%s%s%s" % tuple(tmpList)
	tmpstr = hashlib.sha1(tmpstr).hexdigest()
	if tmpstr == signature:
		return echoStr
	else:
		return None

def responseMsg(request):
	rawStr = smart_str(request.raw_post_data)
	#rawStr = smart_str(request.POST['XML'])
	msg = paraseMsgXml(ET.fromstring(rawStr))
	
	queryStr = msg.get('Content','You have input nothing~')

	raw_youdaoURL = "http://fanyi.youdao.com/openapi.do?keyfrom=%s&key=%s&type=data&doctype=%s&version=1.1&q=" % (YOUDAO_KEY_FROM,YOUDAO_KEY,YOUDAO_DOC_TYPE)	
	youdaoURL = "%s%s" % (raw_youdaoURL,urllib2.quote(queryStr))

	req = urllib2.Request(url=youdaoURL)
	result = urllib2.urlopen(req).read()

	replyContent = paraseYouDaoXml(ET.fromstring(result))

	return getReplyXml(msg,replyContent)

def paraseMsgXml(rootElem):
	msg = {}
	if rootElem.tag == 'xml':
		for child in rootElem:
			msg[child.tag] = smart_str(child.text)
	return msg

def paraseYouDaoXml(rootElem):
	replyContent = ''
	if rootElem.tag == 'youdao-fanyi':
		for child in rootElem:
			# 错误码
			if child.tag == 'errorCode':
				if child.text == '20':
					return 'too long to translate\n'
				elif child.text == '30':
					return 'can not be able to translate with effect\n'
				elif child.text == '40':
					return 'can not be able to support this language\n'
				elif child.text == '50':
					return 'invalid key\n'

			# 查询字符串
			elif child.tag == 'query':
				replyContent = "%s%s\n" % (replyContent, child.text)

			# 有道翻译
			elif child.tag == 'translation': 
				replyContent = '%s%s\n%s\n' % (replyContent, '-' * 3 + u'有道翻译' + '-' * 3, child[0].text)

			# 有道词典-基本词典
			elif child.tag == 'basic': 
				replyContent = "%s%s\n" % (replyContent, '-' * 3 + u'基本词典' + '-' * 3)
				for c in child:
					if c.tag == 'phonetic':
						replyContent = '%s%s\n' % (replyContent, c.text)
					elif c.tag == 'explains':
						for ex in c.findall('ex'):
							replyContent = '%s%s\n' % (replyContent, ex.text)

			# 有道词典-网络释义
			elif child.tag == 'web': 
				replyContent = "%s%s\n" % (replyContent, '-' * 3 + u'网络释义' + '-' * 3)
				for explain in child.findall('explain'):
					for key in explain.findall('key'):
						replyContent = '%s%s\n' % (replyContent, key.text)
					for value in explain.findall('value'):
						for ex in value.findall('ex'):
							replyContent = '%s%s\n' % (replyContent, ex.text)
					replyContent = '%s%s\n' % (replyContent,'--')
	return replyContent

def getReplyXml(msg,replyContent):
	extTpl = "<xml><ToUserName><![CDATA[%s]]></ToUserName><FromUserName><![CDATA[%s]]></FromUserName><CreateTime>%s</CreateTime><MsgType><![CDATA[%s]]></MsgType><Content><![CDATA[%s]]></Content><FuncFlag>0</FuncFlag></xml>";
	extTpl = extTpl % (msg['FromUserName'],msg['ToUserName'],str(int(time.time())),'text',replyContent)
	return extTpl
