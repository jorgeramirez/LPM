# -*- coding: utf-8 -*-
"""Main Controller"""

from tg import expose, flash, require, url, request, redirect
from pylons.i18n import ugettext as _, lazy_ugettext as l_
from tgext.admin.tgadminconfig import TGAdminConfig
#from tgext.admin.controller import AdminController
from tgext.admin import AdminController
from repoze.what import predicates

from lpm.lib.base import BaseController
from lpm.lib.mail import Gmail
from lpm.model import DBSession, metadata, Usuario
from lpm import model
from lpm.controllers.secure import SecureController
from lpm.controllers.error import ErrorController
from lpm.controllers.proyecto import ProyectoController
from lpm.controllers.fase import FaseController

import hashlib , random

__all__ = ['RootController']


class RootController(BaseController):
    """
    The root controller for the LPM application.

    All the other controllers and WSGI applications should be mounted on this
    controller. For example::

        panel = ControlPanelController()
        another_app = AnotherWSGIApplication()

    Keep in mind that WSGI applications shouldn't be mounted directly: They
    must be wrapped around with :class:`tg.controllers.WSGIAppController`.

    """
    proyectos = ProyectoController(DBSession)
    fases = FaseController(DBSession)
    error = ErrorController()

    @expose('lpm.templates.index')
    def index(self):
        """Handle the front-page."""
        return dict(page='index')

    @expose('lpm.templates.about')
    def about(self):
        """Handle the 'about' page."""
        return dict(page='about')

    @expose('lpm.templates.environ')
    def environ(self):
        """This method showcases TG's access to the wsgi environment."""
        return dict(environment=request.environ)

    @expose('lpm.templates.data')
    @expose('json')
    def data(self, **kw):
        """This method showcases how you can use the same controller for a data page and a display page"""
        return dict(params=kw)

    @expose('lpm.templates.authentication')
    def auth(self):
        """Display some information about auth* on this application."""
        return dict(page='auth')

    @expose('lpm.templates.index')
    @require(predicates.has_permission('manage', msg=l_('Only for managers')))
    def manage_permission_only(self, **kw):
        """Illustrate how a page for managers only works."""
        return dict(page='managers stuff')

    @expose('lpm.templates.index')
    @require(predicates.is_user('editor', msg=l_('Only for the editor')))
    def editor_user_only(self, **kw):
        """Illustrate how a page exclusive for the editor works."""
        return dict(page='editor stuff')

    @expose('lpm.templates.login')
    def login(self, came_from=url('/')):
        """Start the user login."""
        login_counter = request.environ['repoze.who.logins']
        if login_counter > 0:
            flash(_('Wrong credentials'), 'warning')
        return dict(page='login', login_counter=str(login_counter),
                    came_from=came_from)
        
    @expose('lpm.templates.recuperar_pass')
    def recuperar_pass(self):
        """Recupera el pass enviado por mail uno nuevo."""
        return dict(page='recuperar pass')
    
    @expose()
    def enviar_pass(self, **kw):
        """Recupera el pass enviado por mail uno nuevo."""
        usernamegiven = kw["loginusernamegiven"]
        user = Usuario.by_user_name(usernamegiven)
        if user != None:
            smtp_gmail = Gmail()
            mail = user.email #DEBUG: u"carlosbellino@gmail.com"
            hash = hashlib.new('ripemd160')
            hash.update(user.email + unicode(random.random()))
            new_pass = hash.hexdigest()
            user._set_password(new_pass)
            DBSession.add(user)
            text = _(u"Tu nueva contraseña es : %s") % new_pass
            smtp_gmail.enviar_mail(mail, text)
            smtp_gmail.quit()
            flash(_(u'Nueva contraseña enviada a %s') % mail)
            redirect(url('/login'))
        else:
            flash(_(u'No existe Usuario'))
            redirect(url('/recuperar_pass'))
    
    @expose()
    def post_login(self, came_from='/'):
        """
        Redirect the user to the initially requested page on successful
        authentication or redirect her back to the login page if login failed.

        """
        if not request.identity:
            login_counter = request.environ['repoze.who.logins'] + 1
            redirect('/login', came_from=came_from, __logins=login_counter)
        userid = request.identity['repoze.who.userid']
        flash(_('Welcome back, %s!') % userid)
        redirect(came_from)

    @expose()
    def post_logout(self, came_from=url('/')):
        """
        Redirect the user to the initially requested page on logout and say
        goodbye as well.
        """
        flash(_('We hope to see you soon!'))
        #redirect(came_from)
        redirect(url('/'))
