# -*- coding: utf-8 -*-
"""Setup the LPM application"""

import logging
from tg import config
from lpm import model
from lpm.lib.authorization import Permisos
import transaction


def bootstrap(command, conf, vars):
    """Place any commands to setup lpm here"""

    # <websetup.bootstrap.before.auth
    from sqlalchemy.exc import IntegrityError
    try:
        u = model.Usuario()
        u.nombre_usuario = u'admin'
        u.nombre = u'Administrador'
        u.apellido = u'Del Sistema'
        u.email = u'manager@somedomain.com'
        u.password = u'administrador'
    
        model.DBSession.add(u)
    
        g = model.Rol()
        g.nombre_rol = u'Administrador del Sistema'
        g.descripcion= u'Rol por defecto que tiene todos los permisos del sistema'
        
        g.usuarios.append(u)
    
        model.DBSession.add(g)
        
        p = model.Permiso()
        p.nombre_permiso = u'manage'
        p.descripcion = u'This permission give an administrative right to the bearer'
        p.roles.append(g)
        model.DBSession.add(p)
        
        #permisos del sistema
        print "Creando los permisos del sistema..."
        for perm, desc in Permisos.items():
            p = model.Permiso()
            p.nombre_permiso = perm
            p.descripcion = desc
            model.DBSession.add(p) 

        model.DBSession.flush()
        transaction.commit()
        print "Se han creado correctamente las tablas"
    except IntegrityError:
        print 'Warning, there was a problem adding your auth data, it may have already been added:'
        import traceback
        print traceback.format_exc()
        transaction.abort()
        print 'Continuing with bootstrapping...'
        

    # <websetup.bootstrap.after.auth>
