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
from google.appengine.ext.webapp.util import run_wsgi_app

from models import *


class ProjectsAdmin(webapp.RequestHandler):
  def get(self):

    user = User.get_current()
    if user == None:
      self.redirect('/register')
      return
    
    template_values = {
        'user': user,
        'projects': Project.get_all(),
        'users': User.get_all(),
        'logout': users.create_logout_url("/")
    }    

    path = os.path.join(settings.TEMPLATE_DIR, 'projects_admin.html')
    self.response.out.write(template.render(path, template_values))
    
  def post(self):

    user = User.get_current()
    if user == None:
      self.redirect('/register')
      return

    action = self.request.get('action')
    project_tag = self.request.get('project_tag')
    display_name = self.request.get('display_name')
    gravatar_email = self.request.get('gravatar_email')

    if action == 'add':
      project = Project.get_by_key_name(project_tag, Project.datastore_key())

      if not project and project_tag and display_name and gravatar_email:
        project = Project(parent=Project.datastore_key(), key_name=project_tag)
        project.display_name = display_name
        project.gravatar_email = gravatar_email
        project.put()
        memcache.set('project-%s' % project_tag, project)
        memcache.delete('projects')

    if action == 'update':

      if self.request.get('update') and project_tag and display_name:
        project = Project.get_project(project_tag)
        if project:
          project.display_name = display_name
          project.gravatar_email = gravatar_email
          project.put()
          memcache.set('project-%s' % project_tag, project)
          memcache.delete('projects')

      if self.request.get('hide'):
        project = Project.get_project(project_tag)
        if project:
          project.sidebar_hide = not project.sidebar_hide
          project.put()
          memcache.set('project-%s' % project_tag, project)
          memcache.delete('projects')

      if self.request.get('delete'):
        project = Project.get_project(project_tag)
        if project and Snippet.get_project_snippets(project_tag).count() == 0:
          project.delete()
          memcache.delete('project-%s' % project_tag)
          memcache.delete('projects')

    self.redirect(self.request.referrer)


application = webapp.WSGIApplication([
  ('/admin/projects', ProjectsAdmin)
], debug=True)


def main():
  run_wsgi_app(application)


if __name__ == '__main__':
  main()
