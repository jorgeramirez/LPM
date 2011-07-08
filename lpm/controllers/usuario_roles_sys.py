# -*- coding: utf-8 -*-
"""
Módulo que define los controladores de asignacion y
desasignacion de roles de sistemas.

@authors:
    - U{Carlos Bellino<mailto:carlosbellino@gmail.com>}
    - U{Nahuel Hernández<mailto:nahuel.11990@gmail.com>}
    - U{Jorge Ramírez<mailto:jorgeramirez1990@gmail.com>}

@since: 1.0
"""
from tg.controllers import RestController
from tg.decorators import (paginate, expose, with_trailing_slash, 
                           without_trailing_slash)
from tg import redirect, request, require, flash, url, validate 

from lpm.model import DBSession, Usuario, Proyecto, Rol
from lpm.lib.sproxcustom import CustomTableFiller
from lpm.lib.authorization import PoseePermiso, AlgunPermiso, Miembro
from lpm.lib.util import UrlParser

from sprox.tablebase import TableBase
from sprox.fillerbase import TableFiller
from sprox.fillerbase import EditFormFiller
from sprox.dojo.formbase import DojoAddRecordForm as AddRecordForm
from sprox.dojo.formbase import DojoEditableForm as EditableForm
from sprox.widgets import PropertySingleSelectField

from repoze.what.predicates import not_anonymous

from sqlalchemy import and_, or_

import transaction

from tg import tmpl_context, request



#tabla de roles asignados/desasignados al usuario.
class UsuarioRolesTable(TableBase):
    __model__ = Rol
    __headers__ = {'nombre_rol' : u'Nombre',
                   'codigo' : u"Código", 'check' : u'Check'
                  }
    __omit_fields__ = ['id_rol', 'permisos', 'usuarios',
                       'id_proyecto', 'id_fase', 'id_tipo_item',
                       'descripcion', 'creado', "tipo"]
    __default_column_width__ = '15em'
    
    __add_fields__ = {'check' : None}
    __xml_fields__ = ['Check']
    __column_widths__ = {'nombre_rol': "35em",
                         'codigo': "35em",
                         '__actions__' : "50em"
                        }
    __field_order__ = ["nombre_rol", "codigo", "check"]

usuario_roles_table = UsuarioRolesTable(DBSession)


class UsuarioRolesTableFiller(CustomTableFiller):
    __model__ = Rol
    __add_fields__ = {'check' : None}

    def check(self, obj, **kw):
        #id
        checkbox = '<input type="checkbox" class="checkbox_tabla" id="' + str(obj.id_rol) + '"/>'
        return checkbox
    
    def __actions__(self, obj):
        """Links de acciones para un registro dado"""
        clase = 'actions'
        value = "<div>"
        value += '<div>' + \
                    '<a href="/roles/' + str(obj.id_rol) + '" ' + \
                    'class="' + clase + '">Ver</a>' + \
                 '</div><br />'
        value += "</div>"
        return value

    def _do_get_provider_count_and_objs(self, usuario=None, 
                                        asignados=True, **kw):
        count, lista = super(UsuarioRolesTableFiller,
                         self)._do_get_provider_count_and_objs(**kw)
        
        roles = []
        
        if not asignados:
            for r in lista:
                if r.tipo == u"Sistema" and r not in usuario.roles:
                    roles.append(r)
        else:
            for r in usuario.roles:
                if r.tipo == u"Sistema" and r in lista:
                    roles.append(r)

        return len(roles), roles
    
    

usuario_roles_table_filler = UsuarioRolesTableFiller(DBSession)


#controlador de roles de sistema asignados al usuario.
class UsuarioRolesAsignadosController(RestController):
    table = usuario_roles_table
    table_filler = usuario_roles_table_filler
    action = "./"

  
    opciones = dict(codigo= u'Código',
                    nombre_rol= u'Nombre'
                    )
    columnas = dict(codigo='texto',
                    nombre_rol='texto'
                    )
    
    #{ Métodos
    @with_trailing_slash
    @paginate('lista_elementos', items_per_page=5)
    @expose('lpm.templates.miembros.roles_asignados_get_all')
    @expose('json')
    def get_all(self, *args, **kw):
        """ 
        Retorna todos los registros
        Retorna una página HTML si no se especifica JSON
        """
        id_usuario = UrlParser.parse_id(request.url, "usuarios")
        usuario = Usuario.por_id(id_usuario)
        puede_desasignar = PoseePermiso("asignar-desasignar rol") \
                                        .is_met(request.environ)
        
        titulo = "Roles de Sistema para: %s" % usuario.nombre_usuario

        if request.response_type == 'application/json':
            return self.table_filler.get_value(usuario=usuario, **kw)
        if not getattr(self.table.__class__, '__retrieves_own_value__', False):
            roles = self.table_filler.get_value(usuario=usuario, **kw)
        else:
            roles = []
            
        tmpl_context.widget = self.table
        atras = "/usuarios/"
        return dict(lista_elementos=roles, 
                    page=titulo, 
                    titulo=titulo, 
                    columnas=self.columnas,
                    opciones=self.opciones,
                    url_action=self.action, 
                    atras=atras,
                    puede_desasignar=puede_desasignar)

    @with_trailing_slash
    @paginate('lista_elementos', items_per_page=5)
    @expose('lpm.templates.miembros.roles_asignados_get_all')
    @expose('json')
    def post_buscar(self, *args, **kw):
        id_usuario = UrlParser.parse_id(request.url, "usuarios")
        usuario = Usuario.por_id(id_usuario)
        puede_desasignar = PoseePermiso("asignar-desasignar rol") \
                                        .is_met(request.environ)
        
        titulo = "Roles de Sistema para: %s" % usuario.nombre_usuario

        tmpl_context.widget = self.table
        buscar_table_filler = UsuarioRolesTableFiller(DBSession)
        buscar_table_filler.filtros = kw
        usuarios = buscar_table_filler.get_value(usuario=usuario, **kw)
        atras = "/usuarios/"
        return dict(lista_elementos=usuarios, 
                    page=titulo, 
                    titulo=titulo, 
                    columnas=self.columnas,
                    opciones=self.opciones,
                    url_action="../", 
                    atras=atras,
                    puede_desasignar=puede_desasignar)

    #@expose('lpm.templates.miembros.roles_asignados_get_all')
    @expose()
    def desasignar_roles(self, *args, **kw):
        """ Desasigna los roles seleccionados a un usuario """
        if kw:
            pks = []
            for k, pk in kw.items():
                if not k.isalnum():
                    continue
                pks.append(int(pk))
            transaction.begin()
            id_user = UrlParser.parse_id(request.url, "usuarios")
            user = Usuario.por_id(id_user)
            c = 0
            while c < len(user.roles):
                if user.roles[c].id_rol in pks:
                    del user.roles[c]
                else:
                    c += 1
            transaction.commit()
        
        flash("Roles Desasignados correctamente")
        return "./"
    



#controlador de roles de sistema desasignados al usuario.
class UsuarioRolesDesasignadosController(RestController):
    table = usuario_roles_table
    table_filler = usuario_roles_table_filler
    action = "./"

  
    opciones = dict(codigo= u'Código',
                    nombre_rol= u'Nombre'
                    )
    columnas = dict(codigo='texto',
                    nombre_rol='texto'
                    )
    
    #{ Métodos
    @with_trailing_slash
    @paginate('lista_elementos', items_per_page=5)
    @expose('lpm.templates.miembros.roles_desasignados_get_all')
    @expose('json')
    def get_all(self, *args, **kw):
        """ 
        Retorna todos los registros
        Retorna una página HTML si no se especifica JSON
        """
        id_usuario = UrlParser.parse_id(request.url, "usuarios")
        usuario = Usuario.por_id(id_usuario)
        puede_asignar = PoseePermiso("asignar-desasignar rol") \
                                        .is_met(request.environ)
        
        titulo = "Roles Desasignados de Sistema para: %s" % usuario.nombre_usuario
                                        
        if request.response_type == 'application/json':
            return self.table_filler.get_value(usuario=usuario, 
                                                asignados=False,
                                                **kw)
        if not getattr(self.table.__class__, '__retrieves_own_value__', False):
            roles = self.table_filler.get_value(usuario=usuario, 
                                                asignados=False,
                                                **kw)
        else:
            roles = []
            
        tmpl_context.widget = self.table
        atras = "/usuarios/"
        return dict(lista_elementos=roles, 
                    page=titulo, 
                    titulo=titulo, 
                    columnas=self.columnas,
                    opciones=self.opciones,
                    url_action=self.action, 
                    atras=atras,
                    puede_asignar=puede_asignar)

    @with_trailing_slash
    @paginate('lista_elementos', items_per_page=5)
    @expose('lpm.templates.miembros.roles_desasignados_get_all')
    @expose('json')
    def post_buscar(self, *args, **kw):
        id_usuario = UrlParser.parse_id(request.url, "usuarios")
        usuario = Usuario.por_id(id_usuario)
        puede_asignar = PoseePermiso("asignar-desasignar rol") \
                                        .is_met(request.environ)
        
        titulo = "Roles Desasignados de Sistema para: %s" % usuario.nombre_usuario
        tmpl_context.widget = self.table
        buscar_table_filler = UsuarioRolesTableFiller(DBSession)
        buscar_table_filler.filtros = kw
        roles = buscar_table_filler.get_value(usuario=usuario, 
                                                asignados=False,
                                                **kw)
        atras = "/usuarios/"
        return dict(lista_elementos=roles, 
                    page=titulo, 
                    titulo=titulo, 
                    columnas=self.columnas,
                    opciones=self.opciones,
                    url_action="../", 
                    atras=atras,
                    puede_asignar=puede_asignar)

    @expose()
    def asignar_roles(self, *args, **kw):
        """ Asigna los roles seleccionados a un usuario """

        if kw:
            pks = []
            for k, pk in kw.items():
                if not k.isalnum():
                    continue
                pks.append(int(pk))
            transaction.begin()
            id_user = UrlParser.parse_id(request.url, "usuarios")
            user = Usuario.por_id(id_user)
            roles = DBSession.query(Rol).filter(Rol.id_rol.in_(pks)).all()
            for r in roles:
                r.usuarios.append(user)
            transaction.commit()
        flash("Roles Asignados correctamente")
        return "./"

