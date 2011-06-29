# -*- coding: utf-8 -*-
"""
Módulo que define el controlador de roles de tipos de ítem.

@authors:
    - U{Carlos Bellino<mailto:carlosbellino@gmail.com>}
    - U{Nahuel Hernández<mailto:nahuel.11990@gmail.com>}
    - U{Jorge Ramírez<mailto:jorgeramirez1990@gmail.com>}

@since: 1.0
"""
from tgext.crud import CrudRestController
from tg.controllers import RestController
from tg.decorators import (paginate, expose, with_trailing_slash, 
                           without_trailing_slash)
from tg import redirect, request, require, flash, url, validate

from lpm.controllers.validaciones.rol_validator import RolFormValidator
from lpm.model import (DBSession, Usuario, Rol, Permiso, Proyecto, 
                       Fase, TipoItem)
from lpm.lib.sproxcustom import CustomTableFiller, CustomPropertySingleSelectField
from lpm.lib.sproxcustom import WidgetSelectorDojo, MultipleSelectDojo
from lpm.lib.authorization import PoseePermiso, AlgunPermiso
from lpm.lib.util import UrlParser
from lpm.controllers.rol import (RolTable, SelectorPermisosPlantillaTi,
                                 RolEditFiller)

from sprox.tablebase import TableBase
from sprox.fillerbase import TableFiller
from sprox.fillerbase import EditFormFiller
from sprox.dojo.formbase import DojoAddRecordForm as AddRecordForm
from sprox.dojo.formbase import DojoEditableForm as EditableForm
from sprox.widgets import PropertySingleSelectField

from tw.forms.fields import PasswordField, TextField, TextArea, Button

from repoze.what.predicates import not_anonymous

from tg import tmpl_context, request

import transaction

import urllib


roles_tipo_table = RolTable(DBSession)

class RolesTipoTableFiller(CustomTableFiller):
    __model__ = Rol
    __omit_fields__ = ['permisos', 'usuarios',
                       'id_proyecto', 'id_fase', 'id_tipo_item',
                       'descripcion']

    def __actions__(self, obj):
        """Links de acciones para un registro dado"""
        value = '<div>'
        clase = 'actions'
        
        perm_mod = PoseePermiso('modificar rol', id_tipo_item=obj.id_tipo_item)
        perm_del = PoseePermiso('eliminar rol', id_tipo_item=obj.id_tipo_item)
            
        if perm_mod.is_met(request.environ):
            value += '<div>' + \
                        '<a href="./' + str(obj.id_rol) + "/edit"+  \
                        '" class="' + clase + '">Modificar</a>' + \
                     '</div><br />'

        if perm_del.is_met(request.environ):
            value += '<div><form method="POST" action="./' + str(obj.id_rol) + '" class="button-to">'+\
                     '<input type="hidden" name="_method" value="DELETE" />' +\
                     '<input onclick="return confirm(\'Está seguro?\');" value="Eliminar" type="submit" '+\
                     'style="background-color: transparent; float:left; border:0; color: #286571;'+\
                     'display: inline; margin: 0; padding: 0; margin-left:-3px;" class="' + clase + '"/>'+\
                     '</form></div><br />'
        value += '</div>'
        return value
    
    def _do_get_provider_count_and_objs(self, id_tipo_item=None, **kw):
        """
        Se muestra la lista de roles para este tipo de ítem.
        """
        filtrados = []
        if AlgunPermiso(tipo="Tipo", 
                        id_tipo_item=id_tipo_item).is_met(request.environ):
            count, lista = super(RolesTipoTableFiller,
                         self)._do_get_provider_count_and_objs(**kw)
            
            for rol in lista:
                if rol.tipo.find("Tipo") >=0 and rol.id_tipo_item == id_tipo_item:
                    filtrados.append(rol)

        return len(filtrados), filtrados

roles_tipo_table_filler = RolesTipoTableFiller(DBSession)


class RolesTipoAddForm(AddRecordForm):
    __model__ = Rol
    __omit_fields__ = ['id_rol', 'usuarios', 'codigo', 'creado']
    __hide_fields__ = ['tipo', 'id_proyecto', 'id_tipo_item', 'id_fase']
    __require_fields__ = ['nombre_rol', 'permisos']
    __base_validator__ = RolFormValidator
    __field_order__ = ['nombre_rol', 'descripcion', 'permisos']
    __field_attrs__ = {'descripcion' : {'row': '1'},
                       'nombre_rol': { 'maxlength' : '32'}
                       }
    __widget_selector_type__ = SelectorPermisosPlantillaTi
    descripcion = TextArea

roles_tipo_add_form = RolesTipoAddForm(DBSession)


class RolesTipoEditForm(EditableForm):
    __model__ = Rol
    __hide_fields__ = ['id_rol', 'tipo', 'id_proyecto', 'id_fase', 
                       'id_tipo_item']
    __omit_fields__ = ['usuarios', 'codigo', 'creado']
    __require_fields__ = ['nombre_rol', 'permisos']
    __base_validator__ = RolFormValidator
    __field_order__ = ['nombre_rol', 'descripcion', 'permisos']
    __field_attrs__ = {'descripcion' : {'row': '1'},
                       'nombre_rol': { 'maxlength' : '32'}
                      }
    __widget_selector_type__ = SelectorPermisosPlantillaTi
    __field_order__ = ['id_rol', 'nombre_rol', 'descripcion', 'tipo', 'permisos']
    descripcion = TextArea

roles_tipo_edit_form = RolesTipoEditForm(DBSession)

roles_tipo_edit_form_filler = RolEditFiller(DBSession)


class RolesTipoController(CrudRestController):
    """Controlador de roles de tipo plantilla"""
    #{ Variables
    title = u"Roles del Tipo de Ítem"
    tmp_action = "./"
    rol_tipo = u"Tipo Ítem" 

    #{ Modificadores
    model = Rol
    table = roles_tipo_table
    table_filler = roles_tipo_table_filler
    new_form = roles_tipo_add_form
    edit_form = roles_tipo_edit_form
    edit_filler = roles_tipo_edit_form_filler

    #para el form de busqueda
    opciones = dict(codigo= u'Código',
                    nombre_rol= u'Nombre'
                    )
    columnas = dict(codigo='texto',
                    nombre_rol='texto'
                    )
    
    #{ Métodos
    @with_trailing_slash
    @paginate('lista_elementos', items_per_page=5)
    @expose('lpm.templates.rol.get_all')
    @expose('json')
    def get_all(self, *args, **kw):
        """ 
        Retorna todos los registros
        Retorna una página HTML si no se especifica JSON
        """
        id_tipo_item = UrlParser.parse_id(request.url, "tipositems")
        puede_crear = PoseePermiso("crear rol",
                                   id_tipo_item=id_tipo_item).is_met(request.environ)
        
        if request.response_type == 'application/json':
            return self.table_filler.get_value(id_tipo_item=id_tipo_item, **kw)
        if not getattr(self.table.__class__, '__retrieves_own_value__', False):
            roles = self.table_filler.get_value(id_tipo_item=id_tipo_item, **kw)
        else:
            roles = []
        tmpl_context.widget = self.table
        atras = "../"
        url_action = self.tmp_action
        return dict(lista_elementos=roles, 
                    page=self.title, 
                    titulo=self.title, 
                    modelo=self.model.__name__, 
                    columnas=self.columnas,
                    opciones=self.opciones,
                    url_action=url_action,
                    puede_crear=puede_crear,
                    atras=atras
                    )
        
    @with_trailing_slash
    @paginate('lista_elementos', items_per_page=5)
    @expose('lpm.templates.rol.get_all')
    @expose('json')
    def post_buscar(self, *args, **kw):
        id_tipo_item = UrlParser.parse_id(request.url, "tipositems")
        puede_crear = PoseePermiso("crear rol",
                                   id_tipo_item=id_tipo_item).is_met(request.environ)
        tmpl_context.widget = self.table
        buscar_table_filler = self.table_filler.__class__(DBSession)
        buscar_table_filler.filtros = kw
        roles = buscar_table_filler.get_value(id_tipo_item=id_tipo_item)
        atras = "../"
        return dict(lista_elementos=roles, 
                    page=self.title, 
                    titulo=self.title, 
                    modelo=self.model.__name__, 
                    columnas=self.columnas,
                    opciones=self.opciones,
                    url_action="../",
                    puede_crear=puede_crear,
                    atras=atras)
        
    @with_trailing_slash
    @expose('lpm.templates.rol.edit')
    def edit(self, id_rol, *args, **kw):
        """Despliega una pagina para modificar rol"""
        id_tipo_item = UrlParser.parse_id(request.url, "tipositems")
        url_action = "../../"
        tmpl_context.widget = self.edit_form
        value = self.edit_filler.get_value(values={'id_rol': int(id_rol)})
        page=u"Editar Rol de Tipo Ítem"
        return dict(value=value, 
                    page=page, 
                    atras=url_action)
    
    @without_trailing_slash
    @expose('lpm.templates.rol.new')
    def new(self, *args, **kw):
        kw['tipo'] = u'Tipo de Ítem'
        id_tipo_item = UrlParser.parse_id(request.url, "tipositems")
        url_action = "./"
        tmpl_context.widget = self.new_form
        return dict(value=kw, 
                    page=u"Nuevo Rol de Tipo Ítem", 
                    action=url_action, 
                    atras=url_action)

    #@validate(roles_proyecto_add_form, error_handler=new)
    @expose()
    def post(self, *args, **kw):
        """ Crea un nuevo rol plantilla o con contexto"""
        id_tipo_item = UrlParser.parse_id(request.url, "tipositems")
        url_action = "./"
        pp = PoseePermiso('crear rol', id_tipo_item=id_tipo_item)
        

        id_proyecto = UrlParser.parse_id(request.url, "proyectos")
        id_fase = UrlParser.parse_id(request.url, "fases")
        if not id_proyecto:
            id_proyecto = UrlParser.parse_id(request.url, "proyectos_fase")
            if not id_proyecto:
                id_proyecto = UrlParser.parse_id(request.url, "proyectos_fase_ti")
                id_fase = UrlParser.parse_id(request.url, "fases_ti")
        
        kw["id_proyecto"] = id_proyecto
        kw["id_fase"] = id_fase
        kw["id_tipo_item"] = id_tipo_item
        if not pp.is_met(request.environ):
            flash(pp.message % pp.nombre_permiso, 'warning')
            redirect(url_action)

        #url que redirige al new y rellena los parametros que ya ingreso
        error_url = url_action + "new"
       
        #agregamos los parametros que ya ingreso el usuario.
        nombre = kw.get("nombre_rol", None).encode("utf-8")
        nombre_q = urllib.quote(nombre)
        desc = kw.get("descripcion", None).encode("utf-8")
        desc_q = urllib.quote(desc)
        params = "?nombre_rol=" + nombre_q + "&descripcion=" + desc_q
        error_url += params
        
        if not (kw.has_key("permisos") and kw["permisos"]):
            flash("Debe seleccionar al menos un permiso", 'warning')
            redirect(error_url)
        else:    
            Rol.crear_rol(**kw)
            flash(u"El Rol se ha creado correctamente")
            redirect(url_action)
        

   #@validate(rol_plantilla_edit_form, error_handler=edit)
    @expose()
    def put(self, *args, **kw):
        """actualiza un rol"""
        id_tipo_item = UrlParser.parse_id(request.url, "tipositems")
        url_action = "../../"
        msg = u"El Rol se ha actualizado con éxito"
        pp = PoseePermiso('modificar rol', id_tipo_item=id_tipo_item)

        if not pp.is_met(request.environ):
            flash(pp.message % pp.nombre_permiso, 'warning')
            redirect(url_action)

        if not (kw.has_key("permisos") and kw["permisos"]):
            flash("Debe seleccionar al menos un permiso", 'warning')
            redirect(url_action + kw["id_rol"] + "/edit")

        Rol.actualizar_rol(**kw)
        flash(msg)
        redirect(url_action)
        
    @expose()
    def post_delete(self, *args, **kw):
        rol = Rol.por_id(int(args[0]))
        if rol.nombre_rol == u"Miembro de Tipo Item":
            flash(u'Rol Miembro de Tipo Item no puede ser eliminado', 'warning')
        flash("El rol se ha eliminado")
        super(RolesTipoController, self).post_delete(*args, **kw)







