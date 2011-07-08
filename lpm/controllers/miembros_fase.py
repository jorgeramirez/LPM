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

from lpm.model import DBSession, Usuario, Proyecto, Rol, Fase
from lpm.lib.sproxcustom import CustomTableFiller
from lpm.lib.authorization import PoseePermiso, AlgunPermiso, Miembro
from lpm.lib.util import UrlParser
from lpm.controllers.usuario import UsuarioEditForm, UsuarioEditFiller
from lpm.controllers.miembros_proyecto import (MiembrosProyectoTable,
                                               MiembrosProyectoRolesTable)

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


miembros_fase_table = MiembrosProyectoTable(DBSession)


class MiembrosFaseTableFiller(CustomTableFiller):
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
        if id_proyecto:
            url_cont = "/proyectos/%d/" % id_proyecto
        else:
            id_proyecto = UrlParser.parse_id(request.url, "proyectos_fase")
            url_cont = "/proyectos_fase/%d/" % id_proyecto
        
        id_fase = UrlParser.parse_id(request.url, "fases")
        url_cont += "fases/%d/"
        url_cont %= id_fase
        
        clase = 'actions'
        value = "<div>"
        value += '<div>' + \
                    '<a href="' + url_cont + "miembrosfase/" + str(obj.id_usuario) + '" ' + \
                    'class="' + clase + '">Ver</a>' + \
                 '</div><br />'
        
        if PoseePermiso("asignar-desasignar rol", 
                        id_proyecto=id_proyecto).is_met(request.environ):
            value += '<div>' + \
                        '<a href="'+ url_cont + "miembrosfase/" + str(obj.id_usuario) + \
                        "/rolesasignados/" '" ' + \
                        'class="' + clase + '">Roles Asig.</a>' + \
                     '</div><br />'
            value += '<div>' + \
                        '<a href="'+ url_cont + "miembrosfase/" + str(obj.id_usuario) + \
                        "/rolesdesasignados/" '" ' + \
                        'class="' + clase + '">Roles Desasig.</a>' + \
                     '</div><br />'
        value += '</div>'
        
        return value
        
    def _do_get_provider_count_and_objs(self, id_fase=None, **kw):
        """
        Se muestra la lista de usuario si se tiene un permiso 
        necesario. Caso contrario se muestra solo su usuario
        """
        count, lista = super(MiembrosFaseTableFiller,
                         self)._do_get_provider_count_and_objs(**kw)
        
        filtrados = []
        fase = Fase.por_id(id_fase)
        for u in lista:
            if Miembro(id_fase=id_fase, 
                       id_usuario=u.id_usuario).is_met(request.environ):
                filtrados.append(u)
        return len(filtrados), filtrados

miembros_fase_table_filler = MiembrosFaseTableFiller(DBSession)


#tabla de roles asignados/desasignados al usuario.
miembros_fase_roles_table = MiembrosProyectoRolesTable(DBSession)


class MiembrosFaseRolesTableFiller(CustomTableFiller):
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
                                        id_fase=None, **kw):
        count, lista = super(MiembrosFaseRolesTableFiller,
                         self)._do_get_provider_count_and_objs(**kw)
        
        roles = []
        
        if not asignados:
            roles_fase = DBSession.query(Rol) \
                                  .filter(or_(and_(Rol.tipo == u"Fase",
                                          Rol.id_fase == id_fase),
                                          and_(Rol.tipo == u"Plantilla fase")
                                               )).all()
            for r in roles_fase:
                if r not in usuario.roles:
                    roles.append(r)
        else:
            if id_fase:
                for r in usuario.roles:
                    if r.tipo == "Fase" and r.id_fase == id_fase:
                        roles.append(r)

        return len(roles), roles
    
    

miembros_fase_roles_table_filler = MiembrosFaseRolesTableFiller(DBSession)


#controlador de roles asignados al usuario.
class RolesAsignadosController(RestController):
    table = miembros_fase_roles_table
    table_filler = miembros_fase_roles_table_filler
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
        id_fase = UrlParser.parse_id(request.url, "fases")
        id_usuario = UrlParser.parse_id(request.url, "miembrosfase")
        usuario = Usuario.por_id(id_usuario)
        fase = Fase.por_id(id_fase)
        puede_desasignar = PoseePermiso("asignar-desasignar rol", 
                                        id_fase=id_fase).is_met(request.environ)
        
        titulo = "Roles de: %s" % usuario.nombre_usuario

        if request.response_type == 'application/json':
            return self.table_filler.get_value(usuario=usuario, 
                                               id_fase=id_fase, **kw)
        if not getattr(self.table.__class__, '__retrieves_own_value__', False):
            roles = self.table_filler.get_value(usuario=usuario, 
                                               id_fase=id_fase, **kw)
        else:
            roles = []
            
        tmpl_context.widget = self.table
        atras = "../../"
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
        id_fase = UrlParser.parse_id(request.url, "fases")
        id_usuario = UrlParser.parse_id(request.url, "miembrosfase")
        usuario = Usuario.por_id(id_usuario)
        
        fase = Fase.por_id(id_fase)
        puede_desasignar = PoseePermiso("asignar-desasignar rol", 
                                        id_fase=id_fase).is_met(request.environ)
        
        titulo = "Roles de: %s" % usuario.nombre_usuario
        tmpl_context.widget = self.table
        buscar_table_filler = MiembrosFaseRolesTableFiller(DBSession)
        buscar_table_filler.filtros = kw
        usuarios = buscar_table_filler.get_value(usuario=usuario, 
                                                 id_fase=id_fase, **kw)

        atras = "../../"
        return dict(lista_elementos=usuarios, 
                    page=titulo, 
                    titulo=titulo, 
                    columnas=self.columnas,
                    opciones=self.opciones,
                    comboboxes=self.comboboxes,
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
            id_user = UrlParser.parse_id(request.url, "miembrosfase")
            user = Usuario.por_id(id_user)
            c = 0
            while c < len(user.roles):
                r = user.roles[c]
                if r.id_rol in pks:
                    if r.nombre_rol == "Miembro de Fase":
                        msg = "No puedes eliminar el rol {nr}. Si deseas "
                        msg += "que el usuario deje de ser miembro, debes "
                        msg += "hacerlo en la pagina de Miembros de la Fase."
                        flash(msg.format(nr=r.nombre_rol), "warning")
                        DBSession.rollback()
                        return "./"
                    del user.roles[c]
                else:
                    c += 1
            transaction.commit()
        
        flash("Roles Desasignados correctamente")
        return "./"
    



#controlador de roles desasignados al usuario.
class RolesDesasignadosController(RestController):
    table = miembros_fase_roles_table
    table_filler = miembros_fase_roles_table_filler
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
    @expose('lpm.templates.miembros.roles_desasignados_get_all')
    @expose('json')
    def get_all(self, *args, **kw):
        """ 
        Retorna todos los registros
        Retorna una página HTML si no se especifica JSON
        """
        id_fase = UrlParser.parse_id(request.url, "fases")
        id_usuario = UrlParser.parse_id(request.url, "miembrosfase")
        usuario = Usuario.por_id(id_usuario)
        fase = Fase.por_id(id_fase)
                                        
        titulo = u"Roles Desasignados para: %s" % usuario.nombre_usuario
        puede_asignar = PoseePermiso("asignar-desasignar rol", 
                                     id_fase=id_fase).is_met(request.environ)
                                        
        if request.response_type == 'application/json':
            return self.table_filler.get_value(usuario=usuario, asignados=False,
                                               id_fase=id_fase, **kw)
        if not getattr(self.table.__class__, '__retrieves_own_value__', False):
            roles = self.table_filler.get_value(usuario=usuario, asignados=False,
                                               id_fase=id_fase, **kw)
        else:
            roles = []
            
        tmpl_context.widget = self.table
        atras = "../../"
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
        id_fase = UrlParser.parse_id(request.url, "fases")
        id_usuario = UrlParser.parse_id(request.url, "miembrosfase")
        usuario = Usuario.por_id(id_usuario)
        fase = Fase.por_id(id_fase)
        
        puede_asignar = PoseePermiso("asignar-desasignar rol", 
                                        id_fase=id_fase).is_met(request.environ)
        titulo = u"Roles Desasignados para: %s" % usuario.nombre_usuario
        tmpl_context.widget = self.table
        buscar_table_filler = MiembrosFaseRolesTableFiller(DBSession)
        buscar_table_filler.filtros = kw
        roles = buscar_table_filler.get_value(usuario=usuario, asignados=False,
                                               id_fase=id_fase, **kw)
        
        atras = "../../"
        return dict(lista_elementos=roles, 
                    page=titulo, 
                    titulo=titulo, 
                    columnas=self.columnas,
                    opciones=self.opciones,
                    comboboxes=self.comboboxes,
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
            id_user = UrlParser.parse_id(request.url, "miembrosfase")
            id_fase = UrlParser.parse_id(request.url, "fases")
            user = Usuario.por_id(id_user)
            roles = DBSession.query(Rol).filter(Rol.id_rol.in_(pks)).all()
            for r in roles:
                if r.tipo.find(u"Plantilla") >= 0: #crear rol a partir de plantilla
                    rol_new = Rol.nuevo_rol_desde_plantilla(plantilla=r, 
                                                            id=id_fase)
                    rol_new.usuarios.append(user)
                else:
                    r.usuarios.append(user)
            transaction.commit()
        flash("Roles Asignados correctamente")
        return "./"


class MiembrosFaseController(RestController):
    table = miembros_fase_table
    table_filler = miembros_fase_table_filler
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
        id_fase = UrlParser.parse_id(request.url, "fases")
        fase = Fase.por_id(id_fase)

        titulo = "Miembros de la Fase: %s" % fase.nombre

        puede_remover = PoseePermiso("asignar-desasignar rol", 
                                        id_fase=id_fase).is_met(request.environ)

        if request.response_type == 'application/json':
            return self.table_filler.get_value(id_fase=id_fase,**kw)
        if not getattr(self.table.__class__, '__retrieves_own_value__', False):
            miembros = self.table_filler.get_value(id_fase=id_fase,**kw)
        else:
            miembros = []
            
        tmpl_context.widget = self.table
        
        #atras = "/proyectos/%d/" % id_proyecto
        atras = "../"
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
        id_fase = UrlParser.parse_id(request.url, "fases")
        fase = Fase.por_id(id_fase)

        titulo = "Miembros de la Fase: %s" % fase.nombre
        puede_remover = PoseePermiso("asignar-desasignar rol", 
                                     id_fase=id_fase).is_met(request.environ)
        tmpl_context.widget = miembros_fase_table
        buscar_table_filler = MiembrosFaseTableFiller(DBSession)
        buscar_table_filler.filtros = kw
        usuarios = buscar_table_filler.get_value(id_fase=id_fase,**kw)
        
        #atras = "/proyectos/%d/" % id_proyecto
        atras = "../"
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
        Muestras los datos de un usuario miembro de la fase.
        """
        id_fase = UrlParser.parse_id(request.url, "fases")
        tmpl_context.widget = UsuarioEditForm(DBSession)
        filler = UsuarioEditFiller(DBSession)
        value = filler.get_value(values={'id_usuario': int(args[0])})
        page = u"Usuario %s" % value["nombre_usuario"]
        atras = "../"
        return dict(value=value, page=page, atras=atras)
        
    @expose()
    def remover_seleccionados(self, *args, **kw):
        """ 
        Desasigna miembros de la fase.
        """
        id_fase = UrlParser.parse_id(request.url, "fases")

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
                    if u.roles[c].id_fase == id_fase and \
                       u.roles[c].tipo == u"Fase":
                        del u.roles[c]
                    else:
                        c += 1

            transaction.commit()

        flash("Usuarios removidos correctamente")
        return "../"
    
    #}











