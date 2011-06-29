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
from lpm.model.excepciones import *
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
        id = str(obj.id_atributos_por_tipo_item)
        id_tipo = UrlParser.parse_id(request.url, "tipositems")
        
       
        if PoseePermiso('redefinir tipo item',
                        id_tipo_item=obj.id_tipo_item).is_met(request.environ):
            value += '<div>' + \
                        '<a href="./' + id + '/edit" ' + \
                        'class="' + clase + '">Modificar</a>' + \
                     '</div><br />'

        if obj.puede_eliminarse():
            if PoseePermiso('redefinir tipo item',
                            id_tipo_item=obj.id_tipo_item).is_met(request.environ):
                value += '<div><form method="POST" action="' + id + '" class="button-to">'+\
                         '<input type="hidden" name="_method" value="DELETE" />' +\
                         '<input onclick="return confirm(\'Está seguro?\');" value="Eliminar" type="submit" '+\
                         'style="background-color: transparent; float:left; border:0; color: #286571;'+\
                         'display: inline; margin: 0; padding: 0; margin-left:-3px;" class="' + clase + '"/>'+\
                         '</form></div><br />'
        value += '</div>'
        return value
    
    def _do_get_provider_count_and_objs(self, id_tipo_item=None,**kw):
        """
        Se muestra la lista de atributos del tipo de ítem 
        si se tiene un permiso necesario.
        """
        if AlgunPermiso(tipo="Tipo", id_tipo_item=id_tipo_item).is_met(request.environ):
            id_tipo = UrlParser.parse_id(request.url, "tipositems")
            ti = TipoItem.por_id(id_tipo)
            pks = []
            actual = ti
            while actual:
                for attr in actual.atributos:
                    pks.append(attr.id_atributos_por_tipo_item)
                actual = TipoItem.por_id(actual.id_padre)
            query = DBSession.query(AtributosPorTipoItem) \
                             .filter(AtributosPorTipoItem \
                                     .id_atributos_por_tipo_item.in_(pks))
            return query.count(), query.all()

        return 0, []

atributos_por_tipo_item_table_filler = AtributosPorTipoItemTableFiller(DBSession)


class AtributoTipoField(PropertySingleSelectField):
    """Dropdown list para el tipo del atributo"""
    def _my_update_params(self, d, nullable=False):
        options = []
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
    tipo = AtributoTipoField("tipo", labeltext="Tipo")
    
atributos_por_tipo_item_add_form = AtributosPorTipoItemAddForm(DBSession)


class AtributosPorTipoItemEditForm(EditableForm):
    __model__ = AtributosPorTipoItem
    __hide_fields__ = ['id_atributos_por_tipo_item']
    __omit_fields__ = ['id_tipo_item', 'id_atributos_por_tipo_item']
    __require_fields__ = ['nombre', 'tipo', 'valor_por_defecto'] 
    __check_if_unique__ = True
    __field_order__ = ['nombre', 'tipo', 'valor_por_defecto']
    __field_attrs__ = {'nombre': { 'maxlength' : '32'},
                       'tipo': { 'maxlength' : '32'},
                       'valor_por_defecto': { 'maxlength' : '32'}
                      }
    tipo = AtributoTipoField("tipo", label_text=u"Tipo")
    nombre = TextField("nombre", label_text=u"Nombre")

atributos_por_tipo_item_edit_form = AtributosPorTipoItemEditForm(DBSession)


class AtributosPorTipoItemEditFiller(EditFormFiller):
    __model__ = AtributosPorTipoItem
    __omit_fields__ = ['id_tipo_item', 'id_atributos_por_tipo_item']
    
atributos_por_tipo_item_edit_filler = AtributosPorTipoItemEditFiller(DBSession)


class AtributosPorTipoItemController(CrudRestController):
    """Controlador de roles"""
    #{ Variables
    title = u"Atributos de: %s"
    action = "./"
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

    opciones = dict(nombre= u'Nombre',
                    tipo=u"Tipo")
                    
    columnas = dict(nombre= u'texto',
                    tipo=u"combobox")
                    
    comboboxes = dict(tipo=AtributosPorTipoItem._tipos_permitidos)

    #{ Métodos
    @with_trailing_slash
    @paginate('lista_elementos', items_per_page=5)
    @expose('lpm.templates.tipoitem.get_all')
    @expose('json')
    def get_all(self, *args, **kw):
        """ 
        Retorna todos los registros
        Retorna una página HTML si no se especifica JSON
        """
        
        id_tipo_item = UrlParser.parse_id(request.url, "tipositems")
        puede_crear = PoseePermiso('redefinir tipo item',
                                   id_tipo_item=id_tipo_item).is_met(request.environ)
        tipo = TipoItem.por_id(id_tipo_item)
        titulo = self.title % tipo.nombre
        atributos = self.table_filler.get_value(id_tipo_item=id_tipo_item, **kw)
        tmpl_context.widget = self.table
        url_action = self.action
        atras = "../"
        
        return dict(lista_elementos=atributos,
                    page=titulo, 
                    titulo=titulo, 
                    modelo=self.model.__name__, 
                    columnas=self.columnas,
                    opciones=self.opciones,
                    comboboxes=self.comboboxes,
                    url_action=url_action,
                    puede_crear=puede_crear,
                    atras=atras
                    )



    @without_trailing_slash
    @expose('lpm.templates.atributotipoitem.edit')
    def edit(self, *args, **kw):
        """Despliega una pagina para modificar el atributo"""
        id_tipo_item = UrlParser.parse_id(request.url, "tipositems")
        url_action = "../"
       
        pp = PoseePermiso('redefinir tipo item',
                          id_tipo_item=id_tipo_item)
        if not pp.is_met(request.environ):
            flash(pp.message % pp.nombre_permiso, 'warning')
            redirect(url_action)
        tmpl_context.widget = self.edit_form
        value = self.edit_filler.get_value( \
                     values={'id_atributos_por_tipo_item': int(args[0])})
        value['_method'] = 'PUT'
        page = "Atributo {nombre}".format(nombre=value["nombre"])
        return dict(value=value, 
                    page=page, 
                    atras=url_action)

    @without_trailing_slash
    @expose('lpm.templates.atributotipoitem.new')
    def new(self, *args, **kw):
        """Despliega una pagina para crear un tipo_item"""
        id_tipo_item = UrlParser.parse_id(request.url, "tipositems")
        url_action = "./"

        pp = PoseePermiso('redefinir tipo item', id_tipo_item=id_tipo_item)
        if not pp.is_met(request.environ):
            flash(pp.message % pp.nombre_permiso, 'warning')
            redirect(atras)
        tmpl_context.widget = self.new_form
        return dict(value=kw, 
                    page=u"Nuevo Atributo", 
                    action=url_action, 
                    atras=url_action)
    
    @validate(atributos_por_tipo_item_add_form, error_handler=new)
    @expose()
    def post(self, *args, **kw):
        """create a new record"""
        id_tipo_item = UrlParser.parse_id(request.url, "tipositems")
        url_action = "./"

        pp = PoseePermiso('redefinir tipo item',id_tipo_item=id_tipo_item)
                          
        if not pp.is_met(request.environ):
            flash(pp.message % pp.nombre_permiso, 'warning')
            redirect(url_action)
            
        if kw.has_key("sprox_id"):
            del kw["sprox_id"]

        tipo = TipoItem.por_id(id_tipo_item)
        try:
            tipo.agregar_atributo(**kw)
        except NombreDeAtributoError, err:
            flash(unicode(err), "warning")

        redirect(url_action)
        
    @validate(atributos_por_tipo_item_edit_form, error_handler=edit)
    @expose()
    def put(self, *args, **kw):
        """update a record"""
        id_tipo_item = UrlParser.parse_id(request.url, "tipositems")
        id_atributo = UrlParser.parse_id(request.url, "atributostipoitem")
        url_action = "../"

        pp = PoseePermiso('redefinir tipo item',id_tipo_item=id_tipo_item)
                          
        if not pp.is_met(request.environ):
            flash(pp.message % pp.nombre_permiso, 'warning')
            redirect(url_action)
            
        if kw.has_key("sprox_id"):
            del kw["sprox_id"]
        transaction.begin()
        tipo = TipoItem.por_id(id_tipo_item)
        try:
            tipo.modificar_atributo(id_atributo, **kw)
        except NombreDeAtributoError, err:
            flash(unicode(err), "warning")
        transaction.commit()
        redirect(url_action)

    @expose()
    def post_delete(self, *args, **kw):
        """This is the code that actually deletes the record"""
        id_atributo = int(args[0])
        transaction.begin()
        attr = AtributosPorTipoItem.por_id(id_atributo)
        DBSession.delete(attr)
        transaction.commit()
        flash("Atributo Eliminado")
        redirect("./")

    @with_trailing_slash
    @paginate('lista_elementos', items_per_page=5)
    @expose('lpm.templates.tipoitem.get_all')
    @expose('json')
    def post_buscar(self, *args, **kw):
        """ 
        Retorna todos los registros
        Retorna una página HTML si no se especifica JSON
        """
        
        id_tipo_item = UrlParser.parse_id(request.url, "tipositems")
        puede_crear = PoseePermiso('redefinir tipo item',
                                   id_tipo_item=id_tipo_item).is_met(request.environ)
        tipo = TipoItem.por_id(id_tipo_item)
        titulo = self.title % tipo.nombre
        filler = AtributosPorTipoItemTableFiller(DBSession)
        filler.filtros = kw
        atributos = filler.get_value(id_tipo_item=id_tipo_item, **kw)
        tmpl_context.widget = self.table
        url_action = self.action
        atras = "../"
        
        return dict(lista_elementos=atributos,
                    page=titulo, 
                    titulo=titulo, 
                    modelo=self.model.__name__, 
                    columnas=self.columnas,
                    opciones=self.opciones,
                    comboboxes=self.comboboxes,
                    url_action="../",
                    puede_crear=puede_crear,
                    atras=atras
                    )


    #}
