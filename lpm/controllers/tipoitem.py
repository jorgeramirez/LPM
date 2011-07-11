# -*- coding: utf-8 -*-
"""
Módulo que define el controlador de tipos de ítem.

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
from lpm.controllers.atributotipoitem import (AtributosPorTipoItemController)
from lpm.controllers.miembros_tipo_item import MiembrosTipoController
from lpm.controllers.no_miembros_tipo_item import NoMiembrosTipoController
from lpm.controllers.roles_tipo_item import RolesTipoController

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


class TipoItemTable(TableBase):
    __model__ = TipoItem
    __headers__ = {'codigo' : u'Código',
                   'proyecto' : u"Proyecto"
                  }
    __omit_fields__ = ['id_tipo_item', 'id_proyecto', 'id_padre',
                       'hijos', 'atributos', 'items', 'descripcion',
                       'roles', 'id_fase']
    __default_column_width__ = '15em'
    __column_widths__ = {'codigo': "35em",
                         '__actions__' : "50em"
                        }
    
tipo_item_table = TipoItemTable(DBSession)


class TipoItemTableFiller(CustomTableFiller):
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
        
        if UrlParser.parse_nombre(request.url, "post_buscar"):
            url_cont = "../" + str(obj.id_tipo_item)
        
        pp = PoseePermiso('redefinir tipo item', 
                          id_tipo_item=obj.id_tipo_item)
        
            
        #if PoseePermiso('redefinir tipo item').is_met(request.environ):
        if pp.is_met(request.environ):
            value += '<div>' + \
                        '<a href="' + url_cont + '/edit" ' + \
                        'class="' + clase + '">Modificar</a>' + \
                     '</div><br />'

            value += '<div>' + \
                        '<a href="' + url_cont + '/atributostipoitem/" ' + \
                        'class="' + clase + '">Atributos</a>' + \
                     '</div><br />'

            value += '<div>' + \
                        '<a href="'+ url_cont + '/miembrostipo" ' + \
                        'class="' + clase + '">Usuarios</a>' + \
                     '</div><br />'

            '''
            value += '<div>' + \
                        '<a href="'+ url_cont + '/nomiembrostipo" ' + \
                        'class="' + clase + '">No miembros</a>' + \
                     '</div><br />'
            '''
            
            value += '<div>' + \
                        '<a href="'+ url_cont + '/rolestipo" ' + \
                        'class="' + clase + '">Roles de Tipo</a>' + \
                     '</div><br />'

        if obj.puede_eliminarse():
            if pp.is_met(request.environ):
                value += '<div><form method="POST" action="' + str(obj.id_tipo_item) + '" class="button-to">'+\
                         '<input type="hidden" name="_method" value="DELETE" />' +\
                         '<input onclick="return confirm(\'Está seguro?\');" value="Eliminar" type="submit" '+\
                         'style="background-color: transparent; float:left; border:0; color: #286571;'+\
                         'display: inline; margin: 0; padding: 0; margin-left:-3px;" class="' + clase + '"/>'+\
                         '</form></div><br />'
        
        
        value += '</div>'
        return value
    
    def _do_get_provider_count_and_objs(self, id_fase=None, id_tipo=None, **kw):
        """
        Se muestra la lista de tipos de item para la fase en cuestión
        """
        if id_tipo:
            ti = TipoItem.por_id(id_tipo)
            return 1, [ti]
            
        count, lista = super(TipoItemTableFiller, self).\
                            _do_get_provider_count_and_objs(**kw)
        filtrados = []                    
        
        if id_fase:
            id_fase = int(id_fase)
            for t in lista:
                if t.id_fase == id_fase:
                    if AlgunPermiso(tipo='Tipo', 
                       id_tipo_item=t.id_tipo_item).is_met(request.environ):
                        filtrados.append(t)
                
        return len(filtrados), filtrados        


tipo_item_table_filler = TipoItemTableFiller(DBSession)


class TipoPadreField(PropertySingleSelectField):
    """Dropdown list para el tipo padre de un tipo de item"""
    def _my_update_params(self, d, nullable=False):
        options = []
        
        id_proyecto = UrlParser.parse_id(request.url, "proyectos")
        id_fase = UrlParser.parse_id(request.url, "fases")
        if not id_proyecto:
            id_proyecto = UrlParser.parse_id(request.url, "proyectos_fase")
            if not id_proyecto:
                id_proyecto = UrlParser.parse_id(request.url, "proyectos_fase_ti")
                id_fase = UrlParser.parse_id(request.url, "fases_ti")
            
        if (self.accion == "new"):
            if id_fase:
                tipos = Fase.por_id(id_fase).tipos_de_item
                
            #elif (id_proyecto):
            #    tipos = Proyecto.por_id(id_proyecto).tipos_de_item
                
            for ti in tipos:
                options.append((ti.id_tipo_item, '%s (%s)' % (ti.nombre, 
                                                              ti.codigo)))
        if (self.accion == "edit"):
            id_tipo = UrlParser.parse_id(request.url, "tipositems")
            ti = TipoItem.por_id(id_tipo)
            padre = TipoItem.por_id(ti.id_padre)
            if padre:
                options.append((ti.id_padre, '%s (%s)' % (padre.nombre, 
                                                          padre.codigo)))
            else:
                options.append((ti.id_padre, 'Tipo base'))
        d['options'] = options
        return d

class TipoImportadoField(PropertySingleSelectField):
    """Dropdown list para la lista de tipos a importar"""
    
    def _my_update_params(self, d, nullable=False):
        options = []
        options.append((None, '-----------------'))

        #Solo tipos de otros proyectos
        
        id_proyecto = UrlParser.parse_id(request.url, "proyectos")
        id_fase = UrlParser.parse_id(request.url, "fases")
        if not id_proyecto:
            id_proyecto = UrlParser.parse_id(request.url, "proyectos_fase")
            if not id_proyecto:
                id_proyecto = UrlParser.parse_id(request.url, "proyectos_fase_ti")
                id_fase = UrlParser.parse_id(request.url, "fases_ti")
                
        if (self.accion == "new"):
            #de otros proyectos.
            if id_proyecto:
                tipos_items = DBSession.query(TipoItem) \
                                       .filter(TipoItem.id_proyecto != id_proyecto) \
                                       .all()
            
            for ti in tipos_items:
                options.append((ti.id_tipo_item, '%s (%s)' % (ti.nombre, 
                                                              ti.codigo)))
            
            #importa de otras fases tambien
            if id_fase:
                fase = Fase.por_id(id_fase)
                id_proyecto = fase.id_proyecto
                tipos_items_fase = DBSession.query(TipoItem) \
                            .filter(and_(TipoItem.id_proyecto == id_proyecto,
                                         TipoItem.id_fase != id_fase)) \
                                         .all()
                '''
                tipos_items_fase = DBSession.query(TipoItem) \
                            .filter(or_(TipoItem.id_proyecto != id_proyecto,
                            and_(TipoItem.id_proyecto == id_proyecto,
                            TipoItem.id_fase != id_fase))) \
                                       .all()
                '''

                for ti in tipos_items_fase:
                    #solo si posee algun permiso sobre el tipo de item
                    #if (AlgunPermiso(tipo="Tipo", id_tipo_item=ti.id_tipo_item)):
                    options.append((ti.id_tipo_item, '%s (%s)' % (ti.nombre, 
                                                                  ti.codigo)))

        d['options'] = options
        return d
  

class TipoItemAddForm(AddRecordForm):
    __model__ = TipoItem
    __omit_fields__ = ['id_tipo_item', 'id_proyecto', 'codigo',
                       'hijos', 'atributos', 'items', 'roles', 'id_fase']
    __check_if_unique__ = True
    __field_order__ = ['nombre', 'siglas', 'descripcion', 'id_padre', 
                       'id_importado', 'mezclar']
    __field_attrs__ = {'descripcion' : {'row': '1'},
                       'nombre': { 'maxlength' : '50'}
                       
                      }
    __add_fields__ = {"siglas": None}
    __require_fields__ = ['nombre', 'id_padre']
    siglas = TextField("siglas", label_text="Siglas")
    id_padre = TipoPadreField("id_padre", accion="new", label_text="Tipo Padre")
    id_importado = TipoImportadoField("id_importado", accion="new", label_text="Importar De")
    descripcion = TextArea
    mezclar = CheckBox("mezclar", label_text="Mezclar Estructuras")
    
tipo_item_add_form = TipoItemAddForm(DBSession)


class TipoItemEditForm(EditableForm):
    __model__ = TipoItem
    __hide_fields__ = ['id_tipo_item', 'id_proyecto', 'id_fase']
    __omit_fields__ = ['codigo', 'hijos', 'atributos', 'items', 'roles']
    #__check_if_unique__ = True
    __field_order__ = ['nombre', 'descripcion', 'id_padre' ]
    __field_attrs__ = {'descripcion' : {'row': '1'},
                       'nombre': { 'maxlength' : '50'}
                       
                      }
    __require_fields__ = ['nombre']
    id_padre = TipoPadreField("id_padre", accion="edit", label_text="Tipo Padre")
    descripcion = TextArea

tipo_item_edit_form = TipoItemEditForm(DBSession)


class TipoItemEditFiller(EditFormFiller):
    __model__ = TipoItem

tipo_item_edit_filler = TipoItemEditFiller(DBSession)


class TipoItemController(CrudRestController):
    """Controlador para tipos de item"""
        
    #{ Variables
    title = u"Tipos de Ítem de fase: %s"
    action = "./"
    subaction = "./atributostipoitem/"
    
    #{subcontroller
    miembrostipo  = MiembrosTipoController()
    nomiembrostipo = NoMiembrosTipoController()
    atributostipoitem = AtributosPorTipoItemController(DBSession)
    rolestipo = RolesTipoController(DBSession)
    #{ Plantillas

    # No permitir tipo_items anonimos (?)
    allow_only = not_anonymous(u"El usuario debe haber iniciado sesión")
    
    #{ Modificadores

        
    model = TipoItem
    table = tipo_item_table
    table_filler = tipo_item_table_filler
    new_form = tipo_item_add_form
    edit_form = tipo_item_edit_form
    edit_filler = tipo_item_edit_filler

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
        id_fase = UrlParser.parse_id(request.url, "fases")
        atras = "../"        
        if not id_proyecto:
            id_proyecto = UrlParser.parse_id(request.url, "proyectos_fase")
            if not id_proyecto:
                id_proyecto = UrlParser.parse_id(request.url, "proyectos_fase_ti")
                id_fase = UrlParser.parse_id(request.url, "fases_ti")
            atras = "../../"
        
        proy = Proyecto.por_id(id_proyecto)
        puede_crear = puede_crear = PoseePermiso("crear tipo item",
                                                 id_fase=id_fase).is_met(request.environ)
        if proy.estado != "Iniciado":
            puede_crear = False
            
        fase = Fase.por_id(id_fase)
        titulo = self.title % fase.nombre
        tipo_items = self.table_filler.get_value(id_fase=id_fase, **kw)
        tmpl_context.widget = self.table
        url_action = self.action
        
        if UrlParser.parse_nombre(request.url, "post_buscar"):
            url_action = "../"

        
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

    @expose('lpm.templates.tipoitem.edit')
    def edit(self, *args, **kw):
        """Despliega una pagina para modificar tipo_item"""
        id_tipo = UrlParser.parse_id(request.url, "tipositems")
        id_fase = UrlParser.parse_id(request.url, "fases")
        if not id_fase:
            id_fase = UrlParser.parse_id(request.url, "fases_ti")
        
        value = self.edit_filler.get_value(values={'id_tipo_item': id_tipo})
        url_action = "./"
        pp = PoseePermiso('redefinir tipo item', id_tipo_item=id_tipo)
                          
        if not pp.is_met(request.environ):
            flash(pp.message % pp.nombre_permiso, 'warning')
            redirect(url_action)

        tmpl_context.widget = self.edit_form
        value['_method'] = 'PUT'
        page = "Tipo Item: {nombre}".format(nombre=value["nombre"])
        return dict(value=value, 
                    page=page, 
                    atras=url_action, 
                    url_action=url_action
                    )

    @without_trailing_slash
    @expose('lpm.templates.tipoitem.new')
    def new(self, *args, **kw):
        """Despliega una pagina para crear un tipo_item"""
        id_fase = UrlParser.parse_id(request.url, "fases")
        if not id_fase:
            id_fase = UrlParser.parse_id(request.url, "fases_ti")

        pp = PoseePermiso('crear tipo item', id_fase=id_fase)
        if not pp.is_met(request.environ):
            flash(pp.message % pp.nombre_permiso, 'warning')
            redirect("./")
            
        atras = self.action
        tmpl_context.widget = self.new_form
        return dict(value=kw, 
                    page=u"Nuevo Tipo de Ítem", 
                    action=self.action, 
                    atras=atras)
    
    #@validate(tipo_item_add_form, error_handler=new)
    @expose()
    def post(self, *args, **kw):
        """create a new record"""
        id_proyecto = UrlParser.parse_id(request.url, "proyectos")
        id_fase = UrlParser.parse_id(request.url, "fases")
        if not id_proyecto:
            id_proyecto = UrlParser.parse_id(request.url, "proyectos_fase")
            if not id_proyecto:
                id_proyecto = UrlParser.parse_id(request.url, "proyectos_fase_ti")
                id_fase = UrlParser.parse_id(request.url, "fases_ti")

        pp = PoseePermiso('crear tipo item', id_fase=id_fase)
        url_action = self.action
        
        if not pp.is_met(request.environ):
            flash(pp.message % pp.nombre_permiso, 'warning')
            redirect(url_action)
            
        if kw.has_key("sprox_id"):
            del kw["sprox_id"]
            
        id_padre = int(kw["id_padre"])
        id_importado = kw["id_importado"]
        
        if (kw["id_importado"]):
            id_importado = int(kw["id_importado"])
        mezclar = False
        if kw.has_key("mezclar"):
            mezclar = kw["mezclar"]
            del kw["mezclar"]
        del kw["id_padre"]
        del kw["id_importado"]
        
        proy = Proyecto.por_id(id_proyecto)
        tipo = proy.definir_tipo_item(id_padre, id_importado, mezclar, **kw)
        
        #Creamos el rol miembro  de tipo de ítem
        #plant_m = Rol.obtener_rol_plantilla(nombre_rol=u"Miembro de Tipo Item")
        #rol_m = Rol.nuevo_rol_desde_plantilla(plantilla=plant_m, 
        #                                      id=tipo.id_tipo_item)
        
        flash(u"Creacion exitosa")
        redirect(url_action)
        
    @validate(tipo_item_edit_form, error_handler=edit)
    @expose()
    def put(self, *args, **kw):
        """update a record"""
        url_action = url_action = "../../"
        pp = PoseePermiso('redefinir tipo item',
                          id_tipo_item=kw["id_tipo_item"])
        if not pp.is_met(request.environ):
            flash(pp.message % pp.nombre_permiso, 'warning')
            redirect(url_action)

        tipo = TipoItem.por_id(int(kw["id_tipo_item"]))  
        tipo.descripcion = unicode(kw["descripcion"])
        flash("Actualizacion exitosa")
        redirect("./")
    
    
    @with_trailing_slash
    @paginate('lista_elementos', items_per_page=5)
    @expose('lpm.templates.tipoitem.get_all')
    @expose('json')
    def post_buscar(self, *args, **kw):
        id_proyecto = UrlParser.parse_id(request.url, "proyectos")
        id_fase = UrlParser.parse_id(request.url, "fases")
        atras = "../"
        if not id_proyecto:
            id_proyecto = UrlParser.parse_id(request.url, "proyectos_fase")
            if not id_proyecto:
                id_proyecto = UrlParser.parse_id(request.url, "proyectos_fase_ti")
                id_fase = UrlParser.parse_id(request.url, "fases_ti")
            atras = "../../../"
        
        proy = Proyecto.por_id(id_proyecto)
        puede_crear = puede_crear = PoseePermiso("crear tipo item",
                                                 id_fase=id_fase).is_met(request.environ)
        if proy.estado != "Iniciado":
            puede_crear = False
        fase = Fase.por_id(id_fase)
        titulo = self.title % fase.nombre
        tmpl_context.widget = self.table
        buscar_table_filler = self.table_filler.__class__(DBSession)
        buscar_table_filler.filtros = kw
        tipos_items = buscar_table_filler.get_value(id_fase=id_fase)
        
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
        """This is the code that actually deletes the record"""
        atras = './'
        id_tipo = int(args[0])
        tipo = TipoItem.por_id(id_tipo)
        DBSession.delete(tipo)
        redirect(atras)

    @with_trailing_slash
    @paginate('lista_elementos', items_per_page=5)
    @expose('lpm.templates.tipoitem.get_all')
    @expose('json')
    def get_one(self, *args, **kw):
        id_tipo = int(args[0])
        id_proyecto = UrlParser.parse_id(request.url, "proyectos")
        id_fase = UrlParser.parse_id(request.url, "fases")
        if not id_proyecto:
            id_proyecto = UrlParser.parse_id(request.url, "proyectos_fase")
            if not id_proyecto:
                id_proyecto = UrlParser.parse_id(request.url, "proyectos_fase_ti")
                id_fase = UrlParser.parse_id(request.url, "fases_ti")
        
        proy = Proyecto.por_id(id_proyecto)
        puede_crear = puede_crear = PoseePermiso("crear tipo item",
                                                 id_fase=id_fase).is_met(request.environ)
        if proy.estado != "Iniciado":
            puede_crear = False
            
        ti = self.table_filler.get_value(id_tipo=id_tipo, **kw)
            
        tmpl_context.widget = self.table
        fase = Fase.por_id(id_fase)
        titulo = self.title % fase.nombre
        atras = '../'
        return dict(lista_elementos=ti, 
                    page=titulo,
                    titulo=titulo, 
                    modelo=self.model.__name__, 
                    columnas=self.columnas,
                    opciones=self.opciones,
                    url_action=self.action,
                    puede_crear=puede_crear,
                    atras=atras
                    )

    #}
