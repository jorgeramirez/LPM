# -*- coding: utf-8 -*-
"""
Módulo que define el controlador de historial
de líneas bases.

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

from lpm.model import (DBSession, Item, TipoItem, Fase, PropiedadItem, Usuario,
                       Relacion, LB, ItemsPorLB, HistorialItems, HistorialLB)
from lpm.model.excepciones import *
from lpm.lib.sproxcustom import (CustomTableFiller,
                                 CustomPropertySingleSelectField)
from lpm.lib.authorization import PoseePermiso, AlgunPermiso
from lpm.lib.util import UrlParser

from sprox.tablebase import TableBase
from sprox.fillerbase import TableFiller, EditFormFiller
from sprox.fillerbase import EditFormFiller
from sprox.formbase import AddRecordForm, EditableForm

from tw.forms.fields import TextField, TextArea

from repoze.what.predicates import not_anonymous

from sqlalchemy import and_, or_
import pylons
from pylons import tmpl_context

import transaction

class HistorialLBTable(TableBase):
    __model__ = HistorialLB
    __headers__ = { 'tipo_operacion': u'Tipo de Operación',
                    'fecha_modificacion': u'Fecha de Mofificacion',
                    'nombre_usuario': u'Nombre de Usuario'
                  }
    __omit_fields__ = ['id_historial_lb', 'id_usuario', 'id_lb', 'usuario',
                       'lb']
    __default_column_width__ = '15em'
    __column_widths__ = { '__actions__': "50em"}
    __add_fields__ = {'nombre_usuario': None}
    __field_order__ = ["tipo_operacion", "nombre_usuario", 
                       "fecha_modificacion"]
    
historial_lb_table = HistorialLBTable(DBSession)


class HistorialLBTableFiller(CustomTableFiller):
    __model__ = HistorialLB
    __add_fields__ = {'nombre_usuario': None}
    
    def nombre_usuario(self, obj, **kw):
        return obj.usuario.nombre_usuario
    
    def __actions__(self, obj):
        """Links de acciones para un registro dado"""

        value = '<div>'
        clase = 'actions_fase'
        id = str(obj.id_lb)
        id_fase = UrlParser.parse_id(request.url, "fases")
        if PoseePermiso('consultar lb',
                        id_fase=id_fase).is_met(request.environ):
            value += '<div>' + '<a href="./' + 'examinar/'  + id + \
                        '" class="' + clase + '">Examinar</a>' + \
                     '</div><br />'                
        value += '</div>'
        return value
    
    def _do_get_provider_count_and_objs(self, lb=None, **kw):
        """
        Recupera el historial de la linea base en cuestion
        """
        count, lista = super(HistorialLBTableFiller, self).\
                            _do_get_provider_count_and_objs(**kw)
        filtrados = []
        for hlb in lb.historial_lb:
            if hlb in lista:
                filtrados.append(hlb)
        return len(filtrados), filtrados


historial_lb_table_filler = HistorialLBTableFiller(DBSession)


class ItemLBTable(TableBase):
    __model__ = ItemsPorLB
    __headers__ = { 'version': u'Versión',
                    'complejidad': u'Complejidad',
                    'codigo_item': u'Código',
                    'estado': u'Estado'
                  }
    __omit_fields__ = ['id_item_por_lb', 'id_item', 'id_lb', 'propiedad_item',
                       "__actions__", "lb"]
    __add_fields__ = {'version': None, 'complejidad': None,
                      'codigo_item': None, 'estado': None
                     }
    __default_column_width__ = '15em'
    __column_widths__ = { '__actions__': "50em"}
    __field_order__ = ["codigo_item", "version", "estado", "complejidad"]
    
item_lb_table = ItemLBTable(DBSession)


class ItemLBTableFiller(CustomTableFiller):
    __model__ = ItemsPorLB
    __add_fields__ = {'version': None, 'complejidad': None,
                      'codigo_item': None, 'estado': None
                     }
                     
    def version(self, obj, **kw):
        return obj.propiedad_item.version

    def complejidad(self, obj, **kw):
        return obj.propiedad_item.complejidad

    def estado(self, obj, **kw):
        return obj.propiedad_item.estado

    def codigo_item(self, obj, **kw):
        return Item.por_id(obj.propiedad_item.id_item_actual).codigo
        
    def __actions__(self, obj):
        """Links de acciones para un registro dado"""
        return "<div></div>"
    
    def _do_get_provider_count_and_objs(self, lb=None, **kw):
        """
        Recupera los ítems que forman parte de la lb en cuestión.
        """
        count, lista = super(ItemLBTableFiller, self).\
                            _do_get_provider_count_and_objs(**kw)
        filtrados = []                    
        for iplb in lb.items:
            if iplb in lista:
                filtrados.append(iplb)
        return len(filtrados), filtrados

item_lb_table_filler = ItemLBTableFiller(DBSession)


class HistorialLBController(CrudRestController):
    """Controlador de Historial de una Línea Base"""

    #{ Variables
    title = u"Historial de la Línea Base: %s"
    allow_only = not_anonymous(u"El usuario debe haber iniciado sesión")

    #{plantillas
    tmp_action = "./"
    
    #{ Modificadores
    model = HistorialLB
    table = historial_lb_table
    table_filler = historial_lb_table_filler

    opciones = dict(tipo_operacion=u'Tipo de Operación',
                    fecha_modificacion= u'Fecha de Mofificación'
                    )
    columnas = dict(tipo_operacion=u'texto',
                    fecha_modificacion= u'fecha'
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
        id_lb = UrlParser.parse_id(request.url, "lbs")
        lb = LB.por_id(id_lb)
        titulo = self.title % lb.codigo
        tmpl_context.widget = self.table
        historial = self.table_filler.get_value(lb=lb, **kw)
        return dict(lista_elementos=historial, 
                    page=titulo,
                    titulo=titulo,
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
        id_lb = UrlParser.parse_id(request.url, "lbs")
        lb = LB.por_id(id_lb)
        titulo = self.title % lb.codigo
        tmpl_context.widget = self.table
        buscar_table_filler = HistorialLBTableFiller(DBSession)
        buscar_table_filler.filtros = kw
        historial = self.table_filler.get_value(lb=lb, **kw)
        return dict(lista_elementos=historial, 
                    page=titulo,
                    titulo=titulo, 
                    modelo=self.model.__name__,
                    columnas=self.columnas,
                    url_action='../',
                    opciones=self.opciones,
                    atras='../'
                    )

    @with_trailing_slash
    @paginate('lista_elementos', items_per_page=5)
    @expose('lpm.templates.lb.examinar')
    @expose('json')
    def examinar(self, *args, **kw):
        """ 
        Muestra los elementos que forman parte de la LB
        """
        id_lb = int(args[0])
        lb = LB.por_id(id_lb)
        titulo = u"Ítems de Línea Base: %s" % lb.codigo
        iplbs = item_lb_table_filler.get_value(lb=lb, **kw)
        tmpl_context.widget = item_lb_table
        atras = "../../"
        return dict(lista_elementos=iplbs, 
                    page=titulo,
                    titulo=titulo, 
                    modelo="ItemsPorLB",
                    atras=atras
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
    
    @expose()
    def edit(self, *args, **kw):
        pass
        
    @expose()
    def put(self, *args, **kw):
        pass
    #}
