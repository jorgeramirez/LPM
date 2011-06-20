# -*- coding: utf-8 -*-
"""
Módulo que define el controlador de atributos de un
ítem dado.

@authors:
    - U{Carlos Bellino<mailto:carlosbellino@gmail.com>}
    - U{Nahuel Hernández<mailto:nahuel.11990@gmail.com>}
    - U{Jorge Ramírez<mailto:jorgeramirez1990@gmail.com>}

@since: 1.0
"""
from tgext.crud import CrudRestController
from tg.decorators import (paginate, expose, with_trailing_slash,
                           without_trailing_slash)
from tg import redirect, request, validate, flash

from lpm.model import (DBSession, AtributosDeItems, AtributosPorItem, Item, 
                       TipoItem, Fase, PropiedadItem, AtributosPorTipoItem)
from lpm.lib.sproxcustom import (CustomTableFiller,
                                 CustomPropertySingleSelectField)
from lpm.lib.authorization import PoseePermiso, AlgunPermiso
from lpm.lib.util import UrlParser

from sprox.tablebase import TableBase
from sprox.fillerbase import TableFiller, EditFormFiller
from sprox.fillerbase import EditFormFiller
from sprox.formbase import AddRecordForm, EditableForm

from tw.forms.fields import TextField

from repoze.what.predicates import not_anonymous

import pylons
from pylons import tmpl_context

import transaction


class AtributoItemTable(TableBase):
    __model__ = AtributosPorItem
    __headers__ = {'nombre': u'Nombre', 'valor': u'Valor'}
    __add_fields__ = {'nombre': None, 'valor': None}
    __omit_fields__ = ['id_atributos_por_item', 'id_propiedad_item',
                       'id_atributos_de_items', 'atributo']
    __default_column_width__ = '15em'
    __column_widths__ = { '__actions__': "50em"}
    __field_order__ = ['nombre', 'valor']
    
atributo_item_table = AtributoItemTable(DBSession)


class AtributoItemTableFiller(CustomTableFiller):
    __model__ = AtributosPorItem
    __add_fields__ = {'nombre': None, 'valor': None}
    
    def nombre(self, obj, **kw):
        id = obj.atributo.id_atributos_por_tipo_item
        attr_por_tipo = AtributosPorTipoItem.por_id(id)
        return attr_por_tipo.nombre
    
    def valor(self, obj, **kw):
        return obj.atributo.valor
    
    def __actions__(self, obj):
        """Links de acciones para un registro dado"""

        if UrlParser.parse_nombre(request.url, "versiones"):
            #no se hace nada desde el controlador de versiones.
            return '<div></div>'

        value = '<div>'
        clase = 'actions_fase'
        id = str(obj.id_atributos_por_item)
        controller = "./atributos/" + id
        id_item = UrlParser.parse_id(request.url, "items")
        item = Item.por_id(id_item)

        if PoseePermiso('modificar item', 
                        id_fase=item.id_fase).is_met(request.environ):
            value += '<div>' + \
                        '<a href="./'+ controller +'/edit" ' + \
                        'class="' + clase + '">Modificar</a>' + \
                     '</div><br />'
        
        value += '</div>'
        return value
    
    def _do_get_provider_count_and_objs(self, id_version=None, **kw):
        """
        Recupera los  atributos de la versión del ítem indicado.
        """
        count, lista = super(AtributoItemTableFiller, self).\
                            _do_get_provider_count_and_objs(**kw)
        filtrados = []                    
        if id_version:
            p_item = PropiedadItem.por_id(id_version)
            item = Item.por_id(p_item.id_item_actual)
            ap = AlgunPermiso(tipo='Fase',
                              id_fase=item.id_fase).is_met(request.environ)
            if ap:
                for attr_por_item in p_item.atributos:
                    if attr_por_item in lista:
                        filtrados.append(attr_por_item)

        return len(filtrados), filtrados


atributo_item_table_filler = AtributoItemTableFiller(DBSession)


class AtributoItemEditForm(EditableForm):
    __model__ = AtributosPorItem
    __hide_fields__ = ['id_atributos_por_item', 'id_propiedad_item',
                       'id_atributos_de_items', 'atributo']
    __add_fields__ = {"valor": None, "nombre": None}
    valor = TextField("valor", label_text="Valor")
    valor = TextField("nombre", label_text="Nombre")
    __field_order__ = ["nombre", "valor"]


atributo_item_edit_form = AtributoItemEditForm(DBSession)


class AtributoItemEditFiller(EditFormFiller):
    __model__ = AtributosPorItem
    __add_fields__ = {"valor": None, "nombre": None}
    
    def valor(self, obj, **kw):
        pass
    
    def nombre(self, obj, **kw):
        pass

atributo_item_edit_filler = AtributoItemEditFiller(DBSession)


class AtributoItemController(CrudRestController):
    """Controlador de atributos de ítem"""

    #{ Variables
    title = u"Atributos de Ítem"
    allow_only = not_anonymous(u"El usuario debe haber iniciado sesión")
    
    #{plantillas
    tmp_action = "./"
    
    #{ Modificadores
    model = AtributosPorItem
    table = atributo_item_table
    table_filler = atributo_item_table_filler     
    edit_form = atributo_item_edit_form
    edit_filler = atributo_item_edit_filler
    
    opciones = dict(nombre= u'Nombre')
    columnas = dict(nombre='texto')
    
    #{ Métodos
    @with_trailing_slash
    @paginate('lista_elementos', items_per_page=5)
    @expose('lpm.templates.atributoitem.get_all')
    @expose('json')
    def get_all(self, *args, **kw):
        """ 
        Retorna todos los registros
        Retorna una página HTML si no se especifica JSON
        """
        id_item = UrlParser.parse_id(request.url, "items")
        id_version = UrlParser.parse_id(request.url, "versiones")
        titulo = self.title
        atributos = {}
        if id_version:
            #desde controller de versiones
            p_item = PropiedadItem.por_id(id_version)
            titulo = u"Atributos de Version: %d" % p_item.version
            atributos = self.table_filler. \
                        get_value(id_version=p_item.id_propiedad_item, **kw)
        elif id_item:
            #desde controller de items.
            item = Item.por_id(id_item)
            titulo = u"Atributos de Ítem: %s" % item.codigo
            atributos = self.table_filler. \
                        get_value(id_version=item.id_propiedad_item, **kw)
        
        tmpl_context.widget = self.table
        return dict(lista_elementos=atributos, 
                    page=titulo,
                    titulo=titulo, 
                    modelo=self.model.__name__, 
                    columnas=self.columnas,
                    opciones=self.opciones,
                    url_action=self.tmp_action
                    )
    
    @without_trailing_slash
    @paginate('lista_elementos', items_per_page=5)
    @expose('lpm.templates.atributoitem.get_all')
    @expose('json')
    def post_buscar(self, *args, **kw):
        """
        Controlador que recibe los parámetros de búsqueda para 
        devolver el resultado esperado.
        """
        id_item = UrlParser.parse_id(request.url, "items")
        id_version = UrlParser.parse_id(request.url, "versiones")
        titulo = self.title
        atributos = {}
        buscar_table_filler = AtributoItemTableFiller(DBSession)
        buscar_table_filler.filtros = kw
        if id_version:
            #desde controller de versiones
            p_item = PropiedadItem.por_id(id_version)
            titulo = u"Atributos de Version: %d" % p_item.version
            atributos = buscar_table_filler. \
                        get_value(id_version=p_item.id_propiedad_item)
        elif id_item:
            #desde controller de items.
            item = Item.por_id(id_item)
            titulo = u"Atributos de Ítem: %s" % item.codigo
            atributos = buscar_table_filler. \
                        get_value(id_version=item.id_propiedad_item)

        tmpl_context.widget = self.table
        return dict(lista_elementos=atributos, 
                    page=titulo,
                    titulo=titulo,
                    modelo=self.model.__name__,
                    columnas=self.columnas,
                    url_action='../',
                    opciones=self.opciones,
                    atras='../'
                    )
    
    @expose()
    def get_one(self, *args, **kw):
        pass

    @expose()
    def new(self, *args, **kw):
        pass
    
    @expose()
    def post_delete(self, id):
        pass
        
    @expose()
    def post(self, *args, **kw):
        pass
    
    @expose('lpm.templates.atributoitem.edit')
    def edit(self, *args, **kw):
        """Despliega una pagina para realizar modificaciones"""
        id_item = UrlParser.parse_id(request.url, "items")
        id_version = UrlParser.parse_id(request.url, "versiones")
        id = int(args[0]) #identificador del atributo
        titulo = self.title

        if id_version:
            #desde controller de versiones
            p_item = PropiedadItem.por_id(id_version)
            titulo = u"Atributo de Versión: %d" % p_item.version
        elif id_item:
            #desde controller de items.
            item = Item.por_id(id_item)
            titulo = u"Atributo de Ítem: %s" % item.codigo

        value = self.edit_filler.get_value(values={'id_atributos_por_item': id})                                
        tmpl_context.widget = self.edit_form
        return dict(value=value,
                    page=titulo
                    )
        
    @validate(atributo_item_edit_form, error_handler=edit)
    @expose()
    def put(self, *args, **kw):
        """update"""
        if "sprox_id" in kw:
            del kw["sprox_id"]
        id_item = UrlParser.parse_id(request.url, "items")
        id = int(args[0]) #identificador del atributo
        if UrlParser.parse_nombre(request.url, "versiones"):
            #No debe poder modificarse, solo visualizar. TODO
            redirect('../')
        if id_item:
            #desde controller de items.
            item = Item.por_id(id_item)
        #TODO
        redirect("../")
    #}
