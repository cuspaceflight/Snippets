import os
import cgi
import datetime
import wsgiref.handlers
import settings

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from google.appengine.dist import use_library
use_library('django', '1.2')

from google.appengine.ext.webapp import template
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.api import memcache
from google.appengine.ext.webapp.util import run_wsgi_app

from models import *


class UserView(webapp.RequestHandler):
  def get(self, user_id=None):

    user = User.get_current()
    if user == None:
      self.redirect('/register')
      return

    if not user_id:
      who = user
      user_id = user.user_object.user_id()
    else:
      who = User.get_user(user_id)
      if who == None:
        self.redirect('/')
        return

    date = datetime.date.today()
    date = date - datetime.timedelta(days=date.weekday())

    snippets = dict((snippet.date, snippet.content)
        for snippet in Snippet.get_snippets(user_id))

    weeks = []

    while date - who.user_since > datetime.timedelta(weeks=-2):
      data = {
          'date': date,
          'end_date': date + datetime.timedelta(days=6),
          'snippet': date in snippets,
          'content': snippets.get(date)
      }      
      weeks.append(data)
      date = date - datetime.timedelta(days=date.weekday(), weeks=1)

    template_values = {
        'user': user,
        'who': who,
        'editable': (user_id == user.user_object.user_id()),
        'weeks': weeks,
        'empty': (snippets == {}),
        'users': User.get_all(),
        'projects': Project.get_all(),
        'logout': users.create_logout_url('/')
    }

    path = os.path.join(settings.TEMPLATE_DIR, 'index.html')
    self.response.out.write(template.render(path, template_values))


class ProjectView(webapp.RequestHandler):
  def get(self, project_tag=None):
    
    user = User.get_current()
    if user == None:
      self.redirect('/register')
      return

    if not project_tag:
      self.redirect('/')
      return
    else:
      project = Project.get_project(project_tag)
      if project == None:
        self.redirect('/')
        return

    date = datetime.date.today()
    date = date - datetime.timedelta(days=date.weekday())

    snippets = dict((snippet.date, snippet.content)
        for snippet in Snippet.get_project_snippets(project_tag))

    weeks = []

    while date - project.user_since > datetime.timedelta(weeks=-2):
      data = {
          'date': date,
          'end_date': date + datetime.timedelta(days=6),
          'snippet': date in snippets,
          'content': snippets.get(date)
      }      
      weeks.append(data)
      date = date - datetime.timedelta(days=date.weekday(), weeks=1)

    template_values = {
        'user': user,
        'project': project,
        'weeks': weeks,
        'empty': (snippets == {}),
        'users': User.get_all(),
        'projects': Project.get_all(),
        'logout': users.create_logout_url('/')
    }

    path = os.path.join(settings.TEMPLATE_DIR, 'project.html')
    self.response.out.write(template.render(path, template_values))


class WeekView(webapp.RequestHandler):
  def get(self, timestamp=None):

    user = User.get_current()
    if user == None:
      self.redirect('/register')
      return

    if not timestamp:
      date = datetime.date.today()
      date = date - datetime.timedelta(days=date.weekday(), weeks=1)
    else:
      date = datetime.date.fromtimestamp(float(timestamp))
      date = date - datetime.timedelta(days=date.weekday())

    users_query = User.get_all()
    projects_query = Project.get_all()

    user_data = dict((user.user_object.user_id(), user) for user in users_query)   
    project_data = dict((proj.key().name(), proj) for proj in projects_query)

    snippets = []
    for snippet in Snippet.get_week_snippets(date):      
      data = {'content': snippet.content}
      if snippet.project_tag and snippet.project_tag in project_data:
        data['project'] = True
        data['entity'] = project_data.get(snippet.project_tag)
        snippets.append(data) 
      elif not snippet.project_tag and snippet.user_id in user_data:
        data['entity'] = user_data.get(snippet.user_id)
        snippets.append(data)

    template_values = {
        'user': user,
        'date': date,
        'end_date': date + datetime.timedelta(days=6),
        'prev': date - datetime.timedelta(weeks=1),
        'next': date + datetime.timedelta(weeks=1),
        'team': True,
        'snippets': snippets,
        'users': users_query,
        'projects': projects_query,
        'logout': users.create_logout_url('/')
    }    

    path = os.path.join(settings.TEMPLATE_DIR, 'team.html')
    self.response.out.write(template.render(path, template_values))


class SaveSnippet(webapp.RequestHandler):
  def post(self):

    timestamp = float(self.request.get('date'))
    date = datetime.date.fromtimestamp(timestamp)
    
    project_tag = self.request.get('project_tag')
    if project_tag:
      snippets = Snippet.get_project_snippet(date, project_tag)
      memcache.delete('snippets-project-%s' % project_tag)
    else:
      snippets = Snippet.get_snippet(date)
      memcache.delete('snippets-user-%s' % users.get_current_user().user_id())

    for snippet in snippets:
      if self.request.get('content'):
        snippet.content = self.request.get('content')
        snippet.put()
      else:
        snippet.delete()
    
    if snippets.count() == 0 and self.request.get('content'):
      snippet = Snippet(parent=Snippet.datastore_key())
      
      if project_tag:
        snippet.project_tag = project_tag
      snippet.user_id = users.get_current_user().user_id()
      snippet.date = date
      snippet.content = self.request.get('content')
      snippet.put()

      memcache.delete('snippets-%s' % date.strftime('%s'))

    if project_tag:
      Project.update(project_tag)
    else:
      User.update()

    self.redirect(self.request.referrer)


class Alerts(webapp.RequestHandler):
  def post(self):
    
    user_object = users.get_current_user()
    if user_object:
      user = User.get_by_key_name(user_object.user_id(), User.datastore_key())
      if user:
        user.user_object = user_object
        user.email_alerts = (self.request.get('alerts') == '1')
        user.put()
        memcache.set('user-%s' % user_object.user_id(), user)
        memcache.delete('users')
        
    
    self.redirect(self.request.referrer)


application = webapp.WSGIApplication([
  ('/', UserView),
  (r'/user/(.*)', UserView),
  (r'/project/(.*)', ProjectView),
  (r'/team/(.*)', WeekView),
  ('/save', SaveSnippet),
  ('/alerts', Alerts)
], debug=True)


def main():
  run_wsgi_app(application)


if __name__ == '__main__':
  main()
