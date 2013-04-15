import os
import webapp2
import jinja2

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
            
app = webapp2.WSGIApplication([('/newpost', NewPostPage),
                               ('/', FrontPage),
                               ('/test',BlogPage)])

response = app.get_response('/')
print response.status_int
assert response.status_int == 201