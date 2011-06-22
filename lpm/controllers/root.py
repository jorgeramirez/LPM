# -*- coding: utf-8 -*-
"""Main Controller"""

from tg import expose, flash, require, url, request, redirect, session
from pylons.i18n import ugettext as _, lazy_ugettext as l_
from tgext.admin.tgadminconfig import TGAdminConfig
#from tgext.admin.controller import AdminController
from tgext.admin import AdminController
from repoze.what import predicates

from lpm.lib.base import BaseController
from lpm.lib.mail import Gmail
from lpm.model import DBSession, metadata, Usuario
from lpm import model
#from lpm.controllers.secure import SecureController
#from lpm.controllers.error import ErrorController
from lpm.controllers.proyecto import ProyectoController
from lpm.controllers.fase import FaseController
from lpm.controllers.usuario import UsuarioController
from lpm.controllers.rol import (RolController, RolPlantillaController)
#                                 RolContextoController)
from lpm.controllers.item import ItemController
from lpm.controllers.tipoitem import TipoItemController

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
    usuarios = UsuarioController(DBSession)
    roles = RolController(DBSession)
    rolesplantilla = RolPlantillaController(DBSession)
#    rolescontexto = RolContextoController(DBSession)
    proyectos = ProyectoController(DBSession)
    fases = FaseController(DBSession)
    tipositems = TipoItemController(DBSession)
    items = ItemController(DBSession)


    @expose('lpm.templates.index')
    def index(self):
        """Handle the front-page."""
        return dict(page='index')
    
    @expose('lpm.templates.data')
    @expose('json')
    def data(self, **kw):
        """This method showcases how you can use the same controller for a data page and a display page"""
        return dict(params=kw)

    @expose('lpm.templates.login.login')
    def login(self, came_from=url('/')):
        """Start the user login."""
        login_counter = request.environ['repoze.who.logins']
        if login_counter > 0:
            flash(_('Wrong credentials'), 'warning')
        return dict(page='login', login_counter=str(login_counter),
                    came_from=came_from)
        
    @expose('lpm.templates.login.recuperar_pass')
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
            mail = user.email #DEBUG:  u"carlosbellino@gmail.com"
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
    
    @expose('lpm.templates.index')
    def _default(self, *args, **kw):
        """Maneja las urls no encontradas"""
        flash(_('Recurso no encontrado'), 'warning')
        redirect('/')
        return dict(page='index')
