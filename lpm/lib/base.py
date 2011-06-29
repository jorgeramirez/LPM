# -*- coding: utf-8 -*-

"""The base Controller API."""

from tg import TGController, tmpl_context
from tg.render import render
from tg import request, session
from pylons.i18n import _, ungettext, N_
import lpm.model as model

__all__ = ['BaseController']


class BaseController(TGController):
    """
    Base class for the controllers in the application.

    Your web application should have one of these. The root of
    your application is used to compute URLs used by your app.

    """

    def __call__(self, environ, start_response):
        """Invoke the Controller"""
        # TGController.__call__ dispatches to the Controller method
        # the request is routed to. This routing information is
        # available in environ['pylons.routes_dict']

        request.identity = request.environ.get('repoze.who.identity')
        # para acceder mas rapido a este componente
        request.credentials = request.environ.get('repoze.what.credentials')

        username = request.credentials["repoze.what.userid"]
        usuario = model.Usuario.by_user_name(username)
        request.puede_proyecto = False
        request.puede_fase = False
        request.puede_ti = False
            
        if u"crear proyecto" in request.credentials["permissions"] or \
           u"modificar proyecto" in  request.credentials["permissions"]:
            request.puede_proyecto = True
        elif u"modificar fase" in request.credentials["permissions"]:
            request.puede_fase = True
        else:
            if u"crear tipo item" in request.credentials["permissions"] or \
               u"redefinir tipo item" in request.credentials["permissions"]:
                request.puede_ti = True
        
        tmpl_context.identity = request.identity
#        session['atras'] = session['actual']
#        session['actual'] = session['adelante']
        
        session.save()
        return TGController.__call__(self, environ, start_response)
