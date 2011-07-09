# -*- coding: utf-8 -*-
"""
Módulo que define el controlador de usuarios miembros
y no miembros de un proyecto.

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
from lpm.controllers.usuario import UsuarioEditForm, UsuarioEditFiller
from lpm.controllers.miembros_proyecto import (MiembrosProyectoTable,
                                               MiembrosProyectoRolesTable,
                                               MiembrosProyectoRolesTableFiller)

from sprox.tablebase import TableBase
from sprox.fillerbase import TableFiller
from sprox.fillerbase import EditFormFiller
from sprox.dojo.formbase import DojoAddRecordForm as AddRecordForm
from sprox.dojo.formbase import DojoEditableForm as EditableForm
from sprox.widgets import PropertySingleSelectField

from repoze.what.predicates import not_anonymous

from sqlalchemy import and_

import transaction

from tg import tmpl_context, request


class NoMiembrosProyectoTable(MiembrosProyectoTable):
    __add_fields__ = None

no_miembros_proyecto_table = NoMiembrosProyectoTable(DBSession)


class NoMiembrosProyectoTableFiller(CustomTableFiller):
    __model__ = Usuario
    __omit_fields__ = ['password', 'telefono', 'nro_documento', 
                       '_password', 'historial_lb', 'roles',
                       'historial_item', 'creado']

    def __actions__(self, obj):
        """Links de acciones para un registro dado"""
        id_proyecto = UrlParser.parse_id(request.url, "proyectos")
        clase = 'actions'
        value = "<div>"
        url_cont = "/proyectos/%d/" % id_proyecto
        id = str(obj.id_usuario)
        value += '<div>' + \
                    '<a href="' + url_cont + "nomiembros/" + id + '" ' + \
                    'class="' + clase + '">Ver</a>' + \
                 '</div><br />'
        
        if PoseePermiso("asignar-desasignar rol", 
                        id_proyecto=id_proyecto).is_met(request.environ):
            value += '<div>' + \
                        '<a href="'+ url_cont + "nomiembros/" + id + \
                        '/rolesdesasignados/" ' + \
                        'class="' + clase + '">Asignar Rol</a>' + \
                     '</div><br />'

        value += '</div>'
        
        return value
        
    def _do_get_provider_count_and_objs(self, id_proyecto=None, **kw):
        """
        Se muestra la lista de usuarios que no tienen algun rol de 
        proyecto para el proyecto en cuestion.
        """
        count, lista = super(NoMiembrosProyectoTableFiller,
                         self)._do_get_provider_count_and_objs(**kw)
        
        filtrados = []
        app = AlgunPermiso(tipo="Proyecto", id_proyecto=id_proyecto)
        for u in lista:
            app.id_usuario = u.id_usuario
            if not app.is_met(request.environ):
                filtrados.append(u)
        return len(filtrados), filtrados

no_miembros_proyecto_table_filler = NoMiembrosProyectoTableFiller(DBSession)

no_miembros_proyecto_roles_table = MiembrosProyectoRolesTable(DBSession)

no_miembros_proyecto_roles_table_filler = MiembrosProyectoRolesTableFiller(DBSession)


#controlador de roles desasignados al usuario, en este proyecto.
class RolesDesasignadosController(RestController):
    table = no_miembros_proyecto_roles_table
    table_filler = no_miembros_proyecto_roles_table_filler
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
        id_proyecto = UrlParser.parse_id(request.url, "proyectos")
        id_usuario = UrlParser.parse_id(request.url, "nomiembros")
        usuario = Usuario.por_id(id_usuario)
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
        atras = "/proyectos/%d/nomiembros/" % id_proyecto
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
        id_usuario = UrlParser.parse_id(request.url, "nomiembros")
        usuario = Usuario.por_id(id_usuario)
        proy = Proyecto.por_id(id_proyecto)
        puede_asignar = PoseePermiso("asignar-desasignar rol", 
                                        id_proyecto=id_proyecto).is_met(request.environ)
        titulo = u"Roles Desasignados para: %s" % usuario.nombre_usuario
        tmpl_context.widget = self.table
        buscar_table_filler = MiembrosProyectoRolesTableFiller(DBSession)
        buscar_table_filler.filtros = kw
        roles = buscar_table_filler.get_value(usuario=usuario, asignados=False,
                                               id_proyecto=id_proyecto, **kw)
        atras = "/proyectos/%d/nomiembros/" % id_proyecto
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
            id_user = UrlParser.parse_id(request.url, "nomiembros")
            id_proyecto = UrlParser.parse_id(request.url, "proyectos")
            user = Usuario.por_id(id_user)
            roles = DBSession.query(Rol).filter(Rol.id_rol.in_(pks)).all()
            for r in roles:
                if r.tipo.find(u"Plantilla") >= 0: #crear rol a partir de plantilla
                    rol_new = Rol.nuevo_rol_desde_plantilla(plantilla=r, 
                                                            id=id_proyecto)
                    rol_new.usuarios.append(user)
                else:
                    r.usuarios.append(user)
            transaction.commit()
            flash("Roles Asignados correctamente")
        else:
            flash("Seleccione por lo menos un rol", "warning")
        return "./"


class NoMiembrosProyectoController(RestController):
    table = no_miembros_proyecto_table
    table_filler = no_miembros_proyecto_table_filler
    action = "./"
    
    #{ Sub-controlador
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
    @expose('lpm.templates.miembros.no_miembros_get_all')
    @expose('json')
    def get_all(self, *args, **kw):
        """ 
        Retorna todos los registros
        Retorna una página HTML si no se especifica JSON
        """

        id_proyecto = UrlParser.parse_id(request.url, "proyectos")
        proy = Proyecto.por_id(id_proyecto)
        titulo = "Lista de Usuarios"

        puede_incorporar = PoseePermiso("asignar-desasignar rol", 
                                        id_proyecto=id_proyecto).is_met(request.environ)

        if request.response_type == 'application/json':
            return self.table_filler.get_value(id_proyecto=id_proyecto,**kw)
        if not getattr(self.table.__class__, '__retrieves_own_value__', False):
            nomiembros = self.table_filler.get_value(id_proyecto=id_proyecto,**kw)
        else:
            nomiembros = []
            
        tmpl_context.widget = self.table
        atras = "/proyectos/%d/" % id_proyecto
        return dict(lista_elementos=nomiembros, 
                    page=titulo, 
                    titulo=titulo, 
                    columnas=self.columnas,
                    opciones=self.opciones,
                    url_action=self.action, 
                    atras=atras,
                    puede_incorporar=puede_incorporar)

    @with_trailing_slash
    @paginate('lista_elementos', items_per_page=5)
    @expose('lpm.templates.miembros.no_miembros_get_all')
    @expose('json')
    def post_buscar(self, *args, **kw):
        id_proyecto = UrlParser.parse_id(request.url, "proyectos")
        proy = Proyecto.por_id(id_proyecto)
        titulo = "Lista de Usuarios"
        puede_incorporar = PoseePermiso("asignar-desasignar rol", 
                                        id_proyecto=id_proyecto).is_met(request.environ)
        tmpl_context.widget = no_miembros_proyecto_table
        buscar_table_filler = NoMiembrosProyectoTableFiller(DBSession)
        buscar_table_filler.filtros = kw
        usuarios = buscar_table_filler.get_value(id_proyecto=id_proyecto,**kw)
        atras = "/proyectos/%d/" % id_proyecto
        return dict(lista_elementos=usuarios, 
                    page=titulo, titulo=titulo, 
                    columnas=self.columnas,
                    opciones=self.opciones,
                    url_action="../", 
                    atras=atras,
                    puede_incorporar=puede_incorporar)
    
    @expose("lpm.templates.miembros.get_one")
    def get_one(self, *args, **kw):
        """
        Muestras los datos de un usuario miembro del proyecto.
        """
        id_proyecto = UrlParser.parse_id(request.url, "proyectos")
        tmpl_context.widget = UsuarioEditForm(DBSession)
        filler = UsuarioEditFiller(DBSession)
        value = filler.get_value(values={'id_usuario': int(args[0])})
        page = u"Usuario %s" % value["nombre_usuario"]
        atras = "/proyectos/%d/" % id_proyecto
        return dict(value=value, page=page, atras=atras)
    
    
    '''    
    @expose()
    def incorporar_seleccionados(self, *args, **kw):
        """ 
        Incorporar al proyecto a los usuarios que fueron seleccionados.
        """
        id_proyecto = UrlParser.parse_id(request.url, "proyectos")
        
        #recuperamos el rol miembro de proyecto
        
        rol = DBSession.query(Rol) \
                       .filter(and_(Rol.id_proyecto == id_proyecto,
                               Rol.nombre_rol == u"Miembro de Proyecto")).one()
        if kw:
            transaction.begin()
            pks = []
            for k, pk in kw.items():
                if not k.isalnum():
                    continue
                pks.append(int(pk))

            usuarios = DBSession.query(Usuario) \
                                .filter(Usuario.id_usuario.in_(pks)).all()
            
            for u in usuarios:
                u.roles.append(rol)
                #rol.usuarios.append(u)
            
            flash("Usuarios incorporados correctamente")
            transaction.commit()
        else:
            flash("Seleccione por lo menos un usuario", "warning")
        
        return "/proyectos/%d/nomiembros/" % id_proyecto
    
    
    @expose()
    def incorporar(self, *args, **kw):
        id_proyecto = UrlParser.parse_id(request.url, "proyectos")
        id_usuario = int(args[0])

        #recuperamos el rol miembro de proyecto
        transaction.begin()
        rol = DBSession.query(Rol) \
                       .filter(and_(Rol.id_proyecto == id_proyecto,
                               Rol.nombre_rol == u"Miembro de Proyecto")).one()

        usuario = Usuario.por_id(id_usuario)
        usuario.roles.append(rol)

        transaction.commit()

        flash("Usuario incorporado correctamente")
        redirect("/proyectos/%d/nomiembros/" % id_proyecto)
    '''

