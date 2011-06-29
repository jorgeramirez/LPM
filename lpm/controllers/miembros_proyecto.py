# -*- coding: utf-8 -*-
"""
Módulo que define el controlador de usuarios miembros
de un proyecto.

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
from lpm.lib.authorization import PoseePermiso, AlgunPermiso
from lpm.lib.util import UrlParser
from lpm.controllers.usuario import UsuarioEditForm, UsuarioEditFiller

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


class MiembrosProyectoTable(TableBase):
    __model__ = Usuario
    __headers__ = {'nombre_usuario' : u'Nombre de Usuario', 'email' : u"E-mail",
                   'nombre' : u"Nombre", 'apellido' : u"Apellido",
                   'check' : u'Check'
                  }
    __add_fields__ = {'check' : None}
    __xml_fields__ = ['Check']
    __omit_fields__ = ['id_usuario', 'password', 'telefono', 'nro_documento', 
                       '_password', 'historial_lb', 'roles',
                       'historial_item', 'creado']
    __default_column_width__ = '15em'
    __column_widths__ = {'email': "35em",
                         '__actions__' : "50em"
                        }
    
miembros_proyecto_table = MiembrosProyectoTable(DBSession)


class MiembrosProyectoTableFiller(CustomTableFiller):
    __model__ = Usuario
    __omit_fields__ = ['password', 'telefono', 'nro_documento', 
                       '_password', 'historial_lb', 'roles',
                       'historial_item', 'creado']
    __add_fields__ = {'check' : None}

    def check(self, obj, **kw):
        #id
        checkbox = '<input type="checkbox" class="checkbox_tabla" id="' + str(obj.id_usuario) + '"/>'
        return checkbox

    def __actions__(self, obj):
        """Links de acciones para un registro dado"""
        id_proyecto = UrlParser.parse_id(request.url, "proyectos")
        clase = 'actions'
        value = "<div>"
        url_cont = "/proyectos/%d/" % id_proyecto
        value += '<div>' + \
                    '<a href="' + url_cont + "miembros/" + str(obj.id_usuario) + '" ' + \
                    'class="' + clase + '">Ver</a>' + \
                 '</div><br />'
        
        if PoseePermiso("asignar-desasignar rol", 
                        id_proyecto=id_proyecto).is_met(request.environ):
            value += '<div>' + \
                        '<a href="'+ url_cont + "miembros/" + str(obj.id_usuario) + \
                        "/rolesasignados/" '" ' + \
                        'class="' + clase + '">Roles Asig.</a>' + \
                     '</div><br />'
            value += '<div>' + \
                        '<a href="'+ url_cont + "miembros/" + str(obj.id_usuario) + \
                        "/rolesdesasignados/" '" ' + \
                        'class="' + clase + '">Roles Desasig.</a>' + \
                     '</div><br />'
        value += '</div>'
        
        return value
        
    def _do_get_provider_count_and_objs(self, id_proyecto=None, **kw):
        """
        Se muestra la lista de usuario si se tiene un permiso 
        necesario. Caso contrario se muestra solo su usuario
        """
        count, lista = super(MiembrosProyectoTableFiller,
                         self)._do_get_provider_count_and_objs(**kw)
        
        filtrados = []
        for u in lista:
            if AlgunPermiso(tipo="Proyecto", id_proyecto=id_proyecto,
                            id_usuario=u.id_usuario):
                filtrados.append(u)
        return len(filtrados), filtrados

miembros_proyecto_table_filler = MiembrosProyectoTableFiller(DBSession)



#tabla de roles asignados/desasignados al usuario.
class MiembrosProyectoRolesTable(TableBase):
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

miembros_proyecto_roles_table = MiembrosProyectoRolesTable(DBSession)


class MiembrosProyectoRolesTableFiller(CustomTableFiller):
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

    def _do_get_provider_count_and_objs(self, usuario=None, asignados=True, 
                                        id_proyecto=None, **kw):
        count, lista = super(MiembrosProyectoRolesTableFiller,
                         self)._do_get_provider_count_and_objs(**kw)
        
        roles = []
        
        if not asignados:
            roles_proy = DBSession.query(Rol) \
                                  .filter(or_(and_(Rol.tipo == ("Proyecto"),
                                          Rol.id_proyecto == id_proyecto),
                                          and_(Rol.tipo == "Plantilla proyecto",
                                               Rol.nombre_rol != u"Miembro de Proyecto",
                                               Rol.nombre_rol != u"Lider de Proyecto")
                                               )).all()
            for r in roles_proy:
                if r not in usuario.roles:
                    roles.append(r)
        else:
            roles = usuario.roles
            if id_proyecto:
                for r in usuario.roles:
                    if r.tipo == "Proyecto" and r.id_proyecto == id_proyecto:
                        roles.append(r)

        return len(roles), roles
    
    

miembros_proyecto_roles_table_filler = MiembrosProyectoRolesTableFiller(DBSession)


#controlador de roles asignados al usuario.
class RolesAsignadosController(RestController):
    table = miembros_proyecto_roles_table
    table_filler = miembros_proyecto_roles_table_filler
    action = "./"

  
    opciones = dict(codigo= u'Código',
                    nombre_rol= u'Nombre',
                    tipo=u'Tipo'
                    )
    columnas = dict(codigo='texto',
                    nombre_rol='texto',
                    tipo='combobox'
                    )
    comboboxes = dict(tipo=Rol.tipos_posibles)
    
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
        id_proyecto = UrlParser.parse_id(request.url, "proyectos")
        usuario = Usuario.by_user_name(request.credentials["repoze.what.userid"])
        proy = Proyecto.por_id(id_proyecto)
        puede_desasignar = PoseePermiso("asignar-desasignar rol", 
                                        id_proyecto=id_proyecto).is_met(request.environ)
        
        titulo = "Roles de: %s" % usuario.nombre_usuario

        if request.response_type == 'application/json':
            return self.table_filler.get_value(usuario=usuario, 
                                               id_proyecto=id_proyecto, **kw)
        if not getattr(self.table.__class__, '__retrieves_own_value__', False):
            roles = self.table_filler.get_value(usuario=usuario, 
                                               id_proyecto=id_proyecto, **kw)
        else:
            roles = []
            
        tmpl_context.widget = self.table
        atras = "/proyectos/"
        return dict(lista_elementos=roles, 
                    page=titulo, 
                    titulo=titulo, 
                    columnas=self.columnas,
                    opciones=self.opciones,
                    comboboxes=self.comboboxes,
                    url_action=self.action, 
                    atras=atras,
                    puede_desasignar=puede_desasignar)

    @with_trailing_slash
    @paginate('lista_elementos', items_per_page=5)
    @expose('lpm.templates.miembros.roles_asignados_get_all')
    @expose('json')
    def post_buscar(self, *args, **kw):
        id_proyecto = UrlParser.parse_id(request.url, "proyectos")
        usuario = Usuario.by_user_name(request.credentials["repoze.what.userid"])
        proy = Proyecto.por_id(id_proyecto)
        puede_desasignar = PoseePermiso("asignar-desasignar rol", 
                                        id_proyecto=id_proyecto).is_met(request.environ)
        
        titulo = "Roles de: %s" % usuario.nombre_usuario
        tmpl_context.widget = self.table
        buscar_table_filler = MiembrosProyectoRolesTableFiller(DBSession)
        buscar_table_filler.filtros = kw
        usuarios = buscar_table_filler.get_value(usuario=usuario, 
                                                 id_proyecto=id_proyecto, **kw)
        atras = "/proyectos/"
        return dict(lista_elementos=usuarios, 
                    page=titulo, 
                    titulo=titulo, 
                    columnas=self.columnas,
                    opciones=self.opciones,
                    comboboxes=self.comboboxes,
                    url_action="../", 
                    atras=atras,
                    puede_desasignar=puede_desasignar)

    @expose('lpm.templates.miembros.roles_asignados_get_all')
    def desasignar_roles(self, *args, **kw):
        """ Desasigna los roles seleccionados a un usuario """
        if kw:
            pks = []
            for k, pk in kw.items():
                if not k.isalnum():
                    continue
                pks.append(int(pk))
            transaction.begin()
            user = Usuario.por_id(int(args[0]))
            c = 0
            while c < len(user.roles):
                if user.roles[c].id_rol in pks:
                    del user.roles[c]
                else:
                    c += 1
            transaction.commit()

        return self.get_all(*args, **kw)   
    



#controlador de roles desasignados al usuario.
class RolesDesasignadosController(RolesAsignadosController):
    
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
        id_proyecto = UrlParser.parse_id(request.url, "proyectos")
        usuario = Usuario.by_user_name(request.credentials["repoze.what.userid"])
        proy = Proyecto.por_id(id_proyecto)
        titulo = u"Roles Desasignados para: %s" % usuario.nombre_usuario
        puede_asignar = PoseePermiso("asignar-desasignar rol", 
                                        id_proyecto=id_proyecto).is_met(request.environ)
                                        
        if request.response_type == 'application/json':
            return self.table_filler.get_value(usuario=usuario, asignados=False,
                                               id_proyecto=id_proyecto, **kw)
        if not getattr(self.table.__class__, '__retrieves_own_value__', False):
            roles = self.table_filler.get_value(usuario=usuario, asignados=False,
                                               id_proyecto=id_proyecto, **kw)
        else:
            roles = []
            
        tmpl_context.widget = self.table
        atras = "/proyectos/"
        return dict(lista_elementos=roles, 
                    page=titulo, 
                    titulo=titulo, 
                    columnas=self.columnas,
                    opciones=self.opciones,
                    comboboxes=self.comboboxes,
                    url_action=self.action, 
                    atras=atras,
                    puede_asignar=puede_asignar)

    @with_trailing_slash
    @paginate('lista_elementos', items_per_page=5)
    @expose('lpm.templates.miembros.roles_desasignados_get_all')
    @expose('json')
    def post_buscar(self, *args, **kw):
        id_proyecto = UrlParser.parse_id(request.url, "proyectos")
        usuario = Usuario.by_user_name(request.credentials["repoze.what.userid"])
        proy = Proyecto.por_id(id_proyecto)
        puede_asignar = PoseePermiso("asignar-desasignar rol", 
                                        id_proyecto=id_proyecto).is_met(request.environ)
        titulo = u"Roles Desasignados para: %s" % usuario.nombre_usuario
        tmpl_context.widget = self.table
        buscar_table_filler = MiembrosProyectoRolesTableFiller(DBSession)
        buscar_table_filler.filtros = kw
        roles = buscar_table_filler.get_value(usuario=usuario, asignados=False,
                                               id_proyecto=id_proyecto, **kw)
        atras = "/proyectos/"
        return dict(lista_elementos=roles, 
                    page=titulo, 
                    titulo=titulo, 
                    columnas=self.columnas,
                    opciones=self.opciones,
                    comboboxes=self.comboboxes,
                    url_action="../", 
                    atras=atras,
                    puede_asignar=puede_asignar)

    @expose('lpm.templates.miembros.roles_desasignados_get_all')
    def asignar_roles(self, *args, **kw):
        """ Asigna los roles seleccionados a un usuario """

        if kw:
            pks = []
            for k, pk in kw.items():
                if not k.isalnum():
                    continue
                pks.append(int(pk))
            transaction.begin()
            user = Usuario.por_id(int(args[0]))
            roles = DBSession.query(Rol).filter(Rol.id_rol.in_(pks)).all()
            for r in roles:
                if r.tipo.find("Plantilla") >= 0: #crear rol a partir de plantilla
                    id = None
                    for k in ["id_proyecto", "id_fase", "id_tipo_item"]:
                        if kw.has_key(k):
                            id = kw[k]
                            break
                    rol_new = Rol.nuevo_rol_desde_plantilla(plantilla=r, id=id)
                    rol_new.usuarios.append(user)
                else:
                    r.usuarios.append(user)
            transaction.commit()
        return self.get_all(*args, **kw)


class MiembrosProyectoController(RestController):
    table = miembros_proyecto_table
    table_filler = miembros_proyecto_table_filler
    action = "./"
    
    #{Sub Controladores
    rolesasignados = RolesAsignadosController()
    rolesdesasignados = RolesDesasignadosController()
    
    #para el form de busqueda
    opciones = dict(nombre_usuario="Nombre de Usuario", 
                    nombre="Nombre", 
                    apellido="Apellido",
                    email="Email")
                    
    columnas = dict(nombre_usuario="texto", 
                    nombre="texto", 
                    apellido="texto",
                    email="texto")


    #{ Métodos
    @with_trailing_slash
    @paginate('lista_elementos', items_per_page=5)
    @expose('lpm.templates.miembros.get_all')
    @expose('json')
    def get_all(self, *args, **kw):
        """ 
        Retorna todos los registros
        Retorna una página HTML si no se especifica JSON
        """

        id_proyecto = UrlParser.parse_id(request.url, "proyectos")
        proy = Proyecto.por_id(id_proyecto)
        titulo = "Miembros del Proyecto: %s" % proy.nombre

        puede_remover = PoseePermiso("asignar-desasignar rol", 
                                        id_proyecto=id_proyecto).is_met(request.environ)

        if request.response_type == 'application/json':
            return self.table_filler.get_value(id_proyecto=id_proyecto,**kw)
        if not getattr(self.table.__class__, '__retrieves_own_value__', False):
            miembros = self.table_filler.get_value(id_proyecto=id_proyecto,**kw)
        else:
            miembros = []
            
        tmpl_context.widget = self.table
        atras = "/proyectos/"
        return dict(lista_elementos=miembros, 
                    page=titulo, 
                    titulo=titulo, 
                    columnas=self.columnas,
                    opciones=self.opciones,
                    url_action=self.action, 
                    atras=atras,
                    puede_remover=puede_remover)

    @with_trailing_slash
    @paginate('lista_elementos', items_per_page=5)
    @expose('lpm.templates.miembros.get_all')
    @expose('json')
    def post_buscar(self, *args, **kw):
        id_proyecto = UrlParser.parse_id(request.url, "proyectos")
        proy = Proyecto.por_id(id_proyecto)
        titulo = "Miembros del Proyecto: %s" % proy.nombre
        puede_remover = PoseePermiso("asignar-desasignar rol", 
                                        id_proyecto=id_proyecto).is_met(request.environ)
        tmpl_context.widget = miembros_proyecto_table
        buscar_table_filler = MiembrosProyectoTableFiller(DBSession)
        buscar_table_filler.filtros = kw
        usuarios = buscar_table_filler.get_value(id_proyecto=id_proyecto,**kw)
        atras = "/proyectos/"
        return dict(lista_elementos=usuarios, 
                    page=titulo, titulo=titulo, 
                    columnas=self.columnas,
                    opciones=self.opciones,
                    url_action="../", 
                    atras=atras,
                    puede_remover=puede_remover)
    
    @expose("lpm.templates.miembros.get_one")
    def get_one(self, *args, **kw):
        """
        Muestras los datos de un usuario miembro del proyecto.
        """
        tmpl_context.widget = UsuarioEditForm(DBSession)
        filler = UsuarioEditFiller(DBSession)
        value = filler.get_value(values={'id_usuario': int(args[0])})
        page = u"Usuario %s" % value["nombre_usuario"]
        return dict(value=value, page=page)
        
    @expose()
    def remover_seleccionados(self, *args, **kw):
        """ 
        Desasigna miembros del proyecto.
        """
        id_proyecto = UrlParser.parse_id(request.url, "proyectos")
        
        #recuperamos el rol miembro de proyecto
        rol = DBSession.query(Rol) \
                       .filter(and_(Rol.id_proyecto == id_proyecto,
                               Rol.nombre_rol == u"Miembro de Proyecto")).first()
        if kw:
            pks = []
            for k, pk in kw.items():
                if not k.isalnum():
                    continue
                pks.append(int(pk))

            transaction.begin()
            usuarios = DBSession.query(Usuario) \
                                .filter(Usuario.id_usuario.in_(pks)).all()
            for u in usuarios:
                c = 0
                while c < len(u.roles):
                    if u.roles[c].id_rol == rol.id_rol:
                        del u.roles[c]
                    else:
                        c += 1

            transaction.commit()

        flash("Usuarios removidos correctamente")
        return "/proyectos/%d/miembros/" % id_proyecto
    
    #}











