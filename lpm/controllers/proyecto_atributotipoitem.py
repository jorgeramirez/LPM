# -*- coding: utf-8 -*-
"""
Módulo que define el simple controlador de atributos de 
tipos de ítem. El mismo es utilizado por el controlador
de tipos de ítem de proyecto.

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
from lpm.controllers.atributotipoitem import \
                                        (AtributosPorTipoItemTable,
                                         AtributosPorTipoItemEditFiller)

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


atributos_por_tipo_item_table = AtributosPorTipoItemTable(DBSession)


class AtributosPorTipoItemTableFiller(CustomTableFiller):
    __model__ = AtributosPorTipoItem
    __omit_fields__ = ['id_tipo_item', 'id_atributos_por_tipo_item']
   
    def __actions__(self, obj):
        """Links de acciones para un registro dado"""
        return '<div></div>'
    
    def _do_get_provider_count_and_objs(self, id_tipo_item=None,**kw):
        """
        Se muestra la lista de atributos del tipo de ítem
        """
        count, lista = super(AtributosPorTipoItemTableFiller, 
                             self)._do_get_provider_count_and_objs(**kw)
                             
        id_tipo = UrlParser.parse_id(request.url, "tipositems")
        ti = TipoItem.por_id(id_tipo)
        pks = []
        actual = ti
        while actual:
            for attr in actual.atributos:
                pks.append(attr.id_atributos_por_tipo_item)
            actual = TipoItem.por_id(actual.id_padre)
            
        filtrados = []
        for attr in lista:
            if attr.id_atributos_por_tipo_item in pks:
                filtrados.append(attr)
        return len(filtrados), filtrados


atributos_por_tipo_item_table_filler = AtributosPorTipoItemTableFiller(DBSession)


class ProyectoAtributosPorTipoItemController(CrudRestController):
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
        puede_crear = False
        tipo = TipoItem.por_id(id_tipo_item)
        titulo = self.title % tipo.nombre
        atributos = self.table_filler.get_value(id_tipo_item=id_tipo_item, **kw)
        tmpl_context.widget = self.table
        url_action = self.action
        atras = "../../"
        
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
    @expose()
    def edit(self, *args, **kw):
        pass

    @expose()
    def new(self, *args, **kw):
        pass
    
    @expose()
    def post(self, *args, **kw):
        pass
        
    @expose()
    def put(self, *args, **kw):
        pass

    @expose()
    def post_delete(self, *args, **kw):
        pass

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
        puede_crear = False
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
