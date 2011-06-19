# -*- coding: utf-8 -*-
"""Setup the LPM application"""
from tg import config

from lpm import model
from lpm.lib.authorization import Permisos

import transaction
import logging

def bootstrap(command, conf, vars):
    """Realiza la creación de las tablas y los contenidos
    por defecto del sistema"""

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
        r.tipo = u"Sistema"
#        r.id_fase = 0
#        r.id_proyecto = 0
#        r.id_tipo_item = 0
        r.usuarios.append(u)
        
        #Rol Lider de Proyecto
        rlp = model.Rol()
        rlp.nombre_rol = u"Lider de Proyecto"
        rlp.descripcion = u"Rol Lider de Proyecto, administra componentes" +\
                           "de un proyecto"
        rlp.tipo = u"Plantilla proyecto"
#        rlp.id_fase = 0
#        rlp.id_proyecto = 0
#        rlp.id_tipo_item = 0
        model.DBSession.add_all([r, rlp])
        model.DBSession.flush()
        rlp.codigo = model.Rol.generar_codigo(rlp)
        r.codigo = model.Rol.generar_codigo(r)
        
        #permisos del sistema
        print "Creando los permisos del sistema..."
        for perm in Permisos:
            p = model.Permiso()
            p.nombre_permiso = perm['nombre']
            p.descripcion = perm['descripcion']
            p.tipo = perm['tipo']
            p.roles.append(r) # Administrador del sistema.
            
            if (perm['tipo'] != u'Sistema'):
                p.roles.append(rlp) #Líder de Proyecto.            

        model.DBSession.flush()
        ####Asignar los permisos para lider de proyecto
        transaction.commit()
        print "Se han creado correctamente las tablas"
    except IntegrityError:
        print 'Warning, there was a problem adding your auth data, it may have already been added:'
        import traceback
        print traceback.format_exc()
        transaction.abort()
        print u'Ocurrió una excepción...'
        

    # <websetup.bootstrap.after.auth>
