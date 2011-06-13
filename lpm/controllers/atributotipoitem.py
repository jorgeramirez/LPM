# -*- coding: utf-8 -*-
"""
Módulo que define el controlador de atributos de 
tipos de ítem.

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

from lpm.model import (DBSession, TipoItem, AtributosPorTipoItem)
from lpm.lib.sproxcustom import CustomTableFiller
from lpm.lib.sproxcustom import WidgetSelectorDojo, MultipleSelectDojo
from lpm.lib.authorization import PoseePermiso, AlgunPermiso
from lpm.lib.util import UrlParser

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


class AtributosPorTipoItemTable(TableBase):
    __model__ = AtributosPorTipoItem
    __headers__ = {'nombre' : u'Nombre',
                   'tipo' : u"Tipo",
                   'valor_por_defecto': u"Valor por Defecto"
                  }
    __omit_fields__ = ['id_tipo_item', 'id_atributos_por_tipo_item']
    __default_column_width__ = '15em'
    __column_widths__ = {'nombre': "35em",
                         '__actions__' : "50em"
                        }
    
atributos_por_tipo_item_table = AtributosPorTipoItemTable(DBSession)


class AtributosPorTipoItemTableFiller(CustomTableFiller):
    __model__ = AtributosPorTipoItem
    __omit_fields__ = ['id_tipo_item', 'id_atributos_por_tipo_item']
   
    def __actions__(self, obj):
        """Links de acciones para un registro dado"""
        value = '<div>'
        clase = 'actions'
        url_cont = "/atributostipoitem/"
        id = str(obj.id_atributos_por_tipo_item)
        if PoseePermiso('redefinir tipo item').is_met(request.environ):
            value += '<div>' + \
                        '<a href="' + url_cont + id + '/edit" ' + \
                        'class="' + clase + '">Modificar</a>' + \
                     '</div><br />'
        if obj.puede_eliminarse():
            if PoseePermiso('eliminar tipo item').is_met(request.environ):
                value += '<div><form method="POST" action="' + url_cont + str(obj.id_tipo_item) + '" class="button-to">'+\
                         '<input type="hidden" name="_method" value="DELETE" />' +\
                         '<input onclick="return confirm(\'Está seguro?\');" value="Delete" type="submit" '+\
                         'style="background-color: transparent; float:left; border:0; color: #286571;'+\
                         'display: inline; margin: 0; padding: 0;" class="' + clase + '"/>'+\
                         '</form></div><br />'
        value += '</div>'
        return value
    
    def _do_get_provider_count_and_objs(self, **kw):
        """
        Se muestra la lista de rol si se tiene un permiso 
        necesario. Caso contrario le muestra sus roles.
        """
        if AlgunPermiso(patron="tipo item").is_met(request.environ):
            return super(AtributosPorTipoItemTableFiller,
                         self)._do_get_provider_count_and_objs(**kw)
        query = DBSession.query(AtributosPorTipoItem)
        return query.count(), query.all()

atributos_por_tipo_item_table_filler = AtributosPorTipoItemTableFiller(DBSession)


class AtributoTipoField(PropertySingleSelectField):
    """Dropdown list para el tipo del atributo"""
    def _my_update_params(self, d, nullable=False):
        options = []
        options.append((0, "----------"))
        options.extend(AtributosPorTipoItem._tipos_permitidos)
        d['options'] = options
        return d


class AtributosPorTipoItemAddForm(AddRecordForm):
    __model__ = AtributosPorTipoItem
    __omit_fields__ = ['id_tipo_item', 'id_atributos_por_tipo_item']
    __require_fields__ = ['nombre', 'tipo', 'valor_por_defecto']
    __check_if_unique__ = True
    __field_order__ = ['nombre', 'tipo', 'valor_por_defecto']
    __field_attrs__ = {'nombre': { 'maxlength' : '32'},
                       'tipo': { 'maxlength' : '32'},
                       'valor_por_defecto': { 'maxlength' : '32'}
                      }
    
atributos_por_tipo_item_add_form = AtributosPorTipoItemAddForm(DBSession)


class AtributosPorTipoItemEditForm(EditableForm):
    __model__ = AtributosPorTipoItem
    __omit_fields__ = ['id_tipo_item', 'id_atributos_por_tipo_item']
    __require_fields__ = ['nombre', 'tipo', 'valor_por_defecto']
    __check_if_unique__ = True
    __field_order__ = ['nombre', 'tipo', 'valor_por_defecto']
    __field_attrs__ = {'nombre': { 'maxlength' : '32'},
                       'tipo': { 'maxlength' : '32'},
                       'valor_por_defecto': { 'maxlength' : '32'}
                      }

atributos_por_tipo_item_edit_form = AtributosPorTipoItemEditForm(DBSession)


class AtributosPorTipoItemEditFiller(EditFormFiller):
    __model__ = AtributosPorTipoItem

atributos_por_tipo_item_edit_filler = AtributosPorTipoItemEditFiller(DBSession)


class AtributosPorTipoItemController(CrudRestController):
    """Controlador de roles"""
    #{ Variables
    title = u"Administrar Atributos de Tipo de Item"
    action = "/tipositems/" #parent controller
    #{ Plantillas

    # No permitir rols anonimos (?)
    allow_only = not_anonymous(u"El usuario debe haber iniciado sesión")
    
    #{ Modificadores
    model = AtributosPorTipoItem
    table = atributos_por_tipo_item_table
    table_filler = atributos_por_tipo_item_table_filler
    new_form = atributos_por_tipo_item_add_form
    edit_form = atributos_por_tipo_item_edit_form
    edit_filler = atributos_por_tipo_item_edit_filler

    #{ Métodos
    @expose('lpm.templates.atributotipoitem.edit')
    def edit(self, *args, **kw):
        """Despliega una pagina para modificar tipo_item"""
        pp = PoseePermiso('redefinir tipo item')
        if not pp.is_met(request.environ):
            flash(pp.message % pp.nombre_permiso, 'warning')
            redirect(self.action)
        tmpl_context.widget = self.edit_form
        value = self.edit_filler.get_value(values={'id_tipo_item': int(args[0])})
        value['_method'] = 'PUT'
        page = "Atributo {nombre}".format(nombre=value["nombre"])
        return dict(value=value, page=page, 
                    atras=self.action)

    @without_trailing_slash
    @expose('lpm.templates.atributotipoitem.new')
    def new(self, *args, **kw):
        """Despliega una pagina para crear un tipo_item"""
        pp = PoseePermiso('redefinir tipo item')
        if not pp.is_met(request.environ):
            flash(pp.message % pp.nombre_permiso, 'warning')
            redirect(self.action)
        tmpl_context.widget = self.new_form
        id_tipo = UrlParser.parse_id(request.url, "tipositems")
        atras = self.action + str(id_tipo) + '/edit'
        return dict(value=kw, page=u"Nuevo Atributo", 
                    action=self.action, atras=atras)
    
    @validate(atributos_por_tipo_item_add_form, error_handler=new)
    @expose()
    def post(self, *args, **kw):
        """create a new record"""
        pp = PoseePermiso('redefinir tipo item')
        if not pp.is_met(request.environ):
            flash(pp.message % pp.nombre_permiso, 'warning')
            redirect(self.action)
        if kw.has_key("sprox_id"):
            del kw["sprox_id"]
        transaction.begin()
        id_tipo = UrlParser.parse_id(request.url, "tipositems")
        tipo = TipoItem.por_id(id_tipo)
        tipo.agregar_atributo(**kw)
        transaction.commit()
        redirect(self.action + id_tipo + '/edit')
        
    @validate(atributos_por_tipo_item_edit_form, error_handler=edit)
    @expose()
    def put(self, *args, **kw):
        """update a record"""
        pp = PoseePermiso('redefinir tipo item')
        if not pp.is_met(request.environ):
            flash(pp.message % pp.nombre_permiso, 'warning')
            redirect(self.action)
        if kw.has_key("sprox_id"):
            del kw["sprox_id"]
        id_atributo = int(args[0])
        id_tipo = UrlParser.parse_id(request.url, "tipositems")
        transaction.begin()
        tipo = TipoItem.por_id(id_tipo)
        tipo.modificar_atributo(id_atributo, **kw)
        transaction.commit()
        redirect(self.action + id_tipo + '/edit')

    #}
