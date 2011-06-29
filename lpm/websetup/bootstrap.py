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
        r.usuarios.append(u)
        
        #Rol Lider de Proyecto
        rlp = model.Rol()
        rlp.nombre_rol = u"Lider de Proyecto"
        rlp.descripcion = u"Rol Lider de Proyecto, administra componentes " +\
                          u"de un proyecto"
        rlp.tipo = u"Plantilla proyecto"
        
        #Rol de Miembro de Proyecto
        rmp = model.Rol()
        rmp.nombre_rol = u"Miembro de Proyecto"
        rmp.descripcion = u"Rol Miembro de Proyecto, indica si un usuario" + \
                          u"es miembro de un proyecto"
        rmp.tipo = u"Plantilla proyecto"

        #Rol de Miembro de Fase
        rmf = model.Rol()
        rmf.nombre_rol = u"Miembro de Fase"
        rmf.descripcion = u"Rol Miembro de Fase, indica si un usuario" + \
                          u"es miembro de una fase"
        rmf.tipo = u"Plantilla fase"
        
        
        #Rol de Miembro de Tipo de Ítem
        rmti = model.Rol()
        rmti.nombre_rol = u"Miembro de Tipo Ítem"
        rmti.descripcion = u"Rol Miembro de Tipo Ítem, indica si un usuario" + \
                          u"es miembro de un tipo de ítem"
        rmti.tipo = u"Plantilla tipo ítem"        


        model.DBSession.add_all([r, rlp, rmp, rmf, rmti])
        model.DBSession.flush()
        rlp.codigo = model.Rol.generar_codigo(rlp)
        r.codigo = model.Rol.generar_codigo(r)
        rmp.codigo = model.Rol.generar_codigo(rmp)
        rmf.codigo = model.Rol.generar_codigo(rmf)
        rmti.codigo = model.Rol.generar_codigo(rmti)
        
        #permisos del sistema
        print "Creando los permisos del sistema..."
        for perm in Permisos:
            p = model.Permiso()
            p.nombre_permiso = perm['nombre']
            p.descripcion = perm['descripcion']
            p.tipo = perm['tipo']
            p.roles.append(r) # Administrador del sistema.
            
            if (perm['tipo'] != u'Sistema'):
                if perm["nombre"] == u"miembro":
                    p.roles.append(rmp)
                    p.roles.append(rmf)
                    p.roles.append(rmti)
                    continue
                p.roles.append(rlp) #Líder de Proyecto.


        model.DBSession.flush()
        transaction.commit()
        print "Se han creado correctamente las tablas"
    except IntegrityError:
        print 'Warning, there was a problem adding your auth data, it may have already been added:'
        import traceback
        print traceback.format_exc()
        transaction.abort()
        print u'Ocurrió una excepción...'
        

    # <websetup.bootstrap.after.auth>
