# -*- coding: utf-8 -*-
"""
Módulo que define el conttipo_itemador de tipos de ítem.

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

from lpm.model import (DBSession, Usuario, TipoItem, Permiso, Proyecto, 
                       Fase, TipoItem)
from lpm.lib.sproxcustom import CustomTableFiller
from lpm.lib.sproxcustom import WidgetSelectorDojo, MultipleSelectDojo
from lpm.lib.authorization import PoseePermiso, AlgunPermiso

from sprox.tablebase import TableBase
from sprox.fillerbase import TableFiller
from sprox.fillerbase import EditFormFiller
from sprox.dojo.formbase import DojoAddRecordForm as AddRecordForm
from sprox.dojo.formbase import DojoEditableForm as EditableForm
from sprox.widgets import PropertySingleSelectField

from tw.forms.fields import (PasswordField, TextField, TextArea, Button, 
                             CheckBox)

from repoze.what.predicates import not_anonymous

from tg import tmpl_context, request

import transaction


class TipoItemTable(TableBase):
    __model__ = TipoItem
    __headers__ = {'codigo' : u'Código',
                   'proyecto' : u"Proyecto"
                  }
    __omit_fields__ = ['id_tipo_item', 'id_proyecto', 'id_padre',
                       'hijos', 'atributos', 'items', 'descripcion']
    __default_column_width__ = '15em'
    __column_widths__ = {'codigo': "35em",
                         '__actions__' : "50em"
                        }
    
tipo_item_table = TipoItemTable(DBSession)


class TipoItemTableFiller(CustomTableFiller):
    __model__ = TipoItem
    __omit_fields__ = ['id_tipo_item', 'id_proyecto', 'id_padre',
                       'hijos', 'atributos', 'items']
   
    def __actions__(self, obj):
        """Links de acciones para un registro dado"""
        value = '<div>'
        clase = 'actions'
        url_cont = "/tipositems/"
        if PoseePermiso('redefinir tipo item').is_met(request.environ):
            value += '<div>' + \
                        '<a href="' + url_cont + str(obj.id_tipo_item) +'/edit" ' + \
                        'class="' + clase + '">Modificar</a>' + \
                     '</div><br />'
        if len(obj.items):
            if PoseePermiso('eliminar tipo item').is_met(request.environ):
                value += '<div><form method="POST" action="' + url_cont + str(obj.id_tipo_item) + '" class="button-to">'+\
                         '<input type="hidden" name="_method" value="DELETE" />' +\
                         '<input onclick="return confirm(\'Está seguro?\');" value="Delete" type="submit" '+\
                         'style="background-color: transparent; float:left; border:0; color: #286571;'+\
                         'display: inline; margin: 0; padding: 0;" class="' + clase + '"/>'+\
                         '</form></div><br />'
        if PoseePermiso('redefinir tipo item').is_met(request.environ):
            value += '<div>' + \
                        '<a href="' + url_cont + '/' + str(obj.id_tipo_item) \
                        + '/atributostipoitem/new" ' + \
                        'class="' + clase + '">Agregar Atributo</a>' + \
                     '</div><br />'
        value += '</div>'
        return value
    
    def _do_get_provider_count_and_objs(self, **kw):
        """
        Se muestra la lista de tipos de item si se tienen los permisos
        necesario.
        """
        if AlgunPermiso(patron="tipo item").is_met(request.environ):
            return super(TipoItemTableFiller,
                         self)._do_get_provider_count_and_objs(**kw)
        query = DBSession.query(TipoItem)
        return query.count(), query.all()


tipo_item_table_filler = TipoItemTableFiller(DBSession)


class TipoPadreField(PropertySingleSelectField):
    """Dropdown list para el tipo padre de un tipo de item"""
    def _my_update_params(self, d, nullable=False):
        options = []
        options.append((0, "----------"))
        tipos_items = DBSession.query(TipoItem).all()
        for ti in tipos_items:
            options.append((ti.id_tipo_item, '%s (%s)' % (ti.codigo, 
                                                          ti.nombre)))
        d['options'] = options
        return d

class TipoExportadoField(PropertySingleSelectField):
    """Dropdown list para la lista de tipos a exportar"""
    def _my_update_params(self, d, nullable=False):
        options = []
        options.append((0, "----------"))
        tipos_items = DBSession.query(TipoItem).all()
        for ti in tipos_items:
            options.append((ti.id_tipo_item, '%s (%s)' % (ti.codigo, 
                                                          ti.nombre)))
        d['options'] = options
        return d
  

class TipoItemAddForm(AddRecordForm):
    __model__ = TipoItem
    __omit_fields__ = ['id_tipo_item', 'id_proyecto', 'codigo',
                       'hijos', 'atributos', 'items']
    __check_if_unique__ = True
    __field_order__ = ['nombre', 'descripcion', 'id_padre', 'id_exportado',
                       'mezclar']
    __field_attrs__ = {'descripcion' : {'row': '1'},
                       'nombre': { 'maxlength' : '50'}
                       
                      }
    id_padre = TipoPadreField("id_padre", label_text="Tipo Padre")
    id_exportado = TipoPadreField("id_exportado", label_text="Exportar De")
    descripcion = TextArea
    mezclar = CheckBox("mezclar", label_text="Mezclar Estructuras")
    
tipo_item_add_form = TipoItemAddForm(DBSession)


class TipoItemEditForm(EditableForm):
    __model__ = TipoItem
    __omit_fields__ = ['id_tipo_item', 'id_proyecto', 'codigo', 'hijos', 
                       'atributos', 'items']
    __check_if_unique__ = True
    __field_order__ = ['nombre', 'descripcion', 'id_padre', 'id_exportado']
    __field_attrs__ = {'descripcion' : {'row': '1'},
                       'nombre': { 'maxlength' : '50'}
                       
                      }
    id_padre = TipoPadreField("id_padre", label_text="Tipo Padre")
    id_exportado = TipoPadreField("id_exportado", label_text="Exportar De")
    descripcion = TextArea

tipo_item_edit_form = TipoItemEditForm(DBSession)


class TipoItemEditFiller(EditFormFiller):
    __model__ = TipoItem

tipo_item_edit_filler = TipoItemEditFiller(DBSession)


class TipoItemController(CrudRestController):
    """Controlador para tipos de item"""
    #{ Variables
    title = u"Administrar Tipos de Ítem"
    action = "/tipositems/"
    #{ Plantillas

    # No permitir tipo_items anonimos (?)
    allow_only = not_anonymous(u"El usuario debe haber iniciado sesión")
    
    #{ Modificadores
    model = TipoItem
    table = tipo_item_table
    table_filler = tipo_item_table_filler
    new_form = tipo_item_add_form
    edit_form = tipo_item_edit_form
    edit_filler = tipo_item_edit_filler

    #para el form de busqueda
    columnas = dict(codigo="texto", nombre="texto")
    tipo_opciones = []
 
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
        puede_crear = PoseePermiso("crear tipo item").is_met(request.environ)
        if request.response_type == 'application/json':
            return self.table_filler.get_value(**kw)
        if not getattr(self.table.__class__, '__retrieves_own_value__', False):
            tipo_itemes = self.table_filler.get_value(**kw)
        else:
            tipo_itemes = []
        tmpl_context.widget = self.table
        return dict(lista_elementos=tipo_itemes, 
                    page=self.title, titulo=self.title, 
                    modelo=self.model.__name__, 
                    columnas=self.columnas,
                    tipo_opciones=self.tipo_opciones, 
                    url_action=self.action,
                    puede_crear=puede_crear)

    @expose('lpm.templates.tipoitem.edit')
    def edit(self, *args, **kw):
        """Despliega una pagina para modificar tipo_item"""
        pp = PoseePermiso('redefinir tipo item')
        if not pp.is_met(request.environ):
            flash(pp.message % pp.nombre_permiso, 'warning')
            redirect(self.action)
        tmpl_context.widget = self.edit_form
        value = self.edit_filler.get_value(values={'id_tipo_item': int(args[0])})
        value['_method'] = 'PUT'
        page = "Tipo Item {nombre}".format(nombre=value["nombre"])
        return dict(value=value, page=page, atras=self.action)

    @without_trailing_slash
    @expose('lpm.templates.tipoitem.new')
    def new(self, *args, **kw):
        """Despliega una pagina para crear un tipo_item"""
        pp = PoseePermiso('crear tipo item')
        if not pp.is_met(request.environ):
            flash(pp.message % pp.nombre_permiso, 'warning')
            redirect(self.action)
        tmpl_context.widget = self.new_form
        return dict(value=kw, page=u"Nuevo Tipo de Ítem", 
                    action=self.action, atras=self.action)
    
    @validate(tipo_item_add_form, error_handler=new)
    @expose()
    def post(self, *args, **kw):
        """create a new record"""
        pp = PoseePermiso('crear tipo item')
        if not pp.is_met(request.environ):
            flash(pp.message % pp.nombre_permiso, 'warning')
            redirect(self.action)
        transaction.begin()
        #TODO
        transaction.commit()
        redirect(self.action)
        
    @validate(tipo_item_edit_form, error_handler=edit)
    @expose()
    def put(self, *args, **kw):
        """update a record"""
        pp = PoseePermiso('modificar tipo_item')
        if not pp.is_met(request.environ):
            flash(pp.message % pp.nombre_permiso, 'warning')
            redirect(self.action)
        transaction.begin()
        #TODO
        transaction.commit()
        redirect(self.action)

    @with_trailing_slash
    @paginate('lista_elementos', items_per_page=5)
    @expose('lpm.templates.tipoitem.get_all')
    @expose('json')
    def post_buscar(self, *args, **kw):
        puede_crear = PoseePermiso("crear tipo_item").is_met(request.environ)
        tmpl_context.widget = self.table
        buscar_table_filler = self.table_filler.__class__(DBSession)
        buscar_table_filler.filtros = kw
        tipos_items = buscar_table_filler.get_value()
        return  dict(lista_elementos=tipos_items, 
                     page=self.title, titulo=self.title,
                     modelo=self.model.__name__, 
                     columnas=self.columnas,
                     tipo_opciones=self.tipo_opciones, 
                     url_action=self.action,
                     puede_crear=puede_crear)
    #}
