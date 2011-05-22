# -*- coding: utf-8 -*-
"""Setup the LPM application"""
from tg import config

from lpm import model
from lpm.lib.authorization import Permisos

import transaction
import logging

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
    
        r = model.Rol()
        r.nombre_rol = u'Administrador del Sistema'
        r.descripcion= u'Rol por defecto que tiene todos los permisos del sistema'
        r.tipo = u"sistema"
        r.usuarios.append(u)
        
        #Rol Lider de Proyecto
        rlp = model.Rol()
        rlp.nombre_rol = u"Lider de Proyecto"
        rlp.descripcion = u"Rol Lider de Proyecto, administra componentes" +\
                           "de un proyecto"
        rlp.tipo = u"plantilla"
        model.DBSession.add_all([r, rlp])
        model.DBSession.flush()
        rlp.codigo = model.Rol.generar_codigo(rlp)
        r.codigo = model.Rol.generar_codigo(r)
        
        p = model.Permiso()
        p.nombre_permiso = u'manage'
        p.descripcion = u'This permission give an administrative right to the bearer'
        p.roles.append(r)
        model.DBSession.add(p)
        
        #permisos del sistema
        print "Creando los permisos del sistema..."
        for perm, desc in Permisos.items():
            p = model.Permiso()
            p.nombre_permiso = perm
            p.descripcion = desc
            p.roles.append(r) # Administrador del sistema.
            model.DBSession.add(r) 

        model.DBSession.flush()
        perm = model.DBSession.query(model.Permiso).filter_by(
                               nombre_permiso=u"administrar proyecto").one()
        perm.roles.append(rlp)
        transaction.commit()
        print "Se han creado correctamente las tablas"
    except IntegrityError:
        print 'Warning, there was a problem adding your auth data, it may have already been added:'
        import traceback
        print traceback.format_exc()
        transaction.abort()
        print 'Continuing with bootstrapping...'
        

    # <websetup.bootstrap.after.auth>
