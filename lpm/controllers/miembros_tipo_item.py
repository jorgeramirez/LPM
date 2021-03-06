# -*- coding: utf-8 -*-
"""
Módulo que define el controlador de usuarios miembros
de un tipo de ítem.

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

from lpm.model import DBSession, Usuario, Proyecto, Rol, Fase, TipoItem
from lpm.lib.sproxcustom import CustomTableFiller
from lpm.lib.authorization import PoseePermiso, AlgunPermiso, Miembro
from lpm.lib.util import UrlParser
from lpm.controllers.usuario import UsuarioEditForm, UsuarioEditFiller
from lpm.controllers.miembros_proyecto import (MiembrosProyectoTable,
                                               MiembrosProyectoRolesTable,
                                               select, selector,
                                               RolVerEditForm,
                                               rol_ver_edit_filler)

from sprox.tablebase import TableBase
from sprox.fillerbase import TableFiller
from sprox.fillerbase import EditFormFiller
from sprox.dojo.formbase import DojoAddRecordForm as AddRecordForm
from sprox.dojo.formbase import DojoEditableForm as EditableForm
from sprox.widgets import PropertySingleSelectField

from tw.forms.fields import TextArea

from repoze.what.predicates import not_anonymous

from sqlalchemy import and_, or_

import transaction

from tg import tmpl_context, request


miembros_tipo_table = MiembrosProyectoTable(DBSession)


class MiembrosTipoTableFiller(CustomTableFiller):
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
        clase = 'actions'
        value = "<div>"
        url = "./"
        if UrlParser.parse_nombre(request.url, "post_buscar"):
            url = "../"
            
        value += '<div>' + \
                    '<a href="' + url + str(obj.id_usuario) + '/" ' + \
                    'class="' + clase + '">Ver</a>' + \
                 '</div><br />'

        id_tipo_item = UrlParser.parse_id(request.url, "tipositems")
        if PoseePermiso("asignar-desasignar rol", 
                        id_tipo_item=id_tipo_item).is_met(request.environ):
            value += '<div>' + \
                        '<a href="./'+ str(obj.id_usuario) + \
                        "/rolesasignados/" '" ' + \
                        'class="' + clase + '">Roles Asig.</a>' + \
                     '</div><br />'
            value += '<div>' + \
                        '<a href="./' + str(obj.id_usuario) + \
                        "/rolesdesasignados/" '" ' + \
                        'class="' + clase + '">Roles Desasig.</a>' + \
                     '</div><br />'
        value += '</div>'
        
        return value
        
    def _do_get_provider_count_and_objs(self, id_tipo_item=None, **kw):
        """
        Se muestra la lista de usuario miembros
        """
        count, lista = super(MiembrosTipoTableFiller,
                         self)._do_get_provider_count_and_objs(**kw)
        
        #filtrados = []
        filtrados = lista
        #apti = AlgunPermiso(tipo="Tipo", id_tipo_item=id_tipo_item)
        #for u in lista:
        #    apti.id_usuario = u.id_usuario
        #    if apti:
        #        filtrados.append(u)
        return len(filtrados), filtrados

miembros_tipo_table_filler = MiembrosTipoTableFiller(DBSession)


#tabla de roles asignados/desasignados al usuario.
miembros_tipo_roles_table = MiembrosProyectoRolesTable(DBSession)


class MiembrosTipoRolesTableFiller(CustomTableFiller):
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
        url = "./"
        if UrlParser.parse_nombre(request.url, "post_buscar"):
            url = "../"
        value += '<div>' + \
                    '<a href="' + url + str(obj.id_rol) + '" ' + \
                    'class="' + clase + '">Ver</a>' + \
                 '</div><br />'
        value += "</div>"
        return value

    def _do_get_provider_count_and_objs(self, usuario=None, asignados=True, 
                                        id_tipo_item=None, **kw):
        count, lista = super(MiembrosTipoRolesTableFiller,
                         self)._do_get_provider_count_and_objs(**kw)
        
        roles = []
        
        if not asignados:
            roles_tipo = DBSession.query(Rol) \
                                  .filter(or_(and_(Rol.tipo.like(u"Tipo%"),
                                          Rol.id_tipo_item == id_tipo_item),
                                          and_(Rol.tipo.like(u"Plantilla tipo ítem"))
                                               )).all()
            for r in roles_tipo:
                if r not in usuario.roles:
                    roles.append(r)
        else:
            if id_tipo_item:
                for r in usuario.roles:
                    if r.tipo.find(u"Tipo") >= 0 and r.id_tipo_item == id_tipo_item:
                        roles.append(r)

        return len(roles), roles
    
    

miembros_tipo_roles_table_filler = MiembrosTipoRolesTableFiller(DBSession)


#controlador de roles asignados al usuario.
class RolesAsignadosController(RestController):
    table = miembros_tipo_roles_table
    table_filler = miembros_tipo_roles_table_filler
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
        id_tipo_item = UrlParser.parse_id(request.url, "tipositems")
        id_usuario = UrlParser.parse_id(request.url, "miembrostipo")
        usuario = Usuario.por_id(id_usuario)
        tipo = TipoItem.por_id(id_tipo_item)
        puede_desasignar = PoseePermiso("asignar-desasignar rol", 
                                        id_tipo_item=id_tipo_item).is_met(request.environ)
        
        titulo = u"Roles de: %s" % usuario.nombre_usuario

        if request.response_type == 'application/json':
            return self.table_filler.get_value(usuario=usuario, 
                                               id_tipo_item=id_tipo_item, **kw)
        if not getattr(self.table.__class__, '__retrieves_own_value__', False):
            roles = self.table_filler.get_value(usuario=usuario, 
                                               id_tipo_item=id_tipo_item, **kw)
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
        id_tipo_item = UrlParser.parse_id(request.url, "tipositems")
        id_usuario = UrlParser.parse_id(request.url, "miembrostipo")
        usuario = Usuario.por_id(id_usuario)
        tipo = TipoItem.por_id(id_tipo_item)
        puede_desasignar = PoseePermiso("asignar-desasignar rol", 
                                        id_tipo_item=id_tipo_item).is_met(request.environ)
        
        titulo = u"Roles de: %s" % usuario.nombre_usuario
        tmpl_context.widget = self.table
        buscar_table_filler = MiembrosFaseRolesTableFiller(DBSession)
        buscar_table_filler.filtros = kw
        usuarios = buscar_table_filler.get_value(usuario=usuario, 
                                                 id_tipo_item=id_tipo_item, **kw)

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
            id_user = UrlParser.parse_id(request.url, "miembrostipo")
            user = Usuario.por_id(id_user)
            c = 0
            while c < len(user.roles):
                r = user.roles[c]
                if r.id_rol in pks:
                    if r.nombre_rol == "Miembro de Tipo Item":
                        msg = "No puedes eliminar el rol {nr}. Si deseas "
                        msg += "que el usuario deje de ser miembro, debes "
                        msg += "hacerlo en la pagina de Miembros para este "
                        msg += "tipo de item."
                        flash(msg.format(nr=r.nombre_rol), "warning")
                        DBSession.rollback()
                        return "./"
                    del user.roles[c]
                else:
                    c += 1
            transaction.commit()
            flash("Roles Desasignados correctamente")
        else:
            flash("Seleccione por lo menos un rol", "warning")
        return "./"

    @expose('lpm.templates.rol.get_one')
    def get_one(self, id_rol):
        """Despliega una página para visualizar el rol"""
        tmpl_context.widget = RolVerEditForm(DBSession)
        value = rol_ver_edit_filler.get_value(values={'id_rol': int(id_rol)})
        page = "Rol {nombre}".format(nombre=value["nombre_rol"])
        atras = self.action
        return dict(value=value, page=page, atras=atras)
    



#controlador de roles desasignados al usuario.
class RolesDesasignadosController(RestController):
    table = miembros_tipo_roles_table
    table_filler = miembros_tipo_roles_table_filler
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
        id_tipo_item = UrlParser.parse_id(request.url, "tipositems")
        id_usuario = UrlParser.parse_id(request.url, "miembrostipo")
        usuario = Usuario.por_id(id_usuario)
        tipo = TipoItem.por_id(id_tipo_item)
        puede_asignar = PoseePermiso("asignar-desasignar rol", 
                                        id_tipo_item=id_tipo_item).is_met(request.environ)
                                        
        titulo = u"Roles Desasignados para: %s" % usuario.nombre_usuario
                                        
        if request.response_type == 'application/json':
            return self.table_filler.get_value(usuario=usuario, asignados=False,
                                               id_tipo_item=id_tipo_item, **kw)
        if not getattr(self.table.__class__, '__retrieves_own_value__', False):
            roles = self.table_filler.get_value(usuario=usuario, asignados=False,
                                               id_tipo_item=id_tipo_item, **kw)
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
        id_tipo_item = UrlParser.parse_id(request.url, "tipositems")
        id_usuario = UrlParser.parse_id(request.url, "miembrostipo")
        usuario = Usuario.por_id(id_usuario)
        tipo = TipoItem.por_id(id_tipo_item)
        puede_asignar = PoseePermiso("asignar-desasignar rol", 
                                        id_tipo_item=id_tipo_item).is_met(request.environ)
        titulo = u"Roles Desasignados para: %s" % usuario.nombre_usuario
        tmpl_context.widget = self.table
        buscar_table_filler = MiembrosTipoRolesTableFiller(DBSession)
        buscar_table_filler.filtros = kw
        roles = buscar_table_filler.get_value(usuario=usuario, asignados=False,
                                               id_tipo_item=id_tipo_item, **kw)
        
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
            id_user = UrlParser.parse_id(request.url, "miembrostipo")
            id_tipo_item = UrlParser.parse_id(request.url, "tipositems")
            user = Usuario.por_id(id_user)
            roles = DBSession.query(Rol).filter(Rol.id_rol.in_(pks)).all()
            for r in roles:
                if r.tipo.find(u"Plantilla") >= 0: #crear rol a partir de plantilla
                    rol_new = Rol.nuevo_rol_desde_plantilla(plantilla=r, 
                                                            id=id_tipo_item)
                    rol_new.usuarios.append(user)
                else:
                    r.usuarios.append(user)
            transaction.commit()
            flash("Roles Asignados correctamente")
        else:
            flash("Seleccione por lo menos un rol", "warning")
        return "./"

    @expose('lpm.templates.rol.get_one')
    def get_one(self, id_rol):
        """Despliega una página para visualizar el rol"""
        tmpl_context.widget = RolVerEditForm(DBSession)
        value = rol_ver_edit_filler.get_value(values={'id_rol': int(id_rol)})
        page = "Rol {nombre}".format(nombre=value["nombre_rol"])
        atras = self.action
        return dict(value=value, page=page, atras=atras)


class MiembrosTipoController(RestController):
    table = miembros_tipo_table
    table_filler = miembros_tipo_table_filler
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
        id_tipo_item = UrlParser.parse_id(request.url, "tipositems")
        tipo = TipoItem.por_id(id_tipo_item)

        #titulo = u"Miembros del Tipo de Item: %s" % tipo.nombre
        titulo = "Lista de Usuarios"
        puede_remover = PoseePermiso("asignar-desasignar rol", 
                                      id_tipo_item=id_tipo_item).is_met(request.environ)
        
        if request.response_type == 'application/json':
            return self.table_filler.get_value(id_tipo_item=id_tipo_item,**kw)
        if not getattr(self.table.__class__, '__retrieves_own_value__', False):
            miembros = self.table_filler.get_value(id_tipo_item=id_tipo_item,**kw)
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
        id_tipo_item = UrlParser.parse_id(request.url, "tipositems")
        tipo = TipoItem.por_id(id_tipo_item)

        #titulo = u"Miembros del Tipo de Ítem: %s" % tipo.nombre
        titulo = "Lista de Usuarios"
        puede_remover = PoseePermiso("asignar-desasignar rol", 
                                        id_tipo_item=id_tipo_item).is_met(request.environ)
        tmpl_context.widget = miembros_tipo_table
        buscar_table_filler = MiembrosTipoTableFiller(DBSession)
        buscar_table_filler.filtros = kw
        usuarios = buscar_table_filler.get_value(id_tipo_item=id_tipo_item,**kw)
        
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
        id_tipo_item = UrlParser.parse_id(request.url, "tipositems")
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
        id_tipo_item = UrlParser.parse_id(request.url, "tipositems")
        
        if kw:
            pks = []
            for k, pk in kw.items():
                if not k.isalnum():
                    continue
                pks.append(int(pk))

            transaction.begin()
            usuarios = DBSession.query(Usuario) \
                                .filter(Usuario.id_usuario.in_(pks)).all()
            
            ti = TipoItem.por_id(id_tipo_item)

            nr = u"Lider de Proyecto"
            rlp = DBSession.query(Rol) \
                          .filter(and_(Rol.tipo == u"Proyecto",
                                       Rol.id_proyecto == ti.id_proyecto,
                                       Rol.nombre_rol == nr)).first()

            warning = False
            for u in usuarios:
                if rlp in u.roles and len(rlp.usuarios) == 1:
                    msg = "No puedes eliminar al usuario {nu} porque "
                    msg += "es el {nr}"
                    flash(msg.format(nu=u.nombre_usuario, 
                                     nr=nr), "warning")
                    warning = True
                    continue

                c = 0
                while c < len(u.roles):
                    if u.roles[c].id_tipo_item == id_tipo_item and \
                       u.roles[c].tipo == u"Tipo Ítem":
                        del u.roles[c]
                    else:
                        c += 1

            transaction.commit()
            if not warning:
                flash("Usuarios removidos correctamente")
        else:
            flash("Seleccione por lo menos un usuario", "warning")
        return "../"
    
    #}











