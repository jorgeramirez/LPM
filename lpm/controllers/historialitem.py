# -*- coding: utf-8 -*-
"""
Módulo que define el controlador de historial de 
un Ítem.

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

from lpm.model import (DBSession, PropiedadItem, Item, TipoItem, Usuario,
                        HistorialItems)
from lpm.lib.sproxcustom import (CustomTableFiller,
                                 CustomPropertySingleSelectField)
from lpm.lib.authorization import PoseePermiso, AlgunPermiso
from lpm.lib.util import UrlParser
from lpm.controllers.atributoitem import AtributoItemTable, AtributoItemTableFiller
from lpm.controllers.adjunto import AdjuntoController
from lpm.controllers.relacion import RelacionTable, RelacionTableFiller

from sprox.tablebase import TableBase
from sprox.fillerbase import TableFiller, EditFormFiller
from sprox.fillerbase import EditFormFiller
from sprox.formbase import AddRecordForm, EditableForm

from repoze.what.predicates import not_anonymous

import pylons
from pylons import tmpl_context

import transaction


class HistorialItemTable(TableBase):
    __model__ = HistorialItems
    __headers__ = { 'tipo_modificacion': u'Tipo de Modificacion',
                    'fecha_modificacion': u'Fecha',
                    'nombre_usuario': u'Usuario',
                    'codigo': u'Código de Item'
                  }
    __omit_fields__ = ['id_historial_items', 'id_usuario', 'id_item', 'usuario',
                       'item']
    __default_column_width__ = '15em'
    __column_widths__ = { '__actions__': "50em"}
    __add_fields__ = {'nombre_usuario': None, 'codigo' : None}
    __field_order__ = ["codigo", "tipo_modificacion", "nombre_usuario", "fecha_modificacion"]
    
historial_item_table = HistorialItemTable(DBSession)


class HistorialItemTableFiller(CustomTableFiller):
    __model__ = HistorialItems
    __add_fields__ = {'nombre_usuario': None, 'codigo': u'Código de Item'}
    
    def nombre_usuario(self, obj, **kw):
        return obj.usuario.nombre_usuario
    
    def codigo(self, obj, **kw):
        item = Item.por_id(obj.item.id_item_actual)
        return item.codigo
    
    def __actions__(self, obj):
        """Links de acciones para un registro dado"""

        value = '<div>'
        clase = 'actions_fase'
        id = obj.id_historial_items
        item = Item.por_id(obj.item.id_item_actual)
        if PoseePermiso('consultar item',
                        id_tipo_item=item.id_tipo_item).is_met(request.environ):
            value += '<div>' + '<a href="./' + str(id) + '/edit" ' +  \
                        'class="' + clase + '">Examinar</a>' + \
                     '</div><br />'                
        value += '</div>'
        return value
    
    def _do_get_provider_count_and_objs(self, id_usuario=None, **kw):
        """
        Recupera el historioal de operaciones del usuario.
        """
        count, lista = super(HistorialItemTableFiller, self).\
                            _do_get_provider_count_and_objs(**kw)
        filtrados = []                    
        if id_usuario:
            id_usuario = int(id_usuario)
            for p_lista in reversed(lista):
                if p_lista.id_usuario == id_usuario:
                    filtrados.append(p_lista)
        return len(filtrados), filtrados


historial_item_filler = HistorialItemTableFiller(DBSession)


class VersionEditForm(EditableForm):
    __model__ = PropiedadItem
    __hide_fields__ = ['id_propiedad_item', 'id_item_actual', 'relaciones',
                       'archivos', 'atributos', 'historial_item',
                       'item_lb_assocs']

version_edit_form = VersionEditForm(DBSession)


class VersionEditFiller(EditFormFiller):
    __model__ = PropiedadItem
    
version_edit_filler = VersionEditFiller(DBSession)


class HistorialItemController(CrudRestController):
    """Controlador de Historial de un Ítem"""

    #{ Variables
    title = u"Historial del Ítem"
    allow_only = not_anonymous(u"El usuario debe haber iniciado sesión")

    #{plantillas
    tmp_action = "./"
    
    #{ Modificadores
    model = HistorialItems
    table = historial_item_table
    table_filler = historial_item_filler
    edit_form = version_edit_form
    edit_filler = version_edit_filler

    opciones = dict(tipo_modificacion=u'Tipo de Modificacion',
                    fecha_modificacion= u'Fecha de Mofificacion',
                    nombre_usuario=u'Nombre de Usuario',
                    )
    columnas = dict(tipo_modificacion=u'texto',
                    fecha_modificacion= u'fecha',
                    nombre_usuario =u'texto'
                    )
    
    #{ Métodos
    @with_trailing_slash
    @paginate('lista_elementos', items_per_page=5)
    @expose('lpm.templates.historialitem.get_all')
    @expose('json')
    def get_all(self, *args, **kw):
        """ 
        Retorna todos los registros
        Retorna una página HTML si no se especifica JSON
        """
        titulo = self.title
        id_usuario = UrlParser.parse_id(request.url, "usuarios")
        if id_usuario:
           usuario = Usuario.por_id(id_usuario)
           titulo = u"Historial de Item de: %s" % usuario.nombre_usuario 
        tmpl_context.widget = self.table
        items = self.table_filler.get_value(id_usuario=id_usuario, **kw)
        return dict(lista_elementos=items, 
                    page=titulo,
                    titulo=self.title, 
                    modelo=self.model.__name__, 
                    columnas=self.columnas,
                    opciones=self.opciones,
                    url_action=self.tmp_action,
                    atras="../../"
                    )
    
    @without_trailing_slash
    @paginate('lista_elementos', items_per_page=5)
    @expose('lpm.templates.historialitem.get_all')
    @expose('json')
    def post_buscar(self, *args, **kw):
        """
        Controlador que recibe los parámetros de búsqueda para 
        devolver el resultado esperado.
        """
        titulo = self.title
        id_usuario = UrlParser.parse_id(request.url, "usuarios")
        if id_usuario:
           usuario = Usuario.por_id(id_usuario)
           titulo = u"Historial de Item de: %s" % usuario.nombre_usuario
        tmpl_context.widget = self.table
        buscar_table_filler = HistorialItemTableFiller(DBSession)
        buscar_table_filler.filtros = kw
        items = self.table_filler.get_value(id_usuario=id_usuario, **kw)
        return dict(lista_elementos=items, 
                    page=self.title, 
                    titulo=self.title, 
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
    
    @expose('lpm.templates.version.edit')
    def edit(self, *args, **kw):
        """ Despliega una pagina donde se puede ver el estado del ítem
            para la versión dada.
        """
        id = int(args[0])
        historial = HistorialItems.por_id(id)
        id_item = historial.item.id_propiedad_item
        value = self.edit_filler.get_value(values={'id_propiedad_item': id_item})
        item = Item.por_id(id_item)
        page = u"Versión %d del Ítem: %s" % (value["version"], item.codigo)
        tmpl_context.widget = self.edit_form
        
        atributos_table = AtributoItemTable(DBSession)
        atributos_table_filler = AtributoItemTableFiller(DBSession)
        
        tmpl_context.tabla_atributos = atributos_table
        atributos = atributos_table_filler.get_value(id_version=id_item)        
        
        relacion_table = RelacionTable(DBSession)
        relacion_table_filler = RelacionTableFiller(DBSession)
        
        tmpl_context.tabla_relaciones = relacion_table
        relaciones = relacion_table_filler.get_value(id_version=id_item)
        
        atras = "../"
        return dict(value=value,
                    page=page,
                    id=str(id_item),
                    atributos=atributos,
                    relaciones=relaciones,
                    atras=atras
                    )
    @expose()
    def put(self, *args, **kw):
        pass

    @expose()
    def revertir(self, *args, **kw):
        pass
    #}
 
