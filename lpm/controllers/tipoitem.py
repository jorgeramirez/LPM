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
from lpm.lib.util import UrlParser
from lpm.controllers.atributotipoitem import (AtributosPorTipoItemController)

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
        id = str(obj.id_tipo_item)
        id_proyecto = UrlParser.parse_id(request.url, "proyectos")
        if id_proyecto:
            url_cont = "/proyectos/%d/tipositems/" % id_proyecto
        if PoseePermiso('redefinir tipo item').is_met(request.environ):
            value += '<div>' + \
                        '<a href="' + url_cont + id +'/edit" ' + \
                        'class="' + clase + '">Modificar</a>' + \
                     '</div><br />'
        if obj.puede_eliminarse():
            if PoseePermiso('redefinir tipo item').is_met(request.environ):
                #value += '<div><form method="POST" action="' + id + '" class="button-to">'+\
                #         '<input type="hidden" name="_method" value="DELETE" />' +\
                #         '<input onclick="return confirm(\'Está seguro?\');" value="Delete" type="submit" '+\
                #         'style="background-color: transparent; float:left; border:0; color: #286571;'+\
                #         'display: inline; margin: 0; padding: 0;" class="' + clase + '"/>'+\
                #         '</form></div><br />'
                value += '<div><form method="POST" action="' + id + '" class="button-to">'+\
                         '<input type="hidden" name="_method" value="DELETE" />' +\
                         '<input onclick="return confirm(\'Está seguro?\');" value="Eliminar" type="submit" '+\
                         'style="background-color: transparent; float:left; border:0; color: #286571;'+\
                         'display: inline; margin: 0; padding: 0;" class="' + clase + '"/>'+\
                         '</form></div><br />'
        if PoseePermiso('redefinir tipo item').is_met(request.environ):
            value += '<div>' + \
                        '<a href="' + url_cont + id + '/atributostipoitem/new" ' + \
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
        id_proyecto = UrlParser.parse_id(request.url, "proyectos")
        if id_proyecto:
            proy = Proyecto.por_id(id_proyecto)
            return len(proy.tipos_de_item), proy.tipos_de_item
        query = DBSession.query(TipoItem)
        return query.count(), query.all()


tipo_item_table_filler = TipoItemTableFiller(DBSession)


class TipoPadreField(PropertySingleSelectField):
    """Dropdown list para el tipo padre de un tipo de item"""
    def _my_update_params(self, d, nullable=False):
        options = []
        options.append((0, "----------"))
        #Solo tipos del proyecto
        id_proyecto = UrlParser.parse_id(request.url, "proyectos")
        if id_proyecto:
            proy = Proyecto.por_id(id_proyecto)
            for ti in proy.tipos_de_item:
                options.append((ti.id_tipo_item, '%s (%s)' % (ti.nombre, 
                                                              ti.codigo)))
        d['options'] = options
        return d

class TipoImportadoField(PropertySingleSelectField):
    """Dropdown list para la lista de tipos a exportar"""
    def _my_update_params(self, d, nullable=False):
        options = []
        options.append((0, "----------"))
        #Solo tipos de otros proyectos
        id_proyecto = UrlParser.parse_id(request.url, "proyectos")
        if id_proyecto:
            tipos_items = DBSession.query(TipoItem) \
                                   .filter(TipoItem.id_proyecto != id_proyecto) \
                                   .all()
            for ti in tipos_items:
                options.append((ti.id_tipo_item, '%s (%s)' % (ti.nombre, 
                                                              ti.codigo)))
        d['options'] = options
        return d
  

class TipoItemAddForm(AddRecordForm):
    __model__ = TipoItem
    __omit_fields__ = ['id_tipo_item', 'id_proyecto', 'codigo',
                       'hijos', 'atributos', 'items']
    __check_if_unique__ = True
    __field_order__ = ['nombre', 'descripcion', 'id_padre', 'id_importado',
                       'mezclar']
    __field_attrs__ = {'descripcion' : {'row': '1'},
                       'nombre': { 'maxlength' : '50'}
                       
                      }
    __require_fields__ = ['nombre', 'id_padre']
    id_padre = TipoPadreField("id_padre", label_text="Tipo Padre")
    id_importado = TipoImportadoField("id_importado", label_text="Importar De")
    descripcion = TextArea
    mezclar = CheckBox("mezclar", label_text="Mezclar Estructuras")
    
tipo_item_add_form = TipoItemAddForm(DBSession)


class TipoItemEditForm(EditableForm):
    __model__ = TipoItem
    __hide_fields__ = ['id_tipo_item']
    __omit_fields__ = ['id_tipo_item', 'id_proyecto', 'codigo', 'hijos', 
                       'atributos', 'items', 'id_padre']
    #__check_if_unique__ = True
    __field_order__ = ['nombre', 'descripcion']
    __field_attrs__ = {'descripcion' : {'row': '1'},
                       'nombre': { 'maxlength' : '50'}
                       
                      }
    __require_fields__ = ['nombre']
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
    subaction = "/atributostipoitem/"
    #subcontroller
    atributostipoitem = AtributosPorTipoItemController(DBSession)
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
    #columnas = dict(codigo="texto", nombre="texto")
    #tipo_opciones = []
    opciones = dict(codigo= u'Código',
                    nombre= u'Nombre'
                    )
    columnas = dict(codigo='texto',
                    nombre='texto'
                    )
    #comboboxes = dict()
 
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
        puede_crear = False
        if request.response_type == 'application/json':
            return self.table_filler.get_value(**kw)
        if not getattr(self.table.__class__, '__retrieves_own_value__', False):
            tipo_items = self.table_filler.get_value(**kw)
        else:
            tipo_items = []
        tmpl_context.widget = self.table
        url_action = self.action
        atras = '/'
        id_proyecto = UrlParser.parse_id(request.url, "proyectos")
        if id_proyecto:
            url_action = '/proyectos/%d/tipositems/' % id_proyecto
            atras = url_action
            puede_crear = PoseePermiso("crear tipo item").is_met(request.environ)
        return dict(lista_elementos=tipo_items,
                    page=self.title, titulo=self.title, 
                    modelo=self.model.__name__, 
                    columnas=self.columnas,
                    opciones=self.opciones, 
                    url_action=url_action,
                    puede_crear=puede_crear,
                    atras=atras)

    @expose('lpm.templates.tipoitem.edit')
    def edit(self, *args, **kw):
        """Despliega una pagina para modificar tipo_item"""
        url_action = self.action
        url_subaction = self.subaction
        id_proyecto = UrlParser.parse_id(request.url, "proyectos")
        id_tipo = UrlParser.parse_id(request.url, "tipositems")
        if id_proyecto:
            url_action = '/proyectos/%d/tipositems/' % id_proyecto
            url_subaction = url_action + 'atributostipoitem/'
        pp = PoseePermiso('redefinir tipo item')
        if not pp.is_met(request.environ):
            flash(pp.message % pp.nombre_permiso, 'warning')
            redirect(url_action)
        tmpl_context.widget = self.edit_form
        tmpl_context.atributos_table = self.atributostipoitem.table
        value = self.edit_filler.get_value(values={'id_tipo_item': id_tipo})
        atributos = self.atributostipoitem.table_filler.get_value(
                                      values={'id_tipo_item': id_tipo})
        value['_method'] = 'PUT'
        page = "Tipo Item {nombre}".format(nombre=value["nombre"])
        return dict(value=value, 
                    atributos=atributos, 
                    page=page, 
                    atras=url_action, 
                    url_action=url_action,
                    id=str(id_tipo), 
                    url_subaction=self.subaction)

    @without_trailing_slash
    @expose('lpm.templates.tipoitem.new')
    def new(self, *args, **kw):
        """Despliega una pagina para crear un tipo_item"""
        url_action = self.action
        id_proyecto = UrlParser.parse_id(request.url, "proyectos")
        if id_proyecto:
            url_action = '/proyectos/%d/tipositems/' % id_proyecto
        pp = PoseePermiso('crear tipo item')
        if not pp.is_met(request.environ):
            flash(pp.message % pp.nombre_permiso, 'warning')
            redirect(url_action)
        tmpl_context.widget = self.new_form
        return dict(value=kw, page=u"Nuevo Tipo de Ítem", 
                    action=url_action, atras=url_action)
    
    @validate(tipo_item_add_form, error_handler=new)
    @expose()
    def post(self, *args, **kw):
        """create a new record"""
        print kw
        id_proyecto = UrlParser.parse_id(request.url, "proyectos")
        if not id_proyecto:
            return
        url_action = '/proyectos/%d/tipositems/' % id_proyecto
        pp = PoseePermiso('crear tipo item')
        if not pp.is_met(request.environ):
            flash(pp.message % pp.nombre_permiso, 'warning')
            redirect(url_action)
        if kw.has_key("sprox_id"):
            del kw["sprox_id"]
        id_padre = int(kw["id_padre"])
        id_importado = int(kw["id_importado"])
        mezclar = kw["mezclar"]
        del kw["mezclar"]
        del kw["id_padre"]
        del kw["id_importado"]
        transaction.begin()
        proy = Proyecto.por_id(id_proyecto)
        proy.definir_tipo_item(id_padre, id_importado, mezclar, **kw)
        transaction.commit()
        redirect(url_action)
        
    @validate(tipo_item_edit_form, error_handler=edit)
    @expose()
    def put(self, *args, **kw):
        """update a record"""
        url_action = self.action
        id_proyecto = UrlParser.parse_id(request.url, "proyectos")
        if id_proyecto:
            url_action = '/proyectos/%d/tipositems/' % id_proyecto
        pp = PoseePermiso('redefinir tipo item')
        if not pp.is_met(request.environ):
            flash(pp.message % pp.nombre_permiso, 'warning')
            redirect(url_action)
        id_tipo = UrlParser.parse_id(request.url, "tipositems")
        transaction.begin()
        tipo = TipoItem.por_id(id_tipo)
        if kw["nombre"] != tipo.nombre:
            if TipoItem.por_nombre(kw["nombre"]):
                return
        tipo.nombre = unicode(kw["nombre"])
        tipo.descripcion = unicode(kw["descripcion"])
        transaction.commit()
        redirect(url_action)

    @with_trailing_slash
    @paginate('lista_elementos', items_per_page=5)
    @expose('lpm.templates.tipoitem.get_all')
    @expose('json')
    def post_buscar(self, *args, **kw):
        url_action = self.action
        atras = '/'
        id_proyecto = UrlParser.parse_id(request.url, "proyectos")
        puede_crear = False
        if id_proyecto:
            url_action = '/proyectos/%d/tipositems/' % id_proyecto
            atras = url_action
            puede_crear = PoseePermiso("crear tipo item").is_met(request.environ)
        tmpl_context.widget = self.table
        buscar_table_filler = self.table_filler.__class__(DBSession)
        buscar_table_filler.filtros = kw
        tipos_items = buscar_table_filler.get_value()
        return  dict(lista_elementos=tipos_items, 
                     page=self.title, titulo=self.title,
                     modelo=self.model.__name__, 
                     columnas=self.columnas,
                     opciones=self.opciones, 
                     url_action=url_action,
                     puede_crear=puede_crear,
                     atras=atras)

    @expose()
    def post_delete(self, *args, **kw):
        """This is the code that actually deletes the record"""
        atras = '/'
        id_proyecto = UrlParser.parse_id(request.url, "proyectos")
        id_tipo = int(args[0])
        transaction.begin()
        if id_proyecto:
            atras = '/proyectos/%d/tipositems/' % id_proyecto
            proy = Proyecto.por_id(id_proyecto)
            proy.eliminar_tipo_item(id_tipo)
        else:
            tipo = TipoItem.por_id(id_tipo)
            DBSession.delete(tipo)
        transaction.commit()
        redirect(atras)
    #}
