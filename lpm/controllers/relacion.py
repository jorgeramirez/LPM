# -*- coding: utf-8 -*-
"""
Módulo que define el controlador de relaciones de un
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

from lpm.model import (DBSession, Relacion, RelacionPorItem, Item, 
                       PropiedadItem)
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


class RelacionTable(TableBase):
    __model__ = Relacion
    __headers__ = {'tipo': u'Tipo', 'codigo': u'Código',
                   'item_relacionado': u"Ítem Relacionado",
                   'estado': 'Estado'}
    __add_fields__ = {'item_relacionado': None,
                      'estado': None}
    __omit_fields__ = ['id_relacion', 'id_anterior', 'id_posterior']
    __default_column_width__ = '15em'
    __column_widths__ = { '__actions__': "50em"}
    __field_order__ = ['codigo', 'tipo', 'item_relacionado']
    __xml_fields__ = ['estado']
relacion_table = RelacionTable(DBSession)


class RelacionTableFiller(CustomTableFiller):
    __model__ = Relacion
    __add_fields__ = {'item_relacionado': None,
                      'estado': None}
    
    def item_relacionado(self, obj, **kw):
        id_item = UrlParser.parse_id(request.url, "items")
        otro = obj.obtener_otro_item(id_item)
        return otro.codigo
    
    def estado(self, obj, **kw):
        id_item = UrlParser.parse_id(request.url, "items")
        item = Item.por_id(id_item)
        rti = DBSession.query(RelacionPorItem).\
                            filter(and_(RelacionPorItem.id_propiedad_item\
                            == item.id_propiedad_item,\
                            RelacionPorItem.id_relacion == obj.id_relacion))\
                            .first()
        color = u"inherit; "
        estado = u"Normal"
        if(rti.revisar):
            color = u"#ff0000; "
            estado = u"Con revisión"
        value = '<div style="font-color:' + color + '">' + estado + '<div>'
        
        return value
    
    def __actions__(self, obj):
        """Links de acciones para un registro dado"""

        if UrlParser.parse_nombre(request.url, "versiones"):
            #no se hace nada desde el controlador de versiones.
            return '<div></div>'

        value = '<div>'
        clase = 'actions_fase'
        id = str(obj.id_relacion)
        controller = "./relaciones/" + id
        id_item = UrlParser.parse_id(request.url, "items")
        item = Item.por_id(id_item)

        if PoseePermiso('modificar item', 
                        id_fase=item.id_fase).is_met(request.environ):
            value += '<div><form method="POST" action="' + controller + '" class="button-to">'+\
                     '<input type="hidden" name="_method" value="DELETE" />' +\
                     '<input onclick="return confirm(\'¿Está seguro?\');" value="Eliminar" type="submit" '+\
                     'style="background-color: transparent; float:left; border:0; color: #286571; display: inline;'+\
                     'margin: 0; padding: 0;' + clase + '"/>'+\
                     '</form></div><br />'
        
        value += '</div>'
        return value
    
    def _do_get_provider_count_and_objs(self, id_version=None, **kw):
        """
        Recupera las relaciones de la versión del ítem indicado.
        """
        count, lista = super(RelacionTableFiller, self).\
                            _do_get_provider_count_and_objs(**kw)
        filtrados = []                    
        if id_version:
            p_item = PropiedadItem.por_id(id_version)
            item = Item.por_id(p_item.id_item_actual)
            #ver este permiso
            ap = AlgunPermiso(tipo='Fase',
                              id_fase=item.id_fase).is_met(request.environ)
            if ap:
                for rel_por_item in p_item.relaciones:
                    if rel_por_item.relacion in lista:
                        filtrados.append(rel_por_item.relacion)

        return len(filtrados), filtrados


relacion_table_filler = RelacionTableFiller(DBSession)



class RelacionController(CrudRestController):
    """Controlador de atributos de ítem"""

    #{ Variables
    title = u"Relaciones de Ítem"
    allow_only = not_anonymous(u"El usuario debe haber iniciado sesión")
    
    #{plantillas
    tmp_action = "./"
    
    #{ Modificadores
    model = Relacion
    table = relacion_table
    table_filler = relacion_table_filler     

    
    opciones = dict(tipo= u'Tipo', codigo=u'Código')
    columnas = dict(tipo='combobox', codigo='texto')
    
    comboboxes = dict(tipo=Relacion.tipo_relaciones.values())
    
    #{ Métodos
    @with_trailing_slash
    @paginate('lista_elementos', items_per_page=5)
    @expose('lpm.templates.relacion.get_all')
    @expose('json')
    def get_all(self, *args, **kw):
        """ 
        Retorna todos los registros
        Retorna una página HTML si no se especifica JSON
        """
        id_item = UrlParser.parse_id(request.url, "items")
        id_version = UrlParser.parse_id(request.url, "versiones")
        titulo = self.title
        relaciones = {}
        if id_version:
            #desde controller de versiones
            p_item = PropiedadItem.por_id(id_version)
            titulo = u"Relaciones de Version: %d" % p_item.version
            relaciones = self.table_filler. \
                        get_value(id_version=p_item.id_propiedad_item, **kw)
        elif id_item:
            #desde controller de items.
            item = Item.por_id(id_item)
            titulo = u"Relaciones de Ítem: %s" % item.codigo
            relaciones = self.table_filler. \
                        get_value(id_version=item.id_propiedad_item, **kw)
        
        tmpl_context.widget = self.table
        return dict(lista_elementos=relaciones, 
                    page=titulo,
                    titulo=titulo, 
                    modelo=self.model.__name__, 
                    columnas=self.columnas,
                    opciones=self.opciones,
                    comboboxes=self.comboboxes,
                    url_action=self.tmp_action
                    )
    
    @without_trailing_slash
    @paginate('lista_elementos', items_per_page=5)
    @expose('lpm.templates.relacion.get_all')
    @expose('json')
    def post_buscar(self, *args, **kw):
        """
        Controlador que recibe los parámetros de búsqueda para 
        devolver el resultado esperado.
        """
        id_item = UrlParser.parse_id(request.url, "items")
        id_version = UrlParser.parse_id(request.url, "versiones")
        titulo = self.title
        relaciones = {}
        buscar_table_filler = RelacionTableFiller(DBSession)
        buscar_table_filler.filtros = kw
        if id_version:
            #desde controller de versiones
            p_item = PropiedadItem.por_id(id_version)
            titulo = u"Relaciones de Version: %d" % p_item.version
            relaciones = buscar_table_filler. \
                        get_value(id_version=p_item.id_propiedad_item)
        elif id_item:
            #desde controller de items.
            item = Item.por_id(id_item)
            titulo = u"Relaciones de Ítem: %s" % item.codigo
            relaciones = buscar_table_filler. \
                        get_value(id_version=item.id_propiedad_item)

        tmpl_context.widget = self.table
        return dict(lista_elementos=relaciones,
                    page=titulo,
                    titulo=titulo,
                    modelo=self.model.__name__,
                    columnas=self.columnas,
                    url_action='../',
                    opciones=self.opciones,
                    comboboxes=self.comboboxes,                    
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
        #TODO llamado desde la pagina de edit Item, al seleccionar
        #el action de eliminar de un elemento de la tabla.
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
    
    @expose()
    def relacionar(self, *args, **kw):
        """
        Relaciona dos ítems.
        """
        # Este metodo es invocado desde la pagina de relacionar_item
        # al seleccionar el link del action Relacionar de un elemento 
        # de alguna de las dos tablas.
        # ./items/1/relacionar/2
        # se debera crear la relacion 1 con 2
        pass
    #}
