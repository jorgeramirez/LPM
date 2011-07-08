# -*- coding: utf-8 -*-
"""
Módulo que define el controlador simple de tipos de ítem
para proyectos.

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
                       Fase, TipoItem, Rol)
from lpm.lib.sproxcustom import CustomTableFiller
from lpm.lib.sproxcustom import WidgetSelectorDojo, MultipleSelectDojo
from lpm.lib.authorization import PoseePermiso, AlgunPermiso
from lpm.lib.util import UrlParser
from lpm.controllers.proyecto_atributotipoitem import \
                                (ProyectoAtributosPorTipoItemController)
from lpm.controllers.tipoitem import TipoItemTable

from sprox.tablebase import TableBase
from sprox.fillerbase import TableFiller
from sprox.fillerbase import EditFormFiller
from sprox.dojo.formbase import DojoAddRecordForm as AddRecordForm
from sprox.dojo.formbase import DojoEditableForm as EditableForm
from sprox.widgets import PropertySingleSelectField

from tw.forms.fields import (PasswordField, TextField, TextArea, Button, 
                             CheckBox)

from repoze.what.predicates import not_anonymous

from sqlalchemy import or_, and_
from tg import tmpl_context, request

import transaction


proyecto_tipo_item_table = TipoItemTable(DBSession)


class ProyectoTipoItemTableFiller(CustomTableFiller):
    __model__ = TipoItem
    __omit_fields__ = ['id_tipo_item', 'id_proyecto', 'id_padre',
                       'hijos', 'atributos', 'items', 'roles']
   
    def __actions__(self, obj):
        """Links de acciones para un registro dado"""
        value = '<div>'
        clase = 'actions'
        url_cont = "./" + str(obj.id_tipo_item)
        id_tipo = UrlParser.parse_id(request.url, "tipositems")
        if id_tipo:
            url_cont = "../" + str(obj.id_tipo_item)
        
        
        value += '<div>' + \
                    '<a href="' + url_cont + '/edit" ' + \
                    'class="' + clase + '">Ver</a>' + \
                 '</div><br />'

        value += '<div>' + \
                    '<a href="' + url_cont + '/atributostipoitem/" ' + \
                    'class="' + clase + '">Atributos</a>' + \
                 '</div><br />'        
        
        value += '</div>'
        return value
    
    def _do_get_provider_count_and_objs(self, id_proyecto=None, id_tipo=None, **kw):
        """
        Se muestra la lista de tipos de ítem para el proyecto en 
        cuestión
        """
        if not id_proyecto: 
            return 0, []
        
        if id_tipo:
            ti = TipoItem.por_id(id_tipo)
            return 1, [ti]
            
        count, lista = super(ProyectoTipoItemTableFiller, self).\
                            _do_get_provider_count_and_objs(**kw)
        filtrados = []                    
        for ti in lista:
            if ti.id_proyecto == id_proyecto:
                filtrados.append(ti)

        return len(filtrados), filtrados        


proyecto_tipo_item_table_filler = ProyectoTipoItemTableFiller(DBSession)


class ProyectoTipoItemEditForm(EditableForm):
    __model__ = TipoItem
    __hide_fields__ = ['id_tipo_item', 'id_proyecto', 'id_fase']
    __omit_fields__ = ['codigo', 'hijos', 'atributos', 'items', 'roles']
    __field_order__ = ['nombre', 'descripcion', 'id_padre' ]
    __field_attrs__ = {'descripcion' : {'row': '1'},
                       'nombre': { 'maxlength' : '50'}
                       
                      }
    __require_fields__ = ['nombre']
    id_padre = TextField("id_padre", accion="edit", label_text="Tipo Padre")
    descripcion = TextArea

proyecto_tipo_item_edit_form = ProyectoTipoItemEditForm(DBSession)




class ProyectoTipoItemEditFiller(EditFormFiller):
    __model__ = TipoItem
    
    def id_padre(self, obj, **kw):
        ti = TipoItem.por_id(obj.id_padre)
        if ti:
            return ti.nombre
        return "No Tiene"

proyecto_tipo_item_edit_filler = ProyectoTipoItemEditFiller(DBSession)

class ProyectoTipoItemController(CrudRestController):
    """Controlador para tipos de item"""
        
    #{ Variables
    title = u"Tipos de Ítem del Proyecto: %s"
    action = "./"
    subaction = "./atributostipoitem/"
    
    #{ subcontroller
    atributostipoitem = ProyectoAtributosPorTipoItemController(DBSession)
    
    #{ Plantillas

    # No permitir tipo_items anonimos (?)
    allow_only = not_anonymous(u"El usuario debe haber iniciado sesión")
    
    #{ Modificadores

        
    model = TipoItem
    table = proyecto_tipo_item_table
    table_filler = proyecto_tipo_item_table_filler
    edit_form = proyecto_tipo_item_edit_form
    edit_filler = proyecto_tipo_item_edit_filler

    #para el form de busqueda

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
        
        id_proyecto = UrlParser.parse_id(request.url, "proyectos")
        atras = "../"        
        proy = Proyecto.por_id(id_proyecto)
        puede_crear = False
        titulo = self.title % proy.nombre
        tipo_items = self.table_filler.get_value(id_proyecto=id_proyecto, 
                                                 **kw)
        tmpl_context.widget = self.table
        url_action = self.action

        return dict(lista_elementos=tipo_items,
                    page=titulo, 
                    titulo=titulo, 
                    modelo=self.model.__name__, 
                    columnas=self.columnas,
                    opciones=self.opciones, 
                    url_action=url_action,
                    puede_crear=puede_crear,
                    atras=atras
                    )

    @expose('lpm.templates.proyecto.tipoitem_edit')
    def edit(self, *args, **kw):
        """Despliega una pagina para modificar tipo_item"""
        id_tipo = UrlParser.parse_id(request.url, "tipositems")        
        value = self.edit_filler.get_value(values={'id_tipo_item': id_tipo})
        tmpl_context.widget = self.edit_form
        page = "Tipo Item {nombre}".format(nombre=value["nombre"])
        return dict(value=value, 
                    page=page, 
                    atras="../", 
                    url_action="../"
                    )

    @expose()
    def new(self, *args, **kw):
        pass
    
    @expose()
    def post(self, *args, **kw):
        pass
        
    @expose()
    def put(self, *args, **kw):
        pass
    
    @with_trailing_slash
    @paginate('lista_elementos', items_per_page=5)
    @expose('lpm.templates.tipoitem.get_all')
    @expose('json')
    def post_buscar(self, *args, **kw):
        id_proyecto = UrlParser.parse_id(request.url, "proyectos")
        atras = "../"        
        proy = Proyecto.por_id(id_proyecto)
        puede_crear = False
        titulo = self.title % proy.nombre
        
        tmpl_context.widget = self.table
        buscar_table_filler = self.table_filler.__class__(DBSession)
        buscar_table_filler.filtros = kw
        tipos_items = buscar_table_filler.get_value(id_proyecto=id_proyecto)
        
        return  dict(lista_elementos=tipos_items, 
                     page=titulo, 
                     titulo=titulo,
                     modelo=self.model.__name__, 
                     columnas=self.columnas,
                     opciones=self.opciones, 
                     url_action="../",
                     puede_crear=puede_crear,
                     atras=atras
                     )

    @expose()
    def post_delete(self, *args, **kw):
        pass

    @expose()
    def get_one(self, *args, **kw):
        pass
    #}
