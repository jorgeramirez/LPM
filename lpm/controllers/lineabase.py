# -*- coding: utf-8 -*-
"""
Módulo que define el controlador de líneas bases.

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


class LineaBaseTable(TableBase):
    __model__ = LB
    __headers__ = { 'codigo': u'Código',
                    'estado': u'Estado',
                    'numero': u'Número'
                  }
    __omit_fields__ = ['id_lb', 'items', 'historial_lb']
    __default_column_width__ = '15em'
    __column_widths__ = { '__actions__': "50em"}
    __field_order__ = ["codigo", "estado", "numero"]
    
linea_base_table = LineaBaseTable(DBSession)


class LineaBaseTableFiller(CustomTableFiller):
    __model__ = LB
        
    def __actions__(self, obj):
        """Links de acciones para un registro dado"""

        value = '<div>'
        clase = 'actions_fase'
        controller = "./lbs/" #+ str(obj.id_lb)
        
        

        #si no está en la tabla que se encuentra en edit fase necesita 
        #solamente esta parte de la url
        if UrlParser.parse_nombre(request.url, "lbs"):
            #controller =  str(obj.id_lb)
            controller = u""
            
            if not obj.items:  #lb rota FIXME
                obj.estado = u'Rota'
                return '<div></div>'
            
            id_item = obj.items[0].propiedad_item.id_item_actual
            id_fase = Item.por_id(id_item).id_fase
        else:
            id_fase = UrlParser.parse_id(request.url, "fases")
        
        id = str(obj.id_lb)
        if PoseePermiso('abrir-cerrar lb', 
                         id_fase=id_fase).is_met(request.environ):
            if obj.estado in [u"Cerrada", u"Para-Revisión"]:
                value += '<div>' + \
                            '<a href="'+ controller +'abrir/' + id + '" ' + \
                            'class="' + clase + '">Abrir</a>' + \
                         '</div><br />'
            elif obj.estado == u"Abierta":
                value += '<div>' + \
                            '<a href="'+ controller +'post_cerrar/' + id + '" ' + \
                            'class="' + clase + '">Cerrar</a>' + \
                         '</div><br />'
            '''
            elif obj.estado == u"Cerrada":
                value += '<div>' + \
                            '<a href="'+ controller +'partir/' + id + '" ' + \
                            'class="' + clase + '">Partir</a>' + \
                         '</div><br />'
            '''
        value += '<div>' + \
                    '<a href="'+ controller +'examinar/' + id + '" ' + \
                    'class="' + clase + '">Examinar</a>' + \
                 '</div><br />'        
        value += "</div>"
        return value
        

    def _do_get_provider_count_and_objs(self, id_fase=None, **kw):
        """
        Recupera las lineas bases de una fase, o aquellas para las 
        que tenemos algún permiso.
        """
        count, lista = super(LineaBaseTableFiller, self).\
                            _do_get_provider_count_and_objs(**kw)
        filtrados = []                    
        if id_fase:
            id_fase = int(id_fase)
            ap = AlgunPermiso(tipo='Fase', id_fase=id_fase).is_met(request.environ)
            if ap:
                lbs = Fase.por_id(id_fase).lineas_bases()
                return len(lbs), lbs
        
        for lb in lista:

            if AlgunPermiso(tipo=u'Fase').is_met(request.environ):
                filtrados.append(lb)
        
        return len(filtrados), filtrados

linea_base_table_filler = LineaBaseTableFiller(DBSession)


#utilizado para desplegar los items que se podran
#seleccionar para generar la LB
class ItemGenerarTable(TableBase):
    __model__ = Item
    __headers__ = { 'codigo': u'Código',
                    'version': u'Versión',
                    'tipo': u'Tipo',
                    'check': u"Check"
                  }
    __add_fields__ = {'version': None, 'tipo': None, 'check':None}
    __omit_fields__ = ['id_item', 'numero', 'numero_por_tipo', 'id_tipo_item',
                       'id_propiedad_item', 'propiedad_item_versiones',
                       'id_fase']
    __xml_fields__ = ['Check']
    __default_column_width__ = '15em'
    __column_widths__ = { '__actions__': "50em"}
    __field_order__ = ["codigo", "version","tipo", "check"]

item_generar_table = ItemGenerarTable(DBSession)

class ItemGenerarTableFiller(CustomTableFiller):
    __model__ = Item
    __add_fields__ = {'version': None, 'tipo': None, 'check':None}
    
    def tipo(self, obj, **kw):
        ti = TipoItem.por_id(obj.id_tipo_item)
        return ti.codigo
    
    def version(self, obj, **kw):
        p_item = PropiedadItem.por_id(obj.id_propiedad_item)
        return p_item.version
    
    def check(self, obj, **kw):
        checkbox = '<input type="checkbox" class="checkbox_tabla" id="' + str(obj.id_item) + '"/>'
        return checkbox

    def __actions__(self, obj):
        """Links de acciones para un registro dado"""

        value = '<div>'
        clase = 'actions_fase'
        controller = "../items/%d/" % obj.id_item
        
        #id_fase = UrlParser.parse_id(request.url, "fases")
        
        #si está en la tabla que se encuentra en edit fase necesita 
        #if UrlParser.parse_nombre(request.url, "fases"):
        #    controller = u""
            #id_item = obj.items[0].propiedad_item.id_item_actual
        #    id_fase = Item.por_id(id_item).id_fase
        #else:
        #    id_fase = UrlParser.parse_id(request.url, "fases")
            
        value += '<div>' + \
                 '<a href="'+ controller +'" ' + \
                 'class="' + clase + '">Examinar</a>' + \
                 '</div><br />'

        value += '</div>'
        return value

    def _do_get_provider_count_and_objs(self, id_fase=None, items=None, **kw):
        """
        Recupera los items aprobados de la fase en cuestión
        """
        if items or items == []:
            return len(items), items
            
        id_fase = int(id_fase)             #falta probar.
        query = DBSession.query(Item).join(PropiedadItem) \
                         .filter(and_(Item.id_propiedad_item == \
                                      PropiedadItem.id_propiedad_item,
                                      and_(Item.id_fase == id_fase,
                                           PropiedadItem.estado == u"Aprobado")))
        return query.count(), query.all()

item_generar_table_filler = ItemGenerarTableFiller(DBSession)

##listado de items inhabilitados
class ItemInhabilitadosTable(TableBase):
    __model__ = PropiedadItem
    __headers__ = { 'codigo': u'Código',
                    'version': u'Versión',
                    'tipo': u'Tipo',
                    
                  }
    __add_fields__ = {'tipo': None, 'codigo': None}
    
    __omit_fields__ = ['id_propiedad_item', 'prioridad', 'descripcion', 'observaciones',
                       'id_item_actual', '__actions__', 'historial_item',
                        'item_lb_assocs', 'archivos', 'relaciones', 'atributos']
    __default_column_width__ = '15em'

    __field_order__ = ["codigo", "version","tipo"]
    

class ItemInhabilitadosTableFiller(CustomTableFiller):
    __model__ = PropiedadItem
    __add_fields__ = {'tipo': None, 'codigo': None}
    
    def tipo(self, obj, **kw):
        item = Item.por_id(obj.id_item_actual)
        ti = TipoItem.por_id(item.id_tipo_item)
        return ti.codigo

    def codigo(self, obj, **kw):
        return Item.por_id(obj.id_item_actual).codigo
               

    def _do_get_provider_count_and_objs(self, items=None, **kw):
        return len(items), items


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
    
    def _do_get_provider_count_and_objs(self, id_lb=None, **kw):
        """
        Recupera las versiones del ítem en cuestión.
        """
        count, lista = super(ItemLBTableFiller, self).\
                            _do_get_provider_count_and_objs(**kw)
        filtrados = []                    
        if id_lb:
            id_lb = int(id_lb)
            lb = LB.por_id(id_lb)
            for iplb in lb.items:
                if iplb in lista:
                    filtrados.append(iplb)
        return len(filtrados), filtrados


item_lb_table_filler = ItemLBTableFiller(DBSession)


class LineaBaseController(CrudRestController):
    """Controlador de LineaBases"""

    #{ Variables
    title = u"Administración de Líneas Base"
    allow_only = not_anonymous(u"El usuario debe haber iniciado sesión")
    
    #{plantillas
    tmp_action = "./"
    
    #{ Modificadores
    model = LB
    table = linea_base_table
    table_filler = linea_base_table_filler     
    
    opciones = dict(estado= u'Estado',
                    codigo= u'Código'
                    )
    columnas = dict(estado='combobox',
                    codigo='texto'
                    )
    comboboxes = dict(estado=LB.estados_posibles)
    
    #{ Métodos
    @with_trailing_slash
    @paginate('lista_elementos', items_per_page=5)
    @expose('lpm.templates.lb.get_all')
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
            puede_crear = PoseePermiso("crear lb", id_fase=id_fase).is_met(request.environ)
            fase = Fase.por_id(id_fase)
            if puede_crear:
                puede_crear = fase.puede_crear_lb()
            titulo = u"Líneas Base de Fase: %s" % fase.nombre
        lbs = self.table_filler.get_value(id_fase=id_fase, **kw)
        tmpl_context.widget = self.table
        return dict(lista_elementos=lbs, 
                    page=titulo,
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
            puede_crear = PoseePermiso("crear lb", id_fase=id_fase).is_met(request.environ)
            fase = Fase.por_id(id_fase)
            titulo = u"Líneas Base de Fase: %s" % fase.nombre

        tmpl_context.widget = self.table
        buscar_table_filler = LineaBaseTableFiller(DBSession)
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
    
    @expose()
    def get_one(self, *args, **kw):
        pass

    @without_trailing_slash
    @expose('lpm.templates.lb.new')
    def new(self, *args, **kw):
        """Pagina para generar una nueva linea base"""
        id_fase = UrlParser.parse_id(request.url, "fases")
        pp = PoseePermiso("crear lb", id_fase=id_fase)
        if not id_fase:
            flash("Se Debe especificar una fase", "warning")
            redirect("../")
        if not pp.is_met(request.environ):
            flash(pp.message % pp.nombre_permiso, 'warning')
            redirect("../")
        fase = Fase.por_id(id_fase)
        titulo = u"Generar LB para Fase: %s" % fase.nombre
        #TODO tabla de items aprobados de fase XXXX
        tmpl_context.tabla_items = item_generar_table
        items = item_generar_table_filler.get_value(id_fase=fase.id_fase)
        return dict(items=items,
                    page=titulo, 
                    atras='./')
    
    @expose()
    def post_delete(self, id_item):
        pass
        
    @expose()
    def post(self, *args, **kw):
        """
        Generamos la línea base.
        """
        #transaction.begin()
        id_fase = UrlParser.parse_id(request.url, "fases")
        pks = []
        for k, v in kw.items():
            if v.isalnum():
                pks.append(int(v))
        fase = Fase.por_id(id_fase)
        user = Usuario.by_user_name(request.credentials["repoze.what.userid"])
        fase.generar_lb(pks, user)
        if pks:
            flash(u"Se ha generado la línea base")
        else:
            flash(u"No existen ele")
        transaction.commit()
        #redirect("/fases/%d/edit" % id_fase)
        url = '/fases/%d/edit' % id_fase
        return url

    @expose()
    def abrir(self, *args, **kw):
        """
        Abre una LB
        """
        lb = LB.por_id(int(args[0]))
        user = Usuario.by_user_name(request.credentials["repoze.what.userid"])
        op = u"Desbloqueo"
        for iplb in lb.items:
            p_item = iplb.propiedad_item
            if p_item.estado == u"Bloqueado":
                p_item.estado = u"Aprobado"
            elif p_item.estado == u"Revisión-Bloq":
                p_item.estado = u"Revisión-Desbloq"
            HistorialItems.registrar(user, p_item, op)
        HistorialLB.registrar(user, lb, u"Apertura")
        id_fase = UrlParser.parse_id(request.url, "fases")
        url = "/lbs/"

        if not id_fase:
            id_item = lb.items[0].propiedad_item.id_item_actual
            id_fase = Item.por_id(id_item).id_fase
        else:
            url = "../"
        
        fase = Fase.por_id(id_fase)
        lb.estado = u"Abierta"
        fase.cambiar_estado()
        flash("Se ha abierto la LB")
        redirect(url)
        
    '''
    @expose("lpm.templates.lb.cerrar_habilitados")
    def cerrar_habilitados(self, id, hab=None, inh=None, *args, **kw):
        """
        No se pudo cerrar la linea base, por lo tanto se despliega la página
        donde se puede generar lb parcial.
        """
        id = id
        id_lb = int(id)
        lb = LB.por_id(id)
        page = u"Generar LB parcial a partir de : {codigo}".format(codigo=lb.codigo)
        tmpl_context.tabla_items_habilitados = ItemGenerarTable
        tmpl_context.tabla_items = ItemInhabilitadosTable(DBSession)
        inhabilitados = ItemInhabilitadosTable(DBSession).get_value(items=inh,\
                                                          **kw)
                                                       
        habilitados = item_generar_table_filler.get_value(items=hab, **kw)
        
        atras = "../"
            
        return dict(anteriores=anteriores, 
                    actuales=actuales,
                    page=page, 
                    id=id, 
                    atras=atras,
                    habilitados=habilitados,
                    inhabilitados=inhabilitados
                    )
    '''
    @expose("lpm.templates.lb.cerrar_habilitados")
    def post_cerrar(self, *args, **kw):
        """
        Cierra una LB. En caso de no poder cerrar, despliega la página
        de cerrar.
        """
        id = int(args[0])
        lb = LB.por_id(id)
        
        habilitados = []
        inhabilitados = []
        for ilb in lb.items:
            p_item = ilb.propiedad_item
            item = Item.por_id(p_item.id_item_actual)
            if (item.id_propiedad_item == p_item.id_propiedad_item and
                p_item.estado == u"Aprobado"):#no cambio o se aprobo
                habilitados.append(p_item)
            else:
                inhabilitados.append(p_item)
                
        if (inhabilitados == []):
            lb.estado = u"Cerrada"
            flash("Linea base cerrada correctamente")
            redirect('../')

        page = u"Generar LB parcial a partir de : {codigo}".format(codigo=lb.codigo)
        tmpl_context.tabla_items_habilitados = ItemGenerarTable(DBSession)
        tmpl_context.tabla_items = ItemInhabilitadosTable(DBSession)
        inhabilitados = ItemInhabilitadosTableFiller(DBSession).get_value(items=inhabilitados)
        
        lista = []
        for i in habilitados:
            lista.append(Item.por_id(i.id_item_actual))
        habilitados = item_generar_table_filler.get_value(items=lista, **kw)
        
        atras = "../"
        
        existen_habilitados = False
        if habilitados:
            existen_habilitados = True
        
        return dict(page=page, 
                    id=id, 
                    atras=atras,
                    habilitados=habilitados,
                    inhabilitados=inhabilitados,
                    existen_habilitados=existen_habilitados
                    )




                

    @expose()
    def partir(self, *args, **kw):
        pass
    
    @expose("lpm.templates.lb.edit")
    def edit(self, *args, **kw):
        pass
    
    @expose()
    def get_one(self, *args, **kw):
        pass

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
        iplbs = item_lb_table_filler.get_value(id_lb=id_lb, **kw)
        tmpl_context.widget = item_lb_table
        atras = "../../"
        if UrlParser.parse_nombre(request.url, "fases"):
            atras = "../../../edit" 
        return dict(lista_elementos=iplbs, 
                    page=titulo,
                    titulo=titulo, 
                    modelo="ItemsPorLB",
                    atras=atras
                    )
    #}
