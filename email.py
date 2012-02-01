import os
import cgi
import datetime
import wsgiref.handlers
import settings

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from google.appengine.dist import use_library
use_library('django', '1.2')

from google.appengine.ext.webapp import template
from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.api import mail
from google.appengine.ext.webapp.util import run_wsgi_app

from models import *


class Reminder(webapp.RequestHandler):
  def get(self):
    
    date = datetime.date.today()
    date = date - datetime.timedelta(days=date.weekday(), weeks=1)
    end_date = date + datetime.timedelta(days=6)

    users = User.get_all()
    snippets = Snippet.get_week_snippets(date)
    
    authors = [snippet.user_id for snippet in snippets
        if not snippet.project_tag]

    remind_users = []
    for user in users:
      if user.user_object.user_id() not in authors:
        remind_users.append(user)

    for user in users:
      if user.user_object.user_id() not in authors and user.email_alerts:
        template_values = {
            'date': date,
            'end_date': end_date,
            'user': user
        }    

        path = os.path.join(settings.TEMPLATE_DIR, 'reminder.tpl')
        message = template.render(path, template_values)

        mail.send_mail('snippets@cusf.co.uk', user.user_object.email(),
            'CUSF Snippets reminder', message)


class Report(webapp.RequestHandler):
  def get(self):

    date = datetime.date.today()
    date = date - datetime.timedelta(days=date.weekday(), weeks=1)
    end_date = date + datetime.timedelta(days=6)    

    users_query = User.get_all()
    projects_query = Project.get_all()

    user_data = dict((user.user_object.user_id(), user) for user in users_query)   
    project_data = dict((proj.key().name(), proj) for proj in projects_query)

    snippets = []
    for snippet in Snippet.get_week_snippets(date):      
      data = {'content': snippet.content}
      if snippet.project_tag and snippet.project_tag in project_data:
        data['entity'] = project_data.get(snippet.project_tag)
        snippets.append(data) 
      elif not snippet.project_tag and snippet.user_id in user_data:
        data['entity'] = user_data.get(snippet.user_id)
        snippets.append(data)

    if len(snippets) > 0:

      template_values = {
          'date': date,
          'snippets': snippets
      }    

      path = os.path.join(settings.TEMPLATE_DIR, 'report.tpl')
      message = template.render(path, template_values)

      subject = 'CUSF Snippets: %s - %s' % (
          date.strftime('%d/%m/%y'), end_date.strftime('%d/%m/%y'))
      
      mail.send_mail('snippets@cusf.co.uk', 'team@cusf.co.uk',
          subject, message)


application = webapp.WSGIApplication([
  ('/email/reminder', Reminder),
  ('/email/report', Report)
], debug=True)


def main():
  run_wsgi_app(application)


if __name__ == '__main__':
  main()
