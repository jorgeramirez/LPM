# -*- coding: utf-8 -*-
"""
Módulo que define el controlador de versiones de 
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

from lpm.model import (DBSession, PropiedadItem, Item, TipoItem, Usuario)
from lpm.lib.sproxcustom import (CustomTableFiller,
                                 CustomPropertySingleSelectField)
from lpm.lib.authorization import PoseePermiso, AlgunPermiso
from lpm.lib.util import UrlParser
from lpm.controllers.atributoitem import AtributoItemController
from lpm.controllers.adjunto import AdjuntoController
from lpm.controllers.relacion import RelacionController
from lpm.controllers.historialitem import HistorialItemController

from sprox.tablebase import TableBase
from sprox.fillerbase import TableFiller, EditFormFiller
from sprox.fillerbase import EditFormFiller
from sprox.formbase import AddRecordForm, EditableForm

from repoze.what.predicates import not_anonymous

import pylons
from pylons import tmpl_context

import transaction


class VersionTable(TableBase):
    __model__ = PropiedadItem
    __headers__ = { 'version': u'Versión',
                    'complejidad': u'Complejidad',
                    'prioridad': u'Prioridad',
                    'estado': u'Estado'
                  }
    __omit_fields__ = ['id_propiedad_item', 'id_item_actual', 'relaciones',
                       'archivos', 'atributos', 'historial_item',
                       'item_lb_assocs', 'descripcion', 'observaciones']
    __default_column_width__ = '15em'
    __column_widths__ = { '__actions__': "50em"}
    __field_order__ = ["version", "complejidad", "prioridad", "estado"]
    
version_table = VersionTable(DBSession)


class VersionTableFiller(CustomTableFiller):
    __model__ = PropiedadItem
    
    def __actions__(self, obj):
        """Links de acciones para un registro dado"""

        value = '<div>'
        clase = 'actions_fase'
        item = Item.por_id(obj.id_item_actual)
        p_item = PropiedadItem.por_id(item.id_propiedad_item)
        id = obj.id_propiedad_item

        controller = "./" + str(obj.id_propiedad_item)
        controller2 = "./"
        if (UrlParser.parse_nombre(request.url, "post_buscar")):#desde post_buscar
            controller = "../" + str(obj.id_propiedad_item)
            controller2 = "../"

            
        
        value += '<div>' + \
                    '<a href="' + controller + '/edit" ' +  \
                    'class="' + clase + '">Detalles</a>' + \
                 '</div><br />'
                 
        if PoseePermiso('modificar item',
                        id_tipo_item=item.id_tipo_item).is_met(request.environ):
                
            if p_item.estado not in [u"Bloqueado", u"Eliminado", u"Revisión-Bloq"] and\
                id != p_item.id_propiedad_item:
                value += '<div>' + \
                            '<a href="' + controller2 + 'revertir/'+ str(id) + '" ' + \
                            'class="' + clase + '">Volver a versión</a>' + \
                         '</div><br />'
                     
        value += '<div>' + \
            '<a href="' + controller +'/adjuntos" ' + \
            'class="' + clase + '">Adjuntos</a>' + \
            '</div><br />'
            
        value += '<div>' + \
            '<a href="' + controller +'/relaciones_ph" ' + \
            'class="' + clase + '">Relaciones P-H</a>' + \
            '</div><br />'
            
        value += '<div>' + \
            '<a href="' + controller +'/relaciones_as" ' + \
            'class="' + clase + '">Relaciones A-S</a>' + \
            '</div><br />'
        
        value += '<div>' + \
            '<a href="' + controller +'/historial" ' + \
            'class="' + clase + '">Historial</a>' + \
            '</div><br />'
                    
        value += '</div>'
        return value
    
    def _do_get_provider_count_and_objs(self, id_item=None, **kw):
        """
        Recupera las versiones del ítem en cuestión.
        """
        count, lista = super(VersionTableFiller, self).\
                            _do_get_provider_count_and_objs(**kw)
        filtrados = []                    
        if id_item:
            id_item = int(id_item)
            item = Item.por_id(id_item)
            for p_item in reversed(item.propiedad_item_versiones):
                if p_item in lista:
                    filtrados.append(p_item)
        return len(filtrados), filtrados


version_table_filler = VersionTableFiller(DBSession)


class VersionEditForm(EditableForm):
    __model__ = PropiedadItem
    __hide_fields__ = ['id_propiedad_item', 'id_item_actual', 'relaciones',
                       'archivos', 'atributos', 'historial_item',
                       'item_lb_assocs']

version_edit_form = VersionEditForm(DBSession)


class VersionEditFiller(EditFormFiller):
    __model__ = PropiedadItem

version_edit_filler = VersionEditFiller(DBSession)


class VersionController(CrudRestController):
    """Controlador de Versiones de un Ítem"""

    #{ Variables
    title = u"Versiones del Ítem"
    allow_only = not_anonymous(u"El usuario debe haber iniciado sesión")

    #{Subcontroladores
    adjuntos = AdjuntoController(DBSession)
    atributos = AtributoItemController(DBSession)
    relaciones_ph = RelacionController(DBSession)
    relaciones_as = RelacionController(DBSession)
    historial = HistorialItemController(DBSession)
    
    #{plantillas
    tmp_action = "./"
    
    #{ Modificadores
    model = PropiedadItem
    table = version_table
    table_filler = version_table_filler
    edit_form = version_edit_form
    edit_filler = version_edit_filler

    opciones = dict(version=u'Versión',
                    estado= u'Estado',
                    complejidad=u'Complejidad',
                    prioridad =u'Prioridad'
                    )
    columnas = dict(version=u'entero',
                    estado= u'combobox',
                    complejidad=u'combobox',
                    prioridad =u'combobox'
                    )
    comboboxes = dict(estado=Item.estados_posibles.values(),
                      complejidad=range(1,11),
                      prioridad=range(1,11))
    
    #{ Métodos
    @with_trailing_slash
    @paginate('lista_elementos', items_per_page=5)
    @expose('lpm.templates.version.get_all')
    @expose('json')
    def get_all(self, *args, **kw):
        """ 
        Retorna todos los registros
        Retorna una página HTML si no se especifica JSON
        """
        titulo = self.title
        id_item = UrlParser.parse_id(request.url, "items")
        if id_item:
           item = Item.por_id(id_item)
           titulo = u"Versiones del Ítem: %s" % item.codigo 
        tmpl_context.widget = self.table
        versiones = self.table_filler.get_value(id_item=id_item, **kw)
        return dict(lista_elementos=versiones, 
                    page=titulo,
                    titulo=self.title, 
                    modelo=self.model.__name__, 
                    columnas=self.columnas,
                    opciones=self.opciones,
                    url_action=self.tmp_action,
                    comboboxes=self.comboboxes,
                    atras="../"
                    )
    
    @without_trailing_slash
    @paginate('lista_elementos', items_per_page=5)
    @expose('lpm.templates.version.get_all')
    @expose('json')
    def post_buscar(self, *args, **kw):
        """
        Controlador que recibe los parámetros de búsqueda para 
        devolver el resultado esperado.
        """
        titulo = self.title
        id_item = UrlParser.parse_id(request.url, "items")
        if id_item:
           item = Item.por_id(id_item)
           titulo = u"Versiones del Ítem: %s" % item.codigo 
        tmpl_context.widget = self.table
        buscar_table_filler = VersionTableFiller(DBSession)
        buscar_table_filler.filtros = kw
        versiones = buscar_table_filler.get_value(id_item=id_item)
        return dict(lista_elementos=versiones, 
                    page=self.title, 
                    titulo=self.title, 
                    modelo=self.model.__name__,
                    columnas=self.columnas,
                    url_action='../',
                    comboboxes=self.comboboxes,
                    opciones=self.opciones,
                    atras='../../'
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
        id_item = UrlParser.parse_id(request.url, "items")
        id = int(args[0])
        value = self.edit_filler.get_value(values={'id_propiedad_item': id})
        item = Item.por_id(id_item)
        page = u"Versión %d del Ítem: %s" % (value["version"], item.codigo)
        tmpl_context.widget = self.edit_form
        #tmpl_context.tabla_atributos = self.atributos.table
        #atributos = self.atributos.table_filler.get_value(id_version=id)        
        #tmpl_context.tabla_relaciones = self.relaciones.table
        #relaciones = self.relaciones.table_filler.get_value(id_version=id)
        atras = "../"
        return dict(value=value,
                    page=page,
                    id=str(id_item),
                    #atributos=atributos,
                    #relaciones=relaciones,
                    atras=atras
                    )
        
    @expose()
    def put(self, *args, **kw):
        pass

    @expose()
    def revertir(self, *args, **kw):
        """
        Revierte el ítem en cuestion a la version indicada.
        """
        id_item = UrlParser.parse_id(request.url, "items")
        id_version = int(args[0])
        if not id_item:
            redirect("../")
        item = Item.por_id(id_item)
        pp = PoseePermiso('modificar item', id_tipo_item=item.id_tipo_item)
        if not pp.is_met(request.environ):
            flash(pp.message % pp.nombre_permiso, 'warning')
            redirect("../")
        user = Usuario.by_user_name(request.credentials["repoze.what.userid"])
        item.revertir(id_version, user)
        redirect("../")
    #}
