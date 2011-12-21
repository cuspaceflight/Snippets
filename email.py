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
    snippets = Snippet.all()
    snippets.ancestor(Snippet.datastore_key())
    snippets.filter("date =", date)
    
    authors = [snippet.user_id for snippet in snippets]

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

    user_data = dict((user.user_object.user_id(), user)
        for user in User.get_all())
   
    snippets = [{
            'user': user_data.get(snippet.user_id),
            'content': snippet.content
        } for snippet in Snippet.get_week_snippets(date)]

    if len(snippets) > 0:

      template_values = {
          'date': date,
          'snippets': snippets
      }    

      path = os.path.join(settings.TEMPLATE_DIR, 'report.tpl')
      message = template.render(path, template_values)

      subject = 'CUSF Snippets: %s - %s' % (
          date.strftime('%d/%m/%y'), end_date.strftime('%d/%m/%y'))
      
      mail.send_mail('snippets@cusf.co.uk', 'admin@cusf.co.uk',
          subject, message)


application = webapp.WSGIApplication([
  ('/email/reminder', Reminder),
  ('/email/report', Report)
], debug=True)


def main():
  run_wsgi_app(application)


if __name__ == '__main__':
  main()
