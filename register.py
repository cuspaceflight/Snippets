import os
import cgi
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
from google.appengine.api import memcache
from google.appengine.ext.webapp.util import run_wsgi_app

from models import *


class Register(webapp.RequestHandler):
  def get(self):
    
    user = None
    if self.request.get('key'):
      user = db.get(self.request.get('key'))
      if user != None:
        if self.request.get('deny'):
          user.delete()
          message = ('Your request to use CUSF Snippets has been denied. '
              'If you think this is an error, please email admin@cusf.co.uk.')
          mail.send_mail('snippets@cusf.co.uk', user.user_object.email(),
              'CUSF Snippets user approval', message)
        else:
          user.approved = True
          user.put()
          memcache.delete('users')
          message = ('Your request to use CUSF Snippets has been approved. '
              'Visit http://snippets.cusf.co.uk/ to begin!')
          mail.send_mail('snippets@cusf.co.uk', user.user_object.email(),
              'CUSF Snippets user approval', message)

    template_values = {
        'user': users.get_current_user(),
        'approved': user,
        'denied': self.request.get('deny'),
        'logout': users.create_logout_url('/')
    }    

    path = os.path.join(settings.TEMPLATE_DIR, 'register.html')
    self.response.out.write(template.render(path, template_values))

  def post(self):
    
    user_object = users.get_current_user()
    if user_object:
      user = User(parent=User.datastore_key(), key_name=user_object.user_id())
      user.display_name = self.request.get('name')
      user.user_object = user_object
      user.put()

      approve_url = '%s?key=%s' % (self.request.referrer, user.key()) 
      deny_url = approve_url + '&deny=1'

      message = ("""%s (%s) is requesting approval to use CUSF Snippets.

The supplied CRSid is: %s

To approve this request, visit: %s

To deny this request, visit: %s

--

(You will be required to authenticate with Google Accounts in order to approve/deny, though you do not necessarily have to have a CUSF Snippets account associated with that account).

          """) % (user.display_name, user_object.email(),
          self.request.get('crsid'), approve_url, deny_url)
      
      mail.send_mail('snippets@cusf.co.uk', 'admin@cusf.co.uk',
          'CUSF Snippets user approval', message)

      template_values = {
          'registered': True,
          'logout': users.create_logout_url('/')
      }    

      path = os.path.join(settings.TEMPLATE_DIR, 'register.html')
      self.response.out.write(template.render(path, template_values))


application = webapp.WSGIApplication([
  ('/register', Register)
], debug=True)


def main():
  run_wsgi_app(application)


if __name__ == '__main__':
  main()
