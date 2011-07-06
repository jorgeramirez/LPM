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

from lpm.model import DBSession, Item, TipoItem, Fase, PropiedadItem, Usuario, Relacion, Proyecto
from lpm.model.excepciones import *
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

from tw.forms.fields import TextField, TextArea

from repoze.what.predicates import not_anonymous

from sqlalchemy import and_, or_
import pylons
from pylons import tmpl_context

import transaction


class ItemTable(TableBase):
    __model__ = Item
    __headers__ = { 'codigo': u'Código',
                    'complejidad': u'Complejidad',
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
                       'id_fase', 'descripcion', 'observaciones']
    __default_column_width__ = '15em'
    __column_widths__ = { '__actions__': "50em"}
    __field_order__ = ["codigo", "version_actual", "complejidad", 
                       "codigo_tipo", "estado", "codigo_fase"]
    
item_table = ItemTable(DBSession)

class ItemRelacionTable(ItemTable):
    __headers__ = { 'codigo': u'Código',
                'version_actual': u'Versión Actual',
                'estado': u'Estado',
                'codigo_fase': u'Fase'
                    }
    __add_fields__ = {'codigo_tipo': None,
                      'version_actual': None, 'estado': None,
                      'check':None}
    __omit_fields__ = ['id_item', 'numero', 'numero_por_tipo', 'id_tipo_item',
                       'id_propiedad_item', 'propiedad_item_versiones',
                       'id_fase']
    __xml_fields__ = ['Check']
    __default_column_width__ = '15em'
    __column_widths__ = { '__actions__': "50em"}
    __field_order__ = ["codigo", "version_actual",
                       "estado", "check"]

 # item_relacion = ItemRelacionTable(DBSession)


class ItemTableFiller(CustomTableFiller):
    __model__ = Item
    __add_fields__ = {'codigo_tipo': None, #'tipo_item': None, 
                      'version_actual': None, 'estado': None,
                      'codigo_fase': None, 'complejidad': None}
    
    def codigo_tipo(self, obj, **kw):
        ti = TipoItem.por_id(obj.id_tipo_item)
        return ti.codigo
    
    def version_actual(self, obj, **kw):
        p_item = PropiedadItem.por_id(obj.id_propiedad_item)
        return p_item.version
    
    def estado(self, obj, **kw):
        p_item = PropiedadItem.por_id(obj.id_propiedad_item)
        return p_item.estado

    def codigo_fase(self, obj, **kw):
        fase = Fase.por_id(obj.id_fase)
        return fase.codigo
    
    def complejidad(self, obj, **kw):
        p_item = PropiedadItem.por_id(obj.id_propiedad_item)
        return p_item.complejidad
        
    def __actions__(self, obj):
        """Links de acciones para un registro dado"""

        value = '<div>'
        clase = 'actions_items'
        controller = "./" + str(obj.id_item)

        p_item = PropiedadItem.por_id(obj.id_propiedad_item) #version actual.    
        
        if PoseePermiso('modificar item', 
                        id_tipo_item=obj.id_tipo_item).is_met(request.environ):
            if p_item.estado not in [u"Bloqueado", u"Revisión-Bloq", "Eliminado"]:
                value += '<div>' + \
                            '<a href="'+ controller +'/edit" ' + \
                            'class="' + clase + '">Modificar</a>' + \
                         '</div><br />'
            #adjuntos es el controlador de archivos adjuntos al item.
            value += '<div>' + \
                        '<a href="'+ controller +'/adjuntos" ' + \
                        'class="' + clase + '">Adjuntos</a>' + \
                     '</div><br />'
            #versiones es el controlador de versiones del item.
            value += '<div>' + \
                        '<a href="'+ controller +'/versiones" ' + \
                        'class="' + clase + '">Versiones</a>' + \
                     '</div><br />'
        
        eliminar = False
        revivir = False
        aprobar = False
        desaprobar = False
        st = p_item.estado
        if st == u"Desaprobado" or st == u"Revisión-Desbloq":
            eliminar = True
            aprobar = True
        elif st == u"Aprobado":
            eliminar = True
            desaprobar = True
        elif st == u"Eliminado":
            revivir = True

        #if PoseePermiso('eliminar-revivir item',
        #                id_fase=obj.id_fase).is_met(request.environ):
        if PoseePermiso('eliminar-revivir item',
                        id_tipo_item=obj.id_tipo_item).is_met(request.environ):
            if eliminar:
                value += '<div><form method="POST" action="' + str(obj.id_item) + '" class="button-to">'+\
                         '<input type="hidden" name="_method" value="DELETE" />' +\
                         '<input onclick="return confirm(\'¿Está seguro?\');" value="Eliminar" type="submit" '+\
                         'style="background-color: transparent; float:left; border:0; color: #286571; display: inline;'+\
                         'margin: 0; padding: 0;' + clase + '"/>'+\
                         '</form></div><br />'

        controller = './'
            
        #if PoseePermiso('aprobar-desaprobar item', 
        #                id_fase=obj.id_fase).is_met(request.environ):
        if PoseePermiso('aprobar-desaprobar item', 
                        id_tipo_item=obj.id_tipo_item).is_met(request.environ):
            if aprobar:
                value += '<div>' + \
                            '<a href="' + controller + 'aprobar/' +str(obj.id_item) +'" ' + \
                            'style="margin-right:8px;" class="' + clase + '">Aprobar</a>' + \
                         '</div><br />'
            elif desaprobar:
                value += '<div>' + \
                            '<a href="' + controller + 'desaprobar/' +str(obj.id_item) +'" ' + \
                            'class="' + clase + '">Desaprobar</a>' + \
                         '</div><br />'
        #if PoseePermiso('calcular impacto', 
        #                id_fase=obj.id_fase).is_met(request.environ):
        if PoseePermiso('calcular impacto', 
                        id_tipo_item=obj.id_tipo_item).is_met(request.environ):
                value += '<div>' + \
                            '<a href="' + controller + 'calcular_impacto/' +str(obj.id_item) +'" ' + \
                            'class="' + clase + '">Calcular Impacto</a>' + \
                         '</div><br />'

        #if PoseePermiso('eliminar-revivir item', 
        #                id_fase=obj.id_fase).is_met(request.environ):
        if PoseePermiso('eliminar-revivir item', 
                        id_tipo_item=obj.id_tipo_item).is_met(request.environ):
            if revivir:
                value += '<div>' + \
                            '<a href="' + controller + 'revivir/' +str(obj.id_item) +'" ' + \
                            'class="' + clase + '">Revivir</a>' + \
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
            #if AlgunPermiso(tipo='Fase', id_fase=it.id_fase).is_met(request.environ):
            if AlgunPermiso(tipo=u'Tipo Ítem', 
                            id_tipo_item=it.id_tipo_item).is_met(request.environ):
                filtrados.append(it)
        
        return len(filtrados), filtrados

item_table_filler = ItemTableFiller(DBSession)

class ItemRelacionTable(TableBase):
    __model__ = Item
    __headers__ = { 'codigo': u'Código',
                    'complejidad': 'Complejidad',
                    'codigo_tipo': u'Tipo de Ítem',
                    'version_actual': u'Versión Actual',
                    'estado': u'Estado',
                    'check': u'Check'
                  }
    __omit_fields__ = ['__actions__', 'id_item', 'numero', 'numero_por_tipo',
                       'id_tipo_item',
                       'id_propiedad_item', 'propiedad_item_versiones',
                       'id_fase', 'descripcion', 'observaciones']
    __add_fields__ = {'codigo_tipo': None,
                      'version_actual': None, 'estado': None,
                      'complejidad': None,
                      'check': None}
    __xml_fields__ = ['Check']
    
    __default_column_width__ = '15em'
    __column_widths__ = { '__actions__': "50em"}
    __field_order__ = ["codigo", "version_actual", "complejidad", 
                       "codigo_tipo", "estado", "check"]
    
item_relacion_table = ItemRelacionTable(DBSession)

    
class ItemRelacionTableFiller(CustomTableFiller):
    __model__ = Item
    __add_fields__ = {'codigo_tipo': None,
                      'version_actual': None, 'estado': None,
                      'complejidad': None,
                      'check': None}
    
    def version_actual(self, obj, **kw):
        p_item = PropiedadItem.por_id(obj.id_propiedad_item)
        return p_item.version
    
    def estado(self, obj, **kw):
        p_item = PropiedadItem.por_id(obj.id_propiedad_item)
        return p_item.estado
    
    def codigo_tipo(self, obj, **kw):
        ti = TipoItem.por_id(obj.id_tipo_item)
        return ti.codigo
    
    def complejidad(self, obj, **kw):
        p_item = PropiedadItem.por_id(obj.id_propiedad_item)
        return p_item.complejidad
    
    def check(self, obj, **kw):
        #id
        checkbox = '<input type="checkbox" class="checkbox_tabla" id="' + str(obj.id_item) + '"/>'
        return checkbox
        
#    def __actions__(self, obj):
        
       
    def _do_get_provider_count_and_objs(self, id_item=None, tipo=None, **kw):
        """
        Recupera los ítems para los cuales tenemos algún permiso. y está o no
        relacionado al campo realcionado.
        Si el usuario se encuentra en una fase, retorna solo
        los ítems que pertenecen a dicha fase.
        """
#        count, lista = super(ItemTableFiller, self).\
#                            _do_get_provider_count_and_objs(**kw)
        filtrados = []                    
        if id_item:
            item = Item.por_id(int(id_item))
            
            if (tipo == 'p-h'):
                
                items_fase_actual = DBSession.query(Item)\
                .filter(and_(Item.id_propiedad_item == PropiedadItem.id_propiedad_item,\
                Item.id_item != item.id_item, Item.id_fase == item.id_fase,
                PropiedadItem.estado != u"Eliminado"))\
                .all()
                
                for it in items_fase_actual:
                    if (not it.esta_relacionado(id_item)):
                        filtrados.append(it)           
               
            if (tipo == 'a-s'):
                fase = Fase.por_id(item.id_fase)
                items_fase_anterior = DBSession.query(Item)\
                .filter(and_(Item.id_propiedad_item == PropiedadItem.id_propiedad_item,\
                Item.id_fase == Fase.id_fase, Fase.id_proyecto == fase.id_proyecto, PropiedadItem.estado == u"Bloqueado", \
                    Fase.posicion == fase.posicion - 1, fase.posicion != 1))\
                .all()
                
                
                for it in items_fase_anterior:
                    if (not it.esta_relacionado(id_item)):
                        filtrados.append(it)
                        
                
        return len(filtrados), filtrados

item_relacion_table_filler = ItemRelacionTableFiller(DBSession)


class TipoItemField(CustomPropertySingleSelectField):
    """
    Dropdown field para el tipo de ítem.
    """
    def _my_update_params(self, d, nullable=False):
        options = []
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
        options = [(5,5)]
        for i in xrange(1, 11):
            if i == 5: 
                continue
            options.append((i, str(i)))
        d["options"] = options
        return d


class ItemAddForm(AddRecordForm):
    __model__ = Item
    __omit_fields__ = ['id_item', 'numero', 'numero_por_tipo',
                       'id_propiedad_item', 'propiedad_item_versiones',
                       'codigo','id_fase']
    __add_fields__ = {"complejidad": None, "prioridad": None,
                      "descripcion": None, "observaciones": None}
    __field_order__ = ['id_tipo_item', 'complejidad', 'prioridad',
                       'descripcion', 'observaciones']
    id_tipo_item = TipoItemField("id_tipo_item", label_text=u"Tipo de Ítem")
    complejidad = ComplejidadPrioridadField("complejidad", 
                                            label_text="Complejidad")
    prioridad = ComplejidadPrioridadField("prioridad", 
                                            label_text="Prioridad")
    descripcion = TextArea("descripcion", label_text=u"Descripción")
    observaciones = TextArea("observaciones", label_text=u"Observaciones")


item_add_form = ItemAddForm(DBSession)


class ItemEditForm(EditableForm):
    __model__ = Item
    __hide_fields__ = ['id_item', 'codigo', 'numero', 'numero_por_tipo', 
                       'id_tipo_item', 'id_fase', 'id_propiedad_item', 
                       'propiedad_item_versiones']
    __add_fields__ = {"complejidad": None, "prioridad": None,
                      "descripcion": None, "observaciones": None}
    __field_order__ = ['complejidad', 'prioridad',
                       'descripcion', 'observaciones']
    complejidad = ComplejidadPrioridadField("complejidad", 
                                            label_text="Complejidad")
    prioridad = ComplejidadPrioridadField("prioridad", 
                                            label_text="Prioridad")
    descripcion = TextArea("descripcion", label_text=u"Descripción")
    observaciones = TextArea("observaciones", label_text=u"Observaciones")

item_edit_form = ItemEditForm(DBSession)


class ItemEditFiller(EditFormFiller):
    __model__ = Item
    __add_fields__ = {"complejidad": None, "prioridad": None,
                      "descripcion": None, "observaciones": None}

    def complejidad(self, obj, **kw):
        p_item = PropiedadItem.por_id(obj.id_propiedad_item)
        return p_item.complejidad
    
    def prioridad(self, obj, **kw):
        p_item = PropiedadItem.por_id(obj.id_propiedad_item)
        return p_item.prioridad

    def descripcion(self, obj, **kw):
        p_item = PropiedadItem.por_id(obj.id_propiedad_item)
        return p_item.descripcion

    def observaciones(self, obj, **kw):
        p_item = PropiedadItem.por_id(obj.id_propiedad_item)
        return p_item.observaciones
        
item_edit_filler = ItemEditFiller(DBSession)


#tabla para eliminar relacion de ítem
class RelacionItemTable(RelacionTable):
    __add_fields__ = {'item_relacionado': None,
                       'check': None, 'estado': None}
    __omit_fields__ = ['id_relacion', 'id_anterior', 'id_posterior',
                       '__actions__']
    __headers__ = {'tipo': u'Tipo', 'codigo': u'Código',
                   'item_relacionado': u"Ítem Relacionado",
                   'estado': u'Estado', 'check': u"Check"}
    
    __field_order__ = ["codigo", 'item_relacionado', 'tipo', "estado", "check"]
    __xml_fields__ = ['Check', 'Estado']
    
    
#filler para relacionar/eliminar relacion de ítem
class RelacionItemTableFiller(RelacionTableFiller):
    __add_fields__ = {'item_relacionado': None, 'check': None,
                      'estado': None}
    
    def check(self, obj, **kw):
        checkbox = '<input type="checkbox" class="checkbox_tabla" id="' + str(obj.id_relacion) + '"/>'
        return checkbox



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
        atras = "/items/"
        if id_fase: 
            # desde el controlador de fases
            puede_crear = PoseePermiso("crear item", id_fase=id_fase).is_met(request.environ)
            atras = "/fases/%d/edit/" % id_fase
            fase = Fase.por_id(id_fase)
            if puede_crear:
                puede_crear = fase.puede_crear_item()
            titulo = u"Ítems de Fase: %s" % fase.nombre
        items = self.table_filler.get_value(id_fase=id_fase, **kw)
        tmpl_context.widget = self.table
        return dict(lista_elementos=items, 
                    page=titulo,
                    atras=atras,
                    titulo=titulo, 
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
            puede_crear = PoseePermiso("crear item", 
                                       id_fase=id_fase).is_met(request.environ)
            fase = Fase.por_id(id_fase)
            if puede_crear:
                puede_crear = fase.puede_crear_item()
            titulo = u"Ítems de Fase: %s" % fase.nombre

        tmpl_context.widget = self.table
        buscar_table_filler = ItemTableFiller(DBSession)
        buscar_table_filler.filtros = kw
        items = buscar_table_filler.get_value(id_fase=id_fase)
        return dict(lista_elementos=items, 
                    page=titulo, 
                    titulo=titulo, 
                    modelo=self.model.__name__,
                    columnas=self.columnas,
                    url_action='../',
                    puede_crear=puede_crear,
                    comboboxes=self.comboboxes,
                    opciones=self.opciones,
                    atras='../'
                    )
    
    @expose("lpm.templates.item.get_one")
    def get_one(self, *args, **kw):
        #id_fase = UrlParser.parse_id(request.url, "fases")
        id_item = UrlParser.parse_id(request.url, "items")
        atras = "./"
        #if UrlParser.parse_nombre(request.url, "fases"):
        #    atras = "../../edit"
        item = Item.por_id(id_item)
        
        class get_one_edit_form(ItemEditForm):
            prioridad = TextField("prioridad")
            complejidad = TextField("complejidad")
        
        
        tmpl_context.widget = get_one_edit_form(DBSession)
        tmpl_context.tabla_atributos = self.atributos.table
        atributos = self.atributos.table_filler \
                        .get_value(id_version=item.id_propiedad_item)
        
        tmpl_context.tabla_relaciones = RelacionItemTable(DBSession)
        rel_table_filler = RelacionItemTableFiller(DBSession)
        relaciones = rel_table_filler.get_value(id_version=item.id_propiedad_item)
        value = self.edit_filler.get_value(values={'id_item': id_item})
        page = u"Ítem: %s" % value["codigo"]

        return dict(value=value,
                    page=page,
                    id=str(id_item),
                    atributos=atributos,
                    relaciones=relaciones,
                    atras=atras
                    )

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
    def post_delete(self, id_item):
        """Elimina un item"""
        item = Item.por_id(int(id_item))
        user = Usuario.by_user_name(request.credentials["repoze.what.userid"])
        try:
            item.eliminar(user)
            flash(u"Ítem Eliminado")
        except EliminarItemError, err:
            flash(unicode(err), 'warning')
        redirect("./")
        
    @validate(item_add_form, error_handler=new)
    @expose()
    def post(self, *args, **kw):
        if "sprox_id" in kw:
            del kw["sprox_id"]
        id_fase = UrlParser.parse_id(request.url, "fases")
        id_tipo = int(kw["id_tipo_item"])
        user = Usuario.by_user_name(request.credentials["repoze.what.userid"])
        del kw["id_tipo_item"]
        if id_fase:
            fase = Fase.por_id(id_fase)
            fase.crear_item(id_tipo, user, **kw)
        redirect("./")
    
    @expose('lpm.templates.item.edit')
    def edit(self, *args, **kw):
        """Despliega una pagina para realizar modificaciones"""
        
        #id_fase = UrlParser.parse_id(request.url, "fases")
        id_item = UrlParser.parse_id(request.url, "items")
        atras = "../"
        if UrlParser.parse_nombre(request.url, "fases"):
            atras = "../../edit"
        item = Item.por_id(id_item)
        puede_modificar = PoseePermiso('modificar item', 
                                       id_fase=item.id_fase).is_met(request.environ)
        if not puede_modificar:
            flash(pp.message % pp.nombre_permiso, 'warning')
            redirect("./")
        tmpl_context.widget = self.edit_form
        tmpl_context.tabla_atributos = self.atributos.table
        atributos = self.atributos.table_filler \
                        .get_value(id_version=item.id_propiedad_item)
        
        tmpl_context.tabla_relaciones = RelacionItemTable(DBSession)
        rel_table_filler = RelacionItemTableFiller(DBSession)
        relaciones = rel_table_filler.get_value(id_version=item.id_propiedad_item)
        value = self.edit_filler.get_value(values={'id_item': id_item})
        page = u"Modificar Ítem: %s" % value["codigo"]

        return dict(value=value,
                    page=page,
                    id=str(id_item),
                    puede_relacionar=puede_modificar,
                    atributos=atributos,
                    relaciones=relaciones,
                    atras=atras
                    )
        
    @validate(item_edit_form, error_handler=edit)
    @expose()
    def put(self, *args, **kw):
        """
        Actualiza un item. Específicamente su prioridad, complejidad, 
        observaciones o descripcion.
        """
        if "sprox_id" in kw:
            del kw["sprox_id"]
        kw["complejidad"] = int(kw["complejidad"])
        kw["prioridad"] = int(kw["prioridad"])
        atras = "../"
        id_item = UrlParser.parse_id(request.url, "items")
        if UrlParser.parse_nombre(request.url, "fases"):
            atras = "../../edit"
        item = Item.por_id(id_item)
        user_name = request.credentials["repoze.what.userid"]
        user = Usuario.by_user_name(user_name)
        try:
            item.modificar(user, **kw)
        except ModificarItemError, err:
            flash(unicode(err), "warning")

        redirect(atras)
        
    
    @expose('lpm.templates.item.relaciones')
    def relacionar_item(self, *args, **kw):
        #se lo llama desde la pagina edit del item, al hacer click en el
        #boton Relacionar
        id = args[0]
        id_item = int(id)
        item = Item.por_id(id_item)
        page = u"Relacionar con ítem: {codigo}".format(codigo=item.codigo)
        tmpl_context.tabla_item_fase_actual = item_relacion_table
        tmpl_context.tabla_item_fase_anterior = item_relacion_table
        anteriores = item_relacion_table_filler.get_value(id_item=id_item,\
                                                          tipo='a-s', **kw)
                                                        
        actuales = item_relacion_table_filler.get_value(id_item=id_item,\
                                                          tipo='p-h', **kw)
        atras = "../%d/edit" % id_item
            
        return dict(anteriores=anteriores, 
                    actuales=actuales,
                    page=page, 
                    id=id, 
                    atras=atras,
                    )
    
    @expose()
    def relacionar_as(self, *args, **kw):
        #recibe los elementos seleccionados en relacionar_item
        #relaciona, y retorna. Ajax
        id = args[0]
        id_item = int(id)
        item = Item.por_id(id_item)
        p_item = PropiedadItem.por_id(item.id_propiedad_item)
        
        if kw:
            ids = []
            for k, pk in kw.items():
                if not k.isalnum():
                    continue
                ids.append(int(pk))
        
        p_item.agregar_relaciones(ids, 'a-s')
        
        usuario = Usuario.by_user_name(request.identity['repoze.who.userid'])
        item.guardar_historial(u"relacionar-AS", usuario)
        transaction.commit()    
        #return "/items/%d/edit" % id_item
        return '../'
        
    @expose()
    def relacionar_ph(self, *args, **kw):
        #recibe los elementos seleccionados en relacionar_item
        #relaciona, y retorna. Ajax
        id = args[0]
        id_item = int(id)
        item = Item.por_id(id_item)
        p_item = PropiedadItem.por_id(item.id_propiedad_item)
        
        if kw:
            ids = []
            for k, pk in kw.items():
                if not k.isalnum():
                    continue
                ids.append(int(pk))
        
            retorno, creado = p_item.agregar_relaciones(ids, 'p-h')
        
            if (creado):#si por lo menos se pudo crear una relacion se guarda en el 
                        #historial
                usuario = Usuario.by_user_name(request.identity['repoze.who.userid'])
                item.guardar_historial(u"relacionar-PH", usuario)
        
            
            if (retorno == u"" and creado):
                flash("Relacionado exiosamente") 
            elif (retorno != u""):
                mensaje = u"No se pudo crear la relación con %s" % retorno
                flash(retorno, "warning")

            transaction.commit()    
            #return "/items/%d/edit" % id_item
        return '../'
    
    @expose()
    def eliminar_relaciones(self, *args, **kw):
        #se lo llama desde la pagina de edit, al marcar las relaciones
        #y luego seleccionar Eliminar. Ajax.
        id = args[0]
        id_item = int(id)
        item = Item.por_id(id_item)
        p_item = PropiedadItem.por_id(item.id_propiedad_item)
        print kw
        if kw:
            ids = []
            for k, pk in kw.items():
                if not k.isalnum():
                    continue
                ids.append(int(pk))

            p_item.eliminar_relaciones(ids)
            
            usuario = Usuario.by_user_name(request.identity['repoze.who.userid'])
            item.guardar_historial(u"eliminar-relaciones", usuario)
        transaction.commit()
        return '../%s/edit' % id

    
    @expose('lpm.templates.item.impacto')
    def calcular_impacto(self, *args, **kw):
        """Calcula el impacto"""
        id = args[0]
        id_item = int(id)
        item = Item.por_id(id_item)
        page = "Calculo de impacto de item: %s" % item.codigo
        atras = "../"
        if UrlParser.parse_nombre(request.url, "fases"):
            atras = "../%s/edit" % id
            
        item = Item.por_id(id_item)
        sumatoria, grafo = item.calcular_impacto()
        id_proyecto = UrlParser.parse_id(request.url, "proyectos")
        
        fase = Fase.por_id(item.id_fase)
        proy = Proyecto.por_id(fase.id_proyecto)
        impacto = (float(sumatoria)/float(proy.complejidad_total)) * 100

        return dict(atras=atras,
                    impacto=str(impacto),
                    page=page,
                    filas=filas,
                    ct=str(proy.complejidad_total),
                    suma=str(sumatoria),
                    grafo=grafo
                    )
    
    @expose()
    def revivir(self, *args, **kw):
        """
        Revive un ítem que se encuentra en estado eliminado.
        """
        item = Item.por_id(int(args[0]))
        user = Usuario.by_user_name(request.credentials["repoze.what.userid"])
        try:
            item.revivir(user)
            flash(u"Ítem Revivido")
        except RevivirItemError, err:
            flash(unicode(err), 'warning')
        redirect("../")
        
    @expose()
    def aprobar(self, *args, **kw):
        """
        Aprueba un ítem.
        """
        item = Item.por_id(int(args[0]))
        user = Usuario.by_user_name(request.credentials["repoze.what.userid"])
        try:
            item.aprobar(user)
            flash(u"Ítem Aprobado")
        except CondicionAprobarError, err:
            flash(unicode(err), 'warning')
        redirect("../")
        
    @expose()
    def desaprobar(self, *args, **kw):
        """
        Desaprueba un ítem.
        """
        user = Usuario.by_user_name(request.credentials["repoze.what.userid"])
        item = Item.por_id(int(args[0]))
        try:
            item.desaprobar(user)
            flash(u"Ítem Desaprobado")
        except DesAprobarItemError, err:
            flash(unicode(err), 'warning')
        redirect("../")
    #}
