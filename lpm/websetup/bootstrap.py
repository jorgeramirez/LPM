# -*- coding: utf-8 -*-
"""Setup the LPM application"""

import logging
from tg import config
from lpm import model

import transaction


def bootstrap(command, conf, vars):
    """Place any commands to setup lpm here"""

    # <websetup.bootstrap.before.auth
    from sqlalchemy.exc import IntegrityError
    try:
        u = model.Usuario()
        u.nombre_usuario = u'manager'
        u.nombre = u'Fulano'
        u.apellido = u'Detal'
        u.email = u'manager@somedomain.com'
        u.password = u'managepass'
    
        model.DBSession.add(u)
    
        g = model.Rol()
        g.nombre_rol = u'managers'
        g.descripcion= u'Managers Group'
    
        g.usuarios.append(u)
    
        model.DBSession.add(g)
    
        p = model.Permiso()
        p.nombre_permiso = u'manage'
        p.descripcion = u'This permission give an administrative right to the bearer'
        p.roles.append(g)
    
        model.DBSession.add(p)
        '''
    
        u1 = model.Usuario()
        u1.nombre_usario = u'editor'
        u1.nombre = u'Example editor'
        u1.email = u'editor@somedomain.com'
        u1.password = u'editpass'
    
        model.DBSession.add(u1)
        '''
        model.DBSession.flush()
        transaction.commit()
    except IntegrityError:
        print 'Warning, there was a problem adding your auth data, it may have already been added:'
        import traceback
        print traceback.format_exc()
        transaction.abort()
        print 'Continuing with bootstrapping...'
        

    # <websetup.bootstrap.after.auth>
