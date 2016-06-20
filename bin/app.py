#!/usr/bin/python
import web
web.config.debug = True
import cgi, cgitb
#cgitb.enable()
import porc
import requests
import simplejson
import random
import os
import shutil
from stegano import lsb
from stegano import exifHeader
t = os.getcwd()
API = open('../../keys/bstego.csv', 'rU') # two ../ for koding, two ../ for c9
API = API.read()
API = API[:-1]
API_KEYS = API.split('\n')
APP_KEYS = []
for each_key in API_KEYS:
	key = each_key.split(',')
	APP_KEYS.append([key[0],key[1]])
EMAIL_API_KEY = APP_KEYS[0][1]
MY_API_KEY = APP_KEYS[1][1]
MAILGUN_API_KEY = APP_KEYS[2][1]
client = porc.Client(MY_API_KEY)
respond = client.ping()

urls = (
	'/', 'index',
	'/register', 'register',
	'/accountcreated', 'created',
	'/login', 'login',
	'/account', 'account',
	'/doesnotexist', 'doesnotexist',
	'/encode', 'encode',
	'/decode', 'decode',
	'/api', 'api',
	'/about', 'about'
)

app = web.application(urls, globals())

render = web.template.render('templates/')

class index:
	def GET(self):
		return render.index()

class register:
	def GET(self):
		return render.register()

class created:
	def GET(self):
		return render.makeanaccount()
		
	def POST(self):
		user = web.input()
		email = user.email
		username = user.username
		params = {'email': email}
		response = requests.get('http://apilayer.net/api/check?access_key='+EMAIL_API_KEY, params=params)
		response = simplejson.loads(response.content)
		if response["disposable"] == True or response["score"] < 0.5:
			return render.comeon(email=email)
		if email == '' or username == '':
			return render.loginerror()
		dbUsername = client.get('bstego', username)
		dbUsername = dbUsername["username"]
		dbEmail = client.get('bstego', email)
		dbEmail = dbEmail["email"]
		uniqueURL = ''
		alphalower = ['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z']
		alphaupper = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z']
		numbers = [0,1,2,3,4,5,6,7,8,9]
		for char in range(25):
			choice = random.randrange(3)
			if choice == 2:
				uniqueURL += str(numbers[random.randrange(10)])
			if choice == 1:
				uniqueURL += alphalower[random.randrange(26)]
			else:
				uniqueURL += alphaupper[random.randrange(26)]
		if dbUsername != username and dbEmail != email:
			send = client.put('bstego', username, {
				"username": username,
        		"email": email,
				"URL": uniqueURL,
				"pictures": [],
				"encoded": 0,
				"decoded": 0
			})
			validate = client.get('bstego', 'test')
			validate = validate["username"]
			send_simple_message(email, username, uniqueURL)
			return render.accountsuccess(username=username)
		else:
			return render.nametaken(username=username)
class login:
	def GET(self):
		return render.login()

class account:
	def GET(self):
		return render.makeanaccount()
	
	def POST(self):
		user = web.input()
		email = user.email
		username = user.username
		passphrase = user.password
		uid = client.get('bstego', username)
		uidu = uid["username"]
		pictures = uid["pictures"]
		encoded = uid["encoded"]
		decoded = uid["decoded"]
		pictures = uid["pictures"]
		if uidu != username:
			raise web.seeother('/doesnotexist')
		elif str(uid["email"]) != email:
			return render.emaildoesnotmatch(email=email)
		elif str(uid["URL"]) != passphrase:
			return render.passdoesnotmatch(password=passphrase)
		else:
			return render.account(email=email,username=username, pictures=pictures, encoded=encoded, decoded=decoded)
			

class doesnotexist:
	def GET(self):
		return render.doesnotexist()
		
class encode:
	def GET(self):
		return render.makeanaccount()
	def POST(self):
		input = web.input(file={})
		filename = input['file'].filename
		fileds = input['file'].value
		message = input.message
		if filename.endswith('.jpg') or filename.endswith('.png') or filename.endswith('.jpeg') and filename.count('/') == -1:
			os.chdir('static/files')
			with open(filename, 'wb') as fout:
				shutil.copyfileobj(input['file'].file, fout, 100000)
			os.chdir('../../')
    		# do NOT touch above code
			if filename.endswith('.png'):
				sec = lsb.hide('static/files/' + filename, message)
				sec.save('static/files/' + filename)
			if filename.endswith('.jpg') or filename.endswith('.jpeg'):
				secret = exifHeader.hide('static/files/' + filename, 'static/files/' + filename, secret_message = message)
			return '''
			<!DOCTYPE html>
			<html lang="en">
				<head>
					<title>
						Your image
					</title>
					<style>
						img {
							width: 500px;
							height: 500px;
						}
					</style>	
				</head>
				<body>
					<h1>
						Right click on the image and click <i>Save As</i> to save it.
					</h1>
					<img src="static/files/'''+filename+'''" />
				</body>
			</html>	
			'''		
		else:
			return

class decode:
    def GET(self):
        return render.makeanaccount()
    def POST(self):
        input = web.input(file={})
        filename = input['file'].filename
        fileds = input['file'].value
        if filename.endswith('.jpg') or filename.endswith('.png') or filename.endswith('.jpeg') and filename.count('/') == -1:
            os.chdir('static/files')
            with open(filename, 'wb') as fout:
                shutil.copyfileobj(input['file'].file, fout, 100000)
            os.chdir('../../')
            # do NOT touch above code
            if filename.endswith('.png'):
                return '''
                <!DOCTYPE html>
                <html lang="en">
                    <head>
                        <title>Attempted to Decode</title>
                        <meta charset="utf-8">
                    </head>
                    <body>
            '''+lsb.reveal("static/files/"+filename)+"<p>Message decoded should be above.</p></body></html>"
            if filename.endswith('.jpg') or filename.endswith('.jpeg'):
                return '''
                <!DOCTYPE html>
                <html lang="en">
                    <head>
                        <title>Attempted to Decode</title>
                        <meta charset="utf-8">
                    </head>
                    <body>
            '''+exifHeader.reveal("static/files/"+filename)+"<p>Message decoded should be above.</p></body></html>"
    
class api:
    def GET(self):
        return render.api()
        
class about:
    def GET(self):
        return render.about()
    
def send_simple_message(email, username, url):
    return requests.post(
        "https://api.mailgun.net/v3/mg.hackthe.tech/messages",
        auth=("api", MAILGUN_API_KEY),
        data={"from": "bStego <mailgun@mg.hackthe.tech>",
              "to": [email],
              "subject": 'bStego registration',
              "html": "<b>Hey "+username+'''</b>,
                  My name is Jonathan. I'm the creator of bStego. Your unique passphrase is <b>'''+ url + '''</b> in case you forget.
               You can now login <a href="http://jonathanwong.koding.io:8080/login">here</a>. Heres a :) on me. In the case that you did not sign up for bStego you should disregard this email, but (hopefully) check my project out!
               
               Thanks, Jonathan
               Please note that receiving emails has not been implemented on my server, so do not email me here. Please email me at <i>jwong24@stuy.edu</i>.
               '''})		

if __name__ == "__main__":
	app.run()