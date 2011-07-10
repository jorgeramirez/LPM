# -*- coding: utf-8 -*-
"""
Módulo que define el controlador de ítems
a relacionar

@authors:
    - U{Carlos Bellino<mailto:carlosbellino@gmail.com>}
    - U{Nahuel Hernández<mailto:nahuel.11990@gmail.com>}
    - U{Jorge Ramírez<mailto:jorgeramirez1990@gmail.com>}

@since: 1.0
"""
from tgext.crud import CrudRestController
from tg.decorators import (paginate, expose, with_trailing_slash,
                           without_trailing_slash)
from tg import redirect, request, validate, flash, session, url

from lpm.model import DBSession, Item, TipoItem, Fase, PropiedadItem, Usuario, Relacion, Proyecto
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


class ItemRelacionTable(TableBase):
    __model__ = Item
    __headers__ = { 'codigo': u'Código',
                    'complejidad': 'Complejidad',
                    'codigo_tipo': u'Tipo de Ítem',
                    'version_actual': u'Versión Actual',
                    'estado': u'Estado',
                    'check': u'Check'
                  }
    __omit_fields__ = ['id_item', 'numero', 'numero_por_tipo',
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
        
    def __actions__(self, obj):
        controller = "relacionar_as"
        clase = "action"
        if (UrlParser.parse_nombre(request.url, "relaciones_ph")):
            controller = "relacionar_ph"
            
        if PoseePermiso('modificar item', 
                        id_tipo_item=obj.id_tipo_item).is_met(request.environ):
            value = '<div>' + \
                        '<a href="./' + controller + '/' + str(obj.id_item) +'" ' + \
                        'class="' + clase + '">Relacionar</a>' + \
                     '</div>'
        
        return value
   
    def _do_get_provider_count_and_objs(self, id_item=None, tipo=None, **kw):
        """
        Recupera los ítems para los cuales tenemos algún permiso. y está o no
        relacionado al campo relacionado.
        Si el usuario se encuentra en una fase, retorna solo
        los ítems que pertenecen a dicha fase.
        """
        #count, lista = super(ItemTableFiller, self).\
        #                   _do_get_provider_count_and_objs(**kw)
        filtrados = []                    
        if id_item:
            item = Item.por_id(int(id_item))
            
            if (tipo == 'P-H'):
                
                items_fase_actual = DBSession.query(Item)\
                .filter(and_(Item.id_propiedad_item == PropiedadItem.id_propiedad_item,\
                Item.id_item != item.id_item, Item.id_fase == item.id_fase,
                PropiedadItem.estado != u"Eliminado"))\
                .all()
                
                for it in items_fase_actual:
                    if (not it.esta_relacionado(id_item)):
                        filtrados.append(it)           
               
            if (tipo == 'A-S'):
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


class ItemRelacionController(CrudRestController):
    """Controlador de Items a Relacionar"""

    #{ Variables
    #TODO ACENTO EN RELACION
    title = u"Crear Relacion %s"
    allow_only = not_anonymous(u"El usuario debe haber iniciado sesión")
    
    #{plantillas
    tmp_action = "./"
    
    #{ Modificadores
    model = Item
    table = item_relacion_table
    table_filler = item_relacion_table_filler     
    
    #{ Métodos
    @with_trailing_slash
    @paginate('lista_elementos', items_per_page=5)
    @expose('lpm.templates.relacion.items')
    @expose('json')
    def get_all(self, *args, **kw):
        """ 
        Retorna todos los registros
        Retorna una página HTML si no se especifica JSON
        """
        id_item = UrlParser.parse_id(request.url, "items")
        item = Item.por_id(id_item)
        
        controller = "relacionar_as"
        tipo = "A-S"
        if (UrlParser.parse_nombre(request.url, "relaciones_ph")):
            controller = "relacionar_ph"
            tipo = "P-H"

        #TODO ACENTO EN RELACION
        page = u"Relacion {tipo} con ítem: {codigo}".format(tipo=tipo, codigo=item.codigo)
        tmpl_context.tabla_items = item_relacion_table
        items = item_relacion_table_filler.get_value(id_item=id_item,\
                                                          tipo=tipo, **kw)

        atras = "../"
            
        return dict(items=items, 
                    page=page,
                    title=self.title, 
                    controlador=controller, 
                    atras=atras
                    )
    @expose()
    def relacionar_as(self, *args, **kw):
        #recibe los elementos seleccionados en relacionar_item
        #relaciona, y retorna. Ajax
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
                flash(u"Argumento inválido", "warning")
            
        p_item.agregar_relaciones(ids, 'a-s')
        
        usuario = Usuario.by_user_name(request.identity['repoze.who.userid'])
        item.guardar_historial(u"relacionar-AS", usuario)
        
        mensaje = ""

        indice = session.get('indice_mensaje', 0)
        session['indice_mensaje'] = indice + 1
        session[str(indice)] = mensaje
           
        if (id):
            redirect('../mensajes/%d' % indice)
        else:
            transaction.commit()   
            #return "/items/%d/edit" % id_item
            return './mensajes/%d' % indice
        
    @expose()
    def relacionar_ph(self, *args, **kw):
        #recibe los elementos seleccionados en relacionar_item
        #relaciona, y retorna. Ajax
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
                flash(u"Argumento inválido", "warning")
        
        retorno, creado = p_item.agregar_relaciones(ids, 'p-h')
    
        if (creado):#si por lo menos se pudo crear una relacion se guarda en el 
                    #historial
            usuario = Usuario.by_user_name(request.identity['repoze.who.userid'])
            item.guardar_historial(u"relacionar-PH", usuario)
        
        mensaje = ""
        if (retorno == u"" and not creado):
            mensaje = u"No se crearon relaciones"
        elif (retorno != u""):
            mensaje = u"No se pudo crear la relación con %s" % retorno
            
        #no sé como pasar strings como parámetro, fea solución

        indice = session.get('indice_mensaje', 0)
        session['indice_mensaje'] = indice + 1
        session[str(indice)] = mensaje
           
        if (id):
            redirect('../mensajes/%d' % indice)
        else:
            transaction.commit()   
            #return "/items/%d/edit" % id_item
            return './mensajes/%d' % indice
        
    @expose()
    def mensajes(self, id):
        """ imprime un mensaje flash"""
        mensaje = session.get(id, "")
        if (mensaje == ""):
            flash(u"Relacionado exitósamente")
        else:
            flash(mensaje, "warning")
            
        redirect("../../")
    
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
