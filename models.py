import urllib
import hashlib
import datetime
import random

from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.api import memcache


class Entity(db.Model):
  """An abstract model representing an entity that stores snippets."""
  display_name = db.StringProperty()
  user_since = db.DateProperty(auto_now_add=True)
  last_update = db.DateTimeProperty(default=datetime.datetime.fromtimestamp(0))

  def gravatar_url(self):
    """All entities should be able to have an icon representation."""
    raise NotImplementedError("Classes extending Entity must implement this.")

  @staticmethod
  def datastore_key():
    raise NotImplementedError("Classes extending Entity must implement this.")


class Project(Entity):
  """A datastore model for teams/projects."""
  sidebar_hide = db.BooleanProperty(default=False)
  gravatar_email = db.StringProperty()

  def gravatar_url(self):
    url = "http://www.gravatar.com/avatar/"
    url += hashlib.md5(self.gravatar_email).hexdigest() + "?"
    url += urllib.urlencode({'d': 'retro'})
    return url

  @staticmethod
  def datastore_key():
    return db.Key.from_path('projects', 'default_projects')  
    
  @staticmethod
  def get_all():
    projects = memcache.get('projects')
    if not projects:
      projects = Project.all()
      projects.ancestor(Project.datastore_key())
      projects.order('-last_update')
      memcache.set('projects', projects)
    return projects

  @staticmethod
  def get_project(project_tag):
    project = memcache.get('project-%s' % project_tag)
    if not project:
      project = Project.get_by_key_name(project_tag, Project.datastore_key())
      if project:
        memcache.set('project-%s' % project_tag, project)
    return project

  @staticmethod
  def update(project_tag):
    project = Project.get_by_key_name(project_tag, Project.datastore_key())
    if project:
      project.last_update = datetime.datetime.today()
      project.put()
      memcache.set('project-%s' % project_tag, project)
      memcache.delete('projects')

class User(Entity):
  """A datastore model for users (each associated with a Google Account)."""

  user_object = db.UserProperty()
  email_alerts = db.BooleanProperty(default=True)
  approved = db.BooleanProperty(default=False)

  def gravatar_url(self):
    url = "http://www.gravatar.com/avatar/"
    url += hashlib.md5(self.user_object.email().lower()).hexdigest() + "?"
    url += urllib.urlencode({'d': 'mm'})
    return url

  @staticmethod
  def datastore_key():
    return db.Key.from_path('users', 'default_users')  

  @staticmethod
  def get_user(user_id):
    user = memcache.get('user-%s' % user_id)
    if not user:
      user = User.get_by_key_name(user_id, User.datastore_key())
      if user:
        memcache.set('user-%s' % user_id, user)
    return user

  @staticmethod
  def get_all():
    users = memcache.get('users')
    if not users:
      users = User.all()
      users.ancestor(User.datastore_key())
      users.filter('approved =', True)
      users.order('-last_update')
      memcache.set('users', users)
    return users

  @staticmethod
  def update():
    user_object = users.get_current_user()
    if user_object:
      user = User.get_by_key_name(user_object.user_id(), User.datastore_key())
      if user:
        user.user_object = user_object
        user.last_update = datetime.datetime.today()
        user.put()
        memcache.set('user-%s' % user_object.user_id(), user)
        memcache.delete('users')

  @staticmethod
  def get_current():
    user_object = users.get_current_user()
    if user_object:
      user = User.get_user(user_object.user_id())
      if user and user.approved:
        return user
      else:
        return None
    else:
      return None
      

class Snippet(db.Model):
  user_id = db.StringProperty()
  project_tag = db.StringProperty()
  content = db.StringProperty(multiline=True)
  date = db.DateProperty()

  @staticmethod
  def datastore_key():
    return db.Key.from_path('snippets', 'default_snippets')

  @staticmethod
  def get_snippets(user_id):
    snippets = memcache.get('snippets-user-%s' % user_id)
    if not snippets:    
      snippets = Snippet.all()
      snippets.ancestor(Snippet.datastore_key())
      snippets.filter("user_id =", user_id)
      snippets.filter('project_tag =', None)
      snippets.order("-date")
      memcache.set('snippets-user-%s' % user_id, snippets)
    return snippets

  @staticmethod
  def get_snippet(date):
    snippets = Snippet.all()
    snippets.ancestor(Snippet.datastore_key())
    snippets.filter("user_id =", users.get_current_user().user_id())
    snippets.filter('project_tag =', None)
    snippets.filter("date =", date)
    return snippets

  @staticmethod
  def get_project_snippets(project_tag):
    snippets = memcache.get('snippets-project-%s' % project_tag)
    if not snippets:    
      snippets = Snippet.all()
      snippets.ancestor(Snippet.datastore_key())
      snippets.filter("project_tag =", project_tag)
      snippets.order("-date")
      memcache.set('snippets-project-%s' % project_tag, snippets)
    return snippets

  @staticmethod
  def get_project_snippet(date, project_tag):
    snippets = Snippet.all()
    snippets.ancestor(Snippet.datastore_key())
    snippets.filter("project_tag =", project_tag)
    snippets.filter("date =", date)
    return snippets  

  @staticmethod
  def get_week_snippets(date):
    snippets = memcache.get('snippets-%s' % date.strftime('%s'))
    if not snippets:
      snippets = Snippet.all()
      snippets.ancestor(Snippet.datastore_key())
      snippets.filter("date =", date)
      snippets.order('-project_tag')
      memcache.set('snippets-%s' % date.strftime('%s'), snippets)
    return snippets

