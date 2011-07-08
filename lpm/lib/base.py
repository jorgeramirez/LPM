# -*- coding: utf-8 -*-

"""The base Controller API."""

from tg import TGController, tmpl_context
from tg.render import render
from tg import request, session
from repoze.what.predicates import has_any_permission
from pylons.i18n import _, ungettext, N_
import lpm.model as model
from lpm.lib.authorization import AlgunPermiso

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
        request.puede_gestion_conf = False
        request.puede_desarrollo = False
        
        if request.credentials:
            username = request.credentials["repoze.what.userid"]
            usuario = model.Usuario.by_user_name(username)
            request.puede_proyecto = False
            request.puede_rol = False
            request.puede_fase = False
            request.puede_ti = False
            request.puede_busqueda = False
            
                
            if u"crear proyecto" in request.credentials["permissions"] or \
               u"modificar proyecto" in  request.credentials["permissions"]:
                request.puede_proyecto = True
            if AlgunPermiso(tipo="Rol").is_met(request.environ):
                request.puede_rol = True
            if u"modificar fase" in request.credentials["permissions"]:
                request.puede_fase = True
            if u"crear tipo item" in request.credentials["permissions"] or \
                   u"redefinir tipo item" in request.credentials["permissions"]:
                    request.puede_ti = True
            if AlgunPermiso(tipo="Usuario").is_met(request.environ):
                request.puede_busqueda = True
            if AlgunPermiso(tipo="Tipo").is_met(request.environ):
                request.puede_desarrollo = True
            if has_any_permission(u"crear lb",u"abrir-cerrar lb",u"consultar lb").\
                is_met(request.environ):
                request.puede_gestion_conf = True
			
        tmpl_context.identity = request.identity
#        session['atras'] = session['actual']
#        session['actual'] = session['adelante']
        
        session.save()
        return TGController.__call__(self, environ, start_response)
