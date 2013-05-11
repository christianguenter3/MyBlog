import os
import webapp2
import jinja2
import hashlib
import hmac

from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__),'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape = True)

class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)
    
    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)
    
    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))
        
class Posts(db.Model):
    subject = db.StringProperty(required = True)
    content = db.TextProperty(required = True)
    create = db.DateTimeProperty(auto_now_add = True)
    permalink = db.StringProperty(required = False)

class Model:
    def get_posts(self):        
        return db.GqlQuery("SELECT * FROM Posts "
                           "ORDER BY create DESC")   
    def delete_all(self):
        db.delete("Model")
        
class User(db.Model):
    name = db.StringProperty(required = True)
    password = db.StringProperty(required = True)        

class FrontPage(Handler):
    def render_front(self, subject="", content="", error=""):
        posts = Model().get_posts()
        for post in posts:
            app.router.add((r'/' + str(post.permalink), BlogPage))
        self.render("front.html",error = error, subject = subject, content = content, posts = posts ) 
    def get(self):
        self.render_front()
        
            
class NewPostPage(Handler):
    def get(self):
        self.render("Form.html")
    def post(self):
        subject = self.request.get("subject")
        content = self.request.get("content")
        permalink = str(hash("subject"))
        
        if subject and content:
            p = Posts(subject = subject, content = content, permalink = permalink)
            p.put()
            app.router.add((r'/' + permalink, BlogPage))
            self.redirect("/" + permalink)
        else:
            error = "Subject and Content please!"
            self.render_front( subject, content, error)
        
class BlogPage(Handler):
    def get(self):
        for post in Model().get_posts():
            if post.permalink == self.request.path[1:]:
                self.render("Blog_Entry.html",post = post)
              
SECRET = 'Test'
              
def hash_str(s):
    return hmac.new(SECRET, s).hexdigest()

def make_secure_val(s):
    return "%s|%s" % (s, hash_str(s))

def check_secure_val(h):
    if not h:
        return None
    val = h.split('|')[0]
    if h == make_secure_val(val):
        return val              
  
class BlogCookie(Handler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        visits = 0
        
        visit_cookie_str = self.request.cookies.get(u'visits')
        
        if visit_cookie_str:
            cookie_val = check_secure_val(visit_cookie_str)
            print cookie_val
            if cookie_val:
                visits = int(cookie_val)
                
        visits += 1
        
        new_cookie_val = make_secure_val(str(visits))
        
        self.response.headers.add_header('Set-Cookie', 'visits=%s' % new_cookie_val)       
        self.write("You've been here %s times!" % visits)
        
        if visits > 20:
            self.write("You are the best ever")
        
import re

class SignupPage(Handler):
  def write_form(self, params):
    f = open('templates/signup.html', 'r')
    self.response.write(f.read()%(params))
  
  def valid_username(self, username):
    USER_RE = re.compile(r"^[a-zA-Z_-]{3,20}$")
    return USER_RE.match(username)

  def valid_password(self, password):
    PASS_RE = re.compile(r"^.{3,20}$")
    return PASS_RE.match(password)

  def password_matches(self, p1, p2):
    return p1 == p2

  def valid_email(self, email):
    EMAIL_RE = re.compile(r"^[\S]+@[\S]+\.[\S]+$")
    return EMAIL_RE.match(email)

  def default_params(self):
    params =  {}
    params['username'] = ""
    params['email'] = ""
    params['username_error'] = ""
    params['password_error'] = ""
    params['email_error'] = ""
    params['password_mismatch'] = ""
    return params

  def get(self):
    params = self.default_params()
    self.write_form(params)

  def post(self):
    params = self.default_params()
    params['username'] = str(self.request.get('username'))
    params['password'] = str(self.request.get('password'))
    params['verify'] = str(self.request.get('verify'))
    params['email'] = str(self.request.get('email'))
    if not self.valid_username(params['username']):
      params['username_error'] = "That's not a valid username"
    if not self.valid_password(params['password']):
      params['password_error'] = "That wasn't a valid password"
    if not self.password_matches(params['password'], params['verify']):
      print 'X'
      params['password_mismatch'] = "Your passwords didn't match"
    if params['email']:
      if not self.valid_email(params['email']):
        params['email_error'] = 'Invalid E-Mail'
    if params['username_error'] or params['password_error'] or params['email_error'] or params['password_mismatch']:
      self.write_form(params)
    else:
      users = User.all()
      users.filter('name =', params['username'])
      for user in users:
          params['username_error'] = 'Username already exists'
          self.write_form(params)
          return     
      user = User(name = params['username'], password = hash_str(params['password']))
      user.put()
      value = make_secure_val(params['username'])
      self.response.headers.add_header('Set-Cookie','name=' + value + '; Path=/')      
      self.redirect('/welcome')
      
class Welcome(webapp2.RequestHandler):
  def get(self):
    name = check_secure_val(self.request.cookies.get('name'))
    if name:
        self.response.write('Welcome, ' +  name)
    else:
        self.response.write('No Cookie Set')
        
class Login(Handler):
    def get(self):
        params = {}
        self.render('login.html',params = params)
    
    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')
        password_hash = hash_str(password)
        q = User.all()
        q.filter("name =", username)
        q.filter("password =", password_hash)
        if q.get():
            value = make_secure_val(username)
            self.response.headers.add_header('Set-Cookie', str('name=' + value + '; Path=/'))      
            self.redirect('/welcome')
        else:
            params = {}
            params['password_error'] = 'Invalid Login'
            self.render('login.html', params = params)
        
class Logout(Handler):
    def get(self):
        self.response.headers.add_header('Set-Cookie','name=;Path=/')
        self.redirect('/signup')
            
app = webapp2.WSGIApplication([('/newpost', NewPostPage),
                               ('/', FrontPage),
                               ('/test',BlogPage),
                               ('/cookie', BlogCookie),
                               ('/signup', SignupPage),
                               ('/welcome',Welcome),
                               ('/login',Login),
                               ('/logout',Logout)])
