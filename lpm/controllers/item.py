# -*- coding: utf-8 -*-
"""
Módulo que define el controlador de ítems.

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

from lpm.model import DBSession, Item, TipoItem, Fase, Proyecto
from lpm.lib.sproxcustom import (CustomTableFiller,
                                 CustomPropertySingleSelectField)
from lpm.lib.authorization import PoseePermiso, AlgunPermiso
from lpm.lib.util import UrlParser
from lpm.controllers.version import VersionController
from lpm.controllers.adjunto import AdjuntoController
from lpm.controllers.atributoitem import AtributoItemController
from lpm.controllers.relacion import (RelacionController, RelacionTable,
                                      RelacionTableFiller)

from sprox.tablebase import TableBase
from sprox.fillerbase import TableFiller, EditFormFiller
from sprox.fillerbase import EditFormFiller
from sprox.formbase import AddRecordForm, EditableForm

from tw.forms.fields import TextField

from repoze.what.predicates import not_anonymous

import pylons
from pylons import tmpl_context

import transaction


class ItemTable(TableBase):
    __model__ = Item
    __headers__ = { 'codigo': u'Código',
                    'complejidad': 'Complejidad',
                    'codigo_tipo': u'Tipo de Ítem',
                    'version_actual': u'Versión Actual',
                    'estado': u'Estado',
                    'codigo_fase': 'Fase'
                  }
    __add_fields__ = {'codigo_tipo': None,
                      'version_actual': None, 'estado': None,
                      'codigo_fase': None, 'complejidad': None}
    __omit_fields__ = ['id_item', 'numero', 'numero_por_tipo', 'id_tipo_item',
                       'id_propiedad_item', 'propiedad_item_versiones',
                       'id_fase']
    __default_column_width__ = '15em'
    __column_widths__ = { '__actions__': "50em"}
    __field_order__ = ["codigo", "complejidad", "codigo_tipo",
                       "version_actual", "estado", "codigo_fase"]
    
item_table = ItemTable(DBSession)


class ItemTableFiller(CustomTableFiller):
    __model__ = Item
    __add_fields__ = {'codigo_tipo': None, #'tipo_item': None, 
                      'version_actual': None, 'estado': None,
                      'codigo_fase': None, 'complejidad': None}
    
    def codigo_tipo(self, obj, **kw):
        pass
    
    def version_actual(self, obj, **kw):
        pass
    
    def estado(self, obj, **kw):
        pass

    def codigo_fase(self, obj, **kw):
        pass
    
    def complejidad(self, obj, **kw):
        pass
        
    def __actions__(self, obj):
        """Links de acciones para un registro dado"""

        value = '<div>'
        clase = 'actions_fase'
        controller = "./items/" + str(obj.id_item)

        #si no está en la tabla que se encuentra en edit fase necesita 
        #solamente esta parte de la url
        if UrlParser.parse_nombre(request.url, "items"):
            controller =  str(obj.id_item)
            
        if PoseePermiso('modificar item', 
                        id_fase=obj.id_fase).is_met(request.environ):
            value += '<div>' + \
                        '<a href="./'+ controller +'/edit" ' + \
                        'class="' + clase + '">Modificar</a>' + \
                     '</div><br />'
            #adjuntos es el controlador de archivos adjuntos al item.
            value += '<div>' + \
                        '<a href="./'+ controller +'/adjuntos" ' + \
                        'class="' + clase + '">Adjuntos</a>' + \
                     '</div><br />'
            #versiones es el controlador de versiones del item.
            value += '<div>' + \
                        '<a href="./'+ controller +'/versiones" ' + \
                        'class="' + clase + '">Versiones</a>' + \
                     '</div><br />'
        
        p_item = PropiedadItem.por_id(obj.id_propiedad_item) #version actual.
        eliminar = False
        revivir = False
        aprobar = False
        desaprobar = False
        st = p_item.estado
        if st == "Desaprobado" or st == u"Revisión-Desbloq":
            eliminar = True
            aprobar = True
        elif st == "Aprobado":
            eliminar = True
            desaprobar = True
        elif st == "Eliminado":
            revivir = True

        if PoseePermiso('eliminar-revivir item',
                        id_fase=obj.id_fase).is_met(request.environ):
            if eliminar:
                value += '<div><form method="POST" action="' + controller + '" class="button-to">'+\
                         '<input type="hidden" name="_method" value="DELETE" />' +\
                         '<input onclick="return confirm(\'¿Está seguro?\');" value="Eliminar" type="submit" '+\
                         'style="background-color: transparent; float:left; border:0; color: #286571; display: inline;'+\
                         'margin: 0; padding: 0;' + clase + '"/>'+\
                         '</form></div><br />'
            elif revivir:
                value += '<div>' + \
                            '<a href="./'+ controller + '/revivir' +'" ' + \
                            'class="' + clase + '">Revivir</a>' + \
                         '</div><br />'
        if PoseePermiso('aprobar-desaprobar item'):
            if aprobar:
                value += '<div>' + \
                            '<a href="./'+ controller + '/aprobar' +'" ' + \
                            'class="' + clase + '">Aprobar</a>' + \
                         '</div><br />'
            elif desaprobar:
                value += '<div>' + \
                            '<a href="./'+ controller + '/desaprobar' +'" ' + \
                            'class="' + clase + '">Desaprobar</a>' + \
                         '</div><br />'

        value += '</div>'
        return value
    
    def _do_get_provider_count_and_objs(self, id_fase=None, **kw):
        """
        Recupera los ítems para los cuales tenemos algún permiso.
        Si el usuario se encuentra en una fase, retorna solo
        los ítems que pertenecen a dicha fase.
        """
        count, lista = super(ItemTableFiller, self).\
                            _do_get_provider_count_and_objs(**kw)
        filtrados = []                    
        if id_fase:
            id_fase = int(id_fase)
            ap = AlgunPermiso(tipo='Fase', id_fase=id_fase).is_met(request.environ)

            if ap:
                for it in lista:
                    if it.id_fase == id_fase:
                        filtrados.append(it)
                
            return len(filtrados), filtrados        
        
        for it in lista:
            if AlgunPermiso(tipo='Fase', id_fase=it.id_fase).is_met(request.environ):
                filtrados.append(it)
        
        return len(filtrados), filtrados


item_table_filler = ItemTableFiller(DBSession)


class TipoItemField(CustomPropertySingleSelectField):
    """
    Dropdown field para el tipo de ítem.
    """
    def _my_update_params(self, d, nullable=False):
        options = [(None, '----------')]
        id_fase = UrlParser.parse_id(request.url, "fases")
        if id_fase:
            fase = Fase.por_id(id_fase)
            for ti in fase.tipos_de_item:
                options.append((ti.id_tipo_item, '%s (%s)' % (ti.nombre, 
                                                              ti.codigo)))
        d["options"] = options
        return d


class ComplejidadPrioridadField(CustomPropertySingleSelectField):
    """
    Dropdown field para la complejidad y prioridad del ítem.
    """
    def _my_update_params(self, d, nullable=False):
        options = [(None, '----------')]
        for i in xrange(0, 11):
            options.append((i, str(i)))
        d["options"] = options
        return d


class ItemAddForm(AddRecordForm):
    __model__ = Item
    __omit_fields__ = ['id_item', 'numero', 'numero_por_tipo',
                       'id_propiedad_item', 'propiedad_item_versiones',
                       'codigo','id_fase']
    __add_fields__ = {"complejidad": None, "prioridad": None}
    id_tipo_item = TipoItemField("id_tipo_item", label_text=u"Tipo de Ítem")
    complejidad = ComplejidadPrioridadField("complejidad", 
                                            label_text="Complejidad")
    prioridad = ComplejidadPrioridadField("prioridad", 
                                            label_text="Prioridad")

item_add_form = ItemAddForm(DBSession)


class ItemEditForm(EditableForm):
    __model__ = Item
    __hide_fields__ = ['id_item', 'numero', 'numero_por_tipo', 'id_fase'
                       'id_propiedad_item', 'propiedad_item_versiones',
                       'codigo', 'id_tipo_item']
    __add_fields__ = {"complejidad": None, "prioridad": None}
    id_tipo_item = TipoItemField("id_tipo_item", label_text=u"Tipo de Ítem")
    complejidad = ComplejidadPrioridadField("complejidad", 
                                            label_text="Complejidad")
    prioridad = ComplejidadPrioridadField("prioridad", 
                                            label_text="Prioridad")

item_edit_form = ItemEditForm(DBSession)


class ItemEditFiller(EditFormFiller):
    __model__ = Item
    __add_fields__ = {"complejidad": None, "prioridad": None}
    
    def complejidad(self, obj, **kw):
        pass
    
    def prioridad(self, obj, **kw):
        pass

item_edit_filler = ItemEditFiller(DBSession)


#tabla para relacionar/eliminar relacion de ítem
class RelacionItemTable(RelacionTable):
    __headers__ = {'tipo': u'Tipo', 'codigo': u'Código',
                   'item_relacionado': u"Ítem Relacionado"}
    __add_fields__ = {'item_relacionado': None, 'check': None}
    __field_order__ = ['codigo', 'tipo', 'item_relacionado', 'check']
    __xml_fields__ = ['Check']

    
#filler para relacionar/eliminar relacion de ítem
class RelacionItemTableFiller(RelacionTableFiller):
    __add_fields__ = {'item_relacionado': None, 'check': None}
    
    def check(self, obj, **kw):
        checkbox = '<input type="checkbox" class="checkbox_tabla" id="' + str(obj.id_relacion) + '"/>'
        return checkbox
    
    def __actions__(self, obj):
        """Links de acciones para un registro dado"""

        value = '<div>'
        clase = 'actions_fase'
        id = str(obj.id_relacion)
        controller = "./relaciones/" + id
        id_item = UrlParser.parse_id(request.url, "items")
        item = Item.por_id(id_item)

        if PoseePermiso('modificar item', 
                        id_fase=item.id_fase).is_met(request.environ):
                        
            if UrlParser.parse_nombre(request.url, "relacionar_item"):
                #pagina relacionar item XXX
                value += '<div>' + \
                            '<a href="./relaciones/relacionar/' + id + '" ' + \
                            'class="' + clase + '">Relacionar</a>' + \
                         '</div><br />'
            else:
                value += '<div><form method="POST" action="' + controller + '" class="button-to">'+\
                         '<input type="hidden" name="_method" value="DELETE" />' +\
                         '<input onclick="return confirm(\'¿Está seguro?\');" value="Eliminar" type="submit" '+\
                         'style="background-color: transparent; float:left; border:0; color: #286571; display: inline;'+\
                         'margin: 0; padding: 0;' + clase + '"/>'+\
                         '</form></div><br />'
        
        value += '</div>'
        return value


class ItemController(CrudRestController):
    """Controlador de Items"""

    #{ Variables
    title = u"Administración de Ítems"
    allow_only = not_anonymous(u"El usuario debe haber iniciado sesión")
    
    #{plantillas
    tmp_action = "./"
    
    #{Subcontroladores
    adjuntos = AdjuntoController(DBSession)
    versiones = VersionController(DBSession)
    atributos = AtributoItemController(DBSession)
    relaciones = RelacionController(DBSession)
    
    #{ Modificadores
    model = Item
    table = item_table
    table_filler = item_table_filler     
    new_form = item_add_form
    edit_form = item_edit_form
    edit_filler = item_edit_filler
    
    opciones = dict(estado= u'Estado',
                    codigo= u'Código'
                    )
    columnas = dict(estado='combobox',
                    codigo='texto'
                    )
    comboboxes = dict(estado=Item.estados_posibles)
    
    #{ Métodos
    @with_trailing_slash
    @paginate('lista_elementos', items_per_page=5)
    @expose('lpm.templates.item.get_all')
    @expose('json')
    def get_all(self, *args, **kw):
        """ 
        Retorna todos los registros
        Retorna una página HTML si no se especifica JSON
        """
        puede_crear = False
        id_fase = UrlParser.parse_id(request.url, "fases")
        titulo = self.title
      
        if id_fase: 
            # desde el controlador de fases
            puede_crear = PoseePermiso("crear item", id_fase=id_fase).is_met(request.environ)
            fase = Fase.por_id(id_fase)
            titulo = u"Ítems de Fase: %s" % fase.nombre
        items = self.table_filler.get_value(id_fase=id_fase, **kw)
        tmpl_context.widget = self.table
        return dict(lista_elementos=items, 
                    page=titulo,
                    titulo=self.title, 
                    modelo=self.model.__name__, 
                    columnas=self.columnas,
                    opciones=self.opciones,
                    url_action=self.tmp_action,
                    puede_crear=puede_crear,
                    comboboxes=self.comboboxes
                    )
    
    @without_trailing_slash
    @paginate('lista_elementos', items_per_page=5)
    @expose('lpm.templates.item.get_all')
    @expose('json')
    def post_buscar(self, *args, **kw):
        """
        Controlador que recibe los parámetros de búsqueda para 
        devolver el resultado esperado.
        """
        puede_crear = False
        id_fase = UrlParser.parse_id(request.url, "fases")
        titulo = self.title
        if id_fase: 
            # desde el controlador de fases
            puede_crear = PoseePermiso("crear item", id_fase=id_fase).is_met(request.environ)
            fase = Fase.por_id(id_fase)
            titulo = u"Ítems de Fase: %s" % fase.nombre

        tmpl_context.widget = self.table
        buscar_table_filler = ItemTableFiller(DBSession)
        buscar_table_filler.filtros = kw
        items = buscar_table_filler.get_value(id_fase=id_fase)
        return dict(lista_elementos=items, 
                    page=self.title, 
                    titulo=self.title, 
                    modelo=self.model.__name__,
                    columnas=self.columnas,
                    url_action='../',
                    puede_crear=puede_crear,
                    comboboxes=self.comboboxes,
                    opciones=self.opciones,
                    atras='../'
                    )
    
    @expose()
    def get_one(self, *args, **kw):
        pass

    @without_trailing_slash
    @expose('lpm.templates.item.new')
    def new(self, *args, **kw):
        """Display a page to show a new record."""
        if not UrlParser.parse_nombre(request.url, "fases"):
            redirect("./")
        tmpl_context.widget = self.new_form
        return dict(value=kw,
                    page=u"Nuevo Ítem", 
                    atras='./')
    
    @expose()
    def post_delete(self, id):
        """Elimina una fase de la bd si el proyecto no está iniciado"""
        item = Item.por_id(id)
        #TODO
        if UrlParser.parse_nombre(request.url, "fases"):
            redirect('../')
        redirect('./')
        
        
    @validate(item_add_form, error_handler=new)
    @expose()
    def post(self, *args, **kw):
        if "sprox_id" in kw:
            del kw["sprox_id"]
        id_fase = UrlParser.parse_id(request.url, "fases")
        if id_fase:
            #TODO
            pass
        redirect("./")
    
    @expose('lpm.templates.item.edit')
    def edit(self, *args, **kw):
        """Despliega una pagina para realizar modificaciones"""
        
        id_fase = UrlParser.parse_id(request.url, "fases")
        puede_modificar = PoseePermiso('modificar item', 
                                       id_fase=id_fase).is_met(request.environ)
        if not puede_modificar:
            flash(pp.message % pp.nombre_permiso, 'warning')
            redirect("./")
        tmpl_context.widget = self.edit_form
        tmpl_context.tabla_atributos = self.atributos.table
        id_item = UrlParser.parse_id(request.url, "items")
        item = Item.por_id(id_item)
        atributos = self.atributos.table_filler \
                        .get_value(id_version=item.id_propiedad_item)
        
        tmpl_context.tabla_relaciones = RelacionItemTable(DBSession)
        rel_table_filler = RelacionItemTableFiller(DBSession)
        relaciones = rel_table_filler.get_value(id_version=item.id_propiedad_item)
        value = self.edit_filler.get_value(values={'id_item': id_item})
        return dict(value=value,
                    page=u"Modificar Ítem",
                    id=str(id_item),
                    puede_modificar=puede_modificar,
                    atributos=atributos,
                    relaciones=relaciones
                    )
        
    @validate(item_edit_form, error_handler=edit)
    @expose()
    def put(self, *args, **kw):
        """update"""
        if "sprox_id" in kw:
            del kw["sprox_id"]
        id_item = UrlParser.parse_id(request.url, "items")
        id_fase = UrlParser.parse_id(request.url, "fases")
        #TODO
        redirect("../")
    
    @expose('lpm.templates.item.relaciones')
    def relacionar_item(self, *args, **kw):
        #se lo llama desde la pagina edit del item, al hacer click en el
        #boton Relacionar
        tabla_item_fase_actual = None
        tabla_item_fase_anterior = None
        anteriores = {}
        actuales = {}
        pass
    
    @expose('lpm.templates.item.relaciones')
    def relacionar_seleccionados(self, *args, **kw):
        #recibe los elementos seleccionados en relacionar_item
        #relaciona, y retorna. Ajax
        pass

    
    @expose('lpm.templates.item.edit')
    def eliminar_relaciones(self, *args, **kw):
        #se lo llama desde la pagina de edit, al marcar las relaciones
        #y luego seleccionar Eliminar. Ajax.
        pass
    #}
