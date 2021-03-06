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
                       PropiedadItem, Fase, Usuario)
from lpm.lib.sproxcustom import (CustomTableFiller,
                                 CustomPropertySingleSelectField)
from lpm.controllers.items_relacion import ItemRelacionController
from lpm.lib.authorization import PoseePermiso, AlgunPermiso
from lpm.lib.util import UrlParser

from sprox.tablebase import TableBase
from sprox.fillerbase import TableFiller, EditFormFiller
from sprox.fillerbase import EditFormFiller
from sprox.formbase import AddRecordForm, EditableForm

from tw.forms.fields import TextField

from repoze.what.predicates import not_anonymous

from sqlalchemy import and_, or_

import pylons
from pylons import tmpl_context

import transaction


class RelacionTable(TableBase):
    __model__ = Relacion
    __headers__ = {'tipo': u'Tipo', 'codigo': u'Código',
                   'item_relacionado': u"Ítem Relacionado",
                   'estado': u'Revision',
                   'item_relacionado_estado': u'Estado'}
    __add_fields__ = {'item_relacionado': None,
                      'estado': None,
                      'item_relacionado_estado': None}
    __omit_fields__ = ['id_relacion', 'id_anterior', 'id_posterior', '__actions__']
    __default_column_width__ = '15em'
    __column_widths__ = { '__actions__': "50em"}
    __field_order__ = ['codigo', 'tipo', 'item_relacionado', 'item_relacionado_estado']
    __xml_fields__ = ['Revision']
    
relacion_table = RelacionTable(DBSession)

class RelacionTableFiller(CustomTableFiller):
    __model__ = Relacion
    __add_fields__ = {'item_relacionado': None,
                      'estado': None,
                      'item_relacionado_estado': None}
    
    def item_relacionado(self, obj, **kw):
        id_item = UrlParser.parse_id(request.url, "items")
        id_version = UrlParser.parse_id(request.url, "versiones")
        if not id_item:
            id_item = id_version        
        otro = obj.obtener_otro_item(id_item)
        return otro.codigo
    
    def item_relacionado_estado(self, obj, **kw):
        id_item = UrlParser.parse_id(request.url, "items")
        id_version = UrlParser.parse_id(request.url, "versiones")
        if not id_item:
            id_item = id_version        
        otro = obj.obtener_otro_item(id_item)
        p_otro = PropiedadItem.por_id(otro.id_propiedad_item)
        return p_otro.estado
    
    def estado(self, obj, **kw):
        id_item = UrlParser.parse_id(request.url, "items")
        id_version = UrlParser.parse_id(request.url, "versiones")
        if not id_version:
            item = Item.por_id(id_item)
            rti = DBSession.query(RelacionPorItem).\
                                filter(and_(RelacionPorItem.id_propiedad_item\
                                == item.id_propiedad_item,\
                                RelacionPorItem.id_relacion == obj.id_relacion))\
                                .first()
        else:
            p_item = PropiedadItem.por_id(id_version)
            rti = DBSession.query(RelacionPorItem).\
                                filter(and_(RelacionPorItem.id_propiedad_item\
                                == p_item.id_propiedad_item,\
                                RelacionPorItem.id_relacion == obj.id_relacion))\
                                .first()
            
        color = u"inherit;"
        estado = u"No"
        
        if(rti.revisar):
            color = u"#ff0000;"
            estado = u'Sí'
            
        value = '<div style="color:' + color + '">' + estado + '</div>'
        
        return value
    
    def __actions__(self, obj):
        """Links de acciones para un registro dado"""

        if UrlParser.parse_nombre(request.url, "versiones"):
            #no se hace nada desde el controlador de versiones.
            return '<div></div>'

        value = '<div>'
        clase = 'actions_fase'
        id = str(obj.id_relacion)
        controller = "./" + id
        id_item = UrlParser.parse_id(request.url, "items")
        
        if id_item:
            item = Item.por_id(id_item)
            p_item = PropiedadItem.por_id(item.id_propiedad_item)

            otro = obj.obtener_otro_item(id_item)
            p_otro = PropiedadItem.por_id(otro.id_propiedad_item)
        
            if (p_item.estado not in [u"Bloqueado", u"Revisión-Bloq", u"Eliminado"] and\
                    obj.id_anterior != id_item or p_otro.estado == u"Eliminado"):
                    
                if (PoseePermiso('modificar item', 
                                id_fase=item.id_fase).is_met(request.environ) ):
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
        
        tipo = "a-s"
        if (UrlParser.parse_nombre(request.url, "relaciones_ph")):
            tipo = "p-h"
        
        filtrados = []                    
        if id_version:
            p_item = PropiedadItem.por_id(id_version)
            item = Item.por_id(p_item.id_item_actual)
            #ver este permiso
            ap = AlgunPermiso(tipo='Fase',
                              id_fase=item.id_fase).is_met(request.environ)
            if ap:
                
                for rpi in p_item.relaciones:
                    if (rpi.relacion in lista) and \
                        rpi.relacion.tipo == Relacion.tipo_relaciones[tipo]:
                        filtrados.append(rpi.relacion)
        
        return len(filtrados), filtrados


relacion_table_filler = RelacionTableFiller(DBSession)


#tabla para eliminar relacion de ítem
class RelacionItemTable(RelacionTable):
    __add_fields__ = {'item_relacionado': None,
                       'check': None, 'estado': None,
                      'item_relacionado_estado': None}
    __omit_fields__ = ['id_relacion', 'id_anterior', 'id_posterior']
    __headers__ = {'tipo': u'Tipo', 'codigo': u'Código',
                   'item_relacionado': u"Ítem Relacionado",
                   'estado': u'Revision', 'check': u"Check",
                   'item_relacionado_estado': u'Estado'}
    
    __field_order__ = [ 'codigo', 'item_relacionado', 'item_relacionado_estado', \
                       'tipo', "estado", "check"]
    __xml_fields__ = ['Check', 'Revision', '__actions__']
    
relacion_item_table = RelacionItemTable(DBSession)

#filler para relacionar/eliminar relacion de ítem
class RelacionItemTableFiller(RelacionTableFiller):
    __add_fields__ = {'item_relacionado': None, 'check': None,
                      'estado': None,
                      'item_relacionado_estado': None}
    
    
    
    def check(self, obj, **kw):
        bloq = ' '
        id_item = UrlParser.parse_id(request.url, "items")
        if id_item:
            item = Item.por_id(id_item)
            p_item = PropiedadItem.por_id(item.id_propiedad_item)
            otro = obj.obtener_otro_item(id_item)
            p_otro = PropiedadItem.por_id(otro.id_propiedad_item)
            
            if (p_item.estado in [u"Bloqueado", u"Revisión-Bloq", u"Eliminado"] or\
                obj.id_anterior == id_item and p_otro.estado != u"Eliminado"):
                bloq = ' disabled="" '
            #se permite eliminar desde el item anterior las relaciones colgadas    

           
        checkbox = '<input type="checkbox" class="checkbox_tabla"' + bloq + 'id="' + str(obj.id_relacion) + '"/>'
        
        return checkbox
        
relacion_item_table_filler = RelacionItemTableFiller(DBSession)
        
class RelacionController(CrudRestController):
    """Controlador de atributos de ítem"""

    #{ Variables
    title = u"Relaciones de Ítem"
    allow_only = not_anonymous(u"El usuario debe haber iniciado sesión")
    
    #{plantillas
    tmp_action = "./"
    
    #{subcontrolador
    relacionar_items = ItemRelacionController(DBSession)
    
    #{ Modificadores
    model = Relacion
    table = relacion_table
    table_filler = relacion_table_filler     

    
#    opciones = dict(codigo=u'Código')
#    columnas = dict(codigo='texto')
    
    #comboboxes = dict(tipo=Relacion.tipo_relaciones.values())
    
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
        relaciones = []
        tabla = self.table
        puede_relacionar = False
        puede_nueva = False
        atras = "../../"    
          
        if id_version:
            #desde controller de versiones
            p_item = PropiedadItem.por_id(id_version)
            titulo = u"Relaciones de Version: %d" % p_item.version
            relaciones = self.table_filler. \
                        get_value(id_version=id_version, **kw)
        elif id_item:
            #desde controller de items.
            item = Item.por_id(id_item)
            titulo = u"Relaciones de Ítem: %s" % item.codigo
            atras = "../"
            
            relaciones = relacion_item_table_filler. \
                        get_value(id_version=item.id_propiedad_item, **kw)
            tabla = relacion_item_table
            
            puede_relacionar = PoseePermiso('modificar item', \
                                id_tipo_item=item.id_tipo_item).is_met(request.environ)
            fase = Fase.por_id(item.id_fase)
            if (UrlParser.parse_nombre(request.url, "relaciones_as")):
                if (fase.posicion > 1):
                    puede_nueva = True
            else:
                puede_nueva = True
                
        tmpl_context.widget = tabla
        return dict(lista_elementos=relaciones, 
                    page=titulo,
                    titulo=titulo, 
                    modelo=self.model.__name__, 
                    #columnas=self.columnas,
                    #opciones=self.opciones,
                    #comboboxes=self.comboboxes,
                    url_action=self.tmp_action,
                    puede_relacionar=puede_relacionar,
                    atras=atras,
                    puede_nueva=puede_nueva
                    )
    
#    @without_trailing_slash
#    @paginate('lista_elementos', items_per_page=5)
#    @expose('lpm.templates.relacion.get_all')
#    @expose('json')
    @expose()
    def post_buscar(self, *args, **kw):
        """
        Controlador que recibe los parámetros de búsqueda para 
        devolver el resultado esperado.
        """
        pass
        '''
        id_item = UrlParser.parse_id(request.url, "items")
        id_version = UrlParser.parse_id(request.url, "versiones")
        titulo = self.title
        relaciones = []
        tabla = self.table
        puede_relacionar = False
        
        if id_version:
            #desde controller de versiones
            buscar_table_filler = RelacionTableFiller(DBSession)
            buscar_table_filler.filtros = kw
            p_item = PropiedadItem.por_id(id_version)
            titulo = u"Relaciones de Version: %d" % p_item.version
            relaciones = buscar_table_filler. \
                        get_value(id_version=p_item.id_propiedad_item)
        elif id_item:
            #desde controller de items.
            buscar_table_filler = RelacionItemTableFiller(DBSession)
            buscar_table_filler.filtros = kw
            tabla = relacion_item_table
            
            item = Item.por_id(id_item)
            titulo = u"Relaciones de Ítem: %s" % item.codigo
            relaciones = relacion_item_table_filler. \
                        get_value(id_version=item.id_propiedad_item, **kw)
            tabla = relacion_item_table
            puede_relacionar = PoseePermiso('modificar item', \
                                id_tipo_item=item.id_tipo_item).is_met(request.environ)

        tmpl_context.widget = tabla
        return dict(lista_elementos=relaciones,
                    page=titulo,
                    titulo=titulo,
                    modelo=self.model.__name__,
                    columnas=self.columnas,
                    url_action='../',
                    opciones=self.opciones,
                    #comboboxes=self.comboboxes,                    
                    atras='../',
                    puede_relacionar=puede_relacionar
                    )
        '''
    @expose()
    def post_delete(self, *args, **kw):
        #se lo llama desde la pagina de edit, al marcar las relaciones
        #y luego seleccionar Eliminar. Ajax.
        id_item = UrlParser.parse_id(request.url, "items")
        item = Item.por_id(id_item)
        
        p_item = PropiedadItem.por_id(item.id_propiedad_item)
        
        ids = []
        id = None
        if kw:
            for k, pk in kw.items():
                if not k.isalnum():
                    continue
                ids.append(int(pk))
        else:    
            try:
                id = int(args[0])
                if (id > 0):
                    ids.append(id)
            except:
                id = 0
                flash(u"Argumento invalido", "warning")
        
        p_item.eliminar_relaciones(ids)    
       
        usuario = Usuario.by_user_name(request.identity['repoze.who.userid'])
        item.guardar_historial(u"eliminar-relaciones", usuario)
        
        if (id):
            redirect("../")
        else:
            transaction.commit()   
            #return "/items/%d/edit" % id_item
            return './'
        
    @expose()
    def eliminar_relaciones(self, *args, **kw):
        #se lo llama desde la pagina de edit, al marcar las relaciones
        #y luego seleccionar Eliminar. Ajax.
        id_item = UrlParser.parse_id(request.url, "items")
        item = Item.por_id(id_item)
        
        p_item = PropiedadItem.por_id(item.id_propiedad_item)
        
        ids = []
        if kw:
            for k, pk in kw.items():
                if not k.isalnum():
                    continue
                ids.append(int(pk))
        
        p_item.eliminar_relaciones(ids)    
       
        usuario = Usuario.by_user_name(request.identity['repoze.who.userid'])
        item.guardar_historial(u"eliminar-relaciones", usuario)
        
        transaction.commit()   
        #return "/items/%d/edit" % id_item
        return './'
    
    @expose()
    def get_one(self, *args, **kw):
        pass

    @expose()
    def new(self, *args, **kw):
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
