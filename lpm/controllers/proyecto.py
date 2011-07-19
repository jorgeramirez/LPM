# -*- coding: utf-8 -*-
"""
Módulo que define el controlador de proyectos.

@authors:
    - U{Carlos Bellino<mailto:carlosbellino@gmail.com>}
    - U{Nahuel Hernández<mailto:nahuel.11990@gmail.com>}
    - U{Jorge Ramírez<mailto:jorgeramirez1990@gmail.com>}

@since: 1.0
"""
from tgext.crud import CrudRestController
from tg.decorators import (paginate, expose, with_trailing_slash, 
                           without_trailing_slash)
from tg import redirect, request, require, flash, validate, session

from lpm.controllers.validaciones.proyecto_validator import ProyectoAddFormValidator, ProyectoEditFormValidator
from lpm.model import DBSession, Proyecto, Usuario, Rol, PropiedadItem, Item, Fase
from lpm.lib.sproxcustom import (CustomTableFiller, 
                                 CustomPropertySingleSelectField)
from lpm.lib.authorization import PoseePermiso, AlgunPermiso
from lpm.lib.util import UrlParser
from lpm.controllers.fase import FaseController, FaseTableFiller, FaseTable
from lpm.controllers.tipoitem import TipoItemController, TipoItemTableFiller
from lpm.controllers.miembros_proyecto import MiembrosProyectoController
from lpm.controllers.no_miembros_proyecto import NoMiembrosProyectoController
from lpm.controllers.roles_proyecto import RolesProyectoController
from lpm.controllers.proyecto_tipoitem import ProyectoTipoItemController

from sprox.tablebase import TableBase
from sprox.fillerbase import TableFiller, EditFormFiller, RecordFiller
from sprox.fillerbase import EditFormFiller
from sprox.formbase import AddRecordForm, EditableForm
from sprox.recordviewbase import RecordViewBase
from repoze.what.predicates import not_anonymous, is_anonymous, All

from sqlalchemy import and_

import pylons
from pylons import tmpl_context
from pylons.decorators import rest


import transaction

from tw.forms import TextField

class ProyectoTable(TableBase):
    __model__ = Proyecto
    __headers__ = {'id_proyecto': u'ID', 'fecha_creacion': u'Creación',
                   'complejidad_total': u'Compl.', 'estado': u'Estado',
                   'numero_fases': u'#Fases', 'descripcion': u'Descripción',
                   'project_leader': 'Lider', 'codigo': u"Código"
                  }
    __omit_fields__ = ['fases', 'tipos_de_item', 'id_proyecto', 'descripcion',
                       'roles']
    __default_column_width__ = '15em'
    __field_order__ = ['codigo', 'nombre', 'numero_fases', 'estado',
                        'project_leader', 'complejidad_total',
                        'fecha_creacion']
    __column_widths__ = {'complejidad_total': "25em",
                         'numero_fases': "35em",
                         '__actions__' : "50em",
                         'codigo': "30em"
                        }
    __field_attrs__ = {'completidad_total': { 'text-aling' : 'center'}}#?
    __add_fields__ = {'project_leader':None}
    
proyecto_table = ProyectoTable(DBSession)


class ProyectoTableFiller(CustomTableFiller):
    __model__ = Proyecto
    __add_fields__ = {'project_leader': None}
    
    def project_leader(self, obj):
        lider = obj.obtener_lider()
        if lider:
            return lider.nombre_usuario
        return None
    
    def __actions__(self, obj):
        """Links de acciones para un registro dado"""
        value = '<div>'
        clase = 'actions'

        if PoseePermiso('modificar proyecto',
                        id_proyecto=obj.id_proyecto).is_met(request.environ):
            value += '<div>' + \
                        '<a href="/proyectos/'+ str(obj.id_proyecto) + '/edit" ' + \
                        'class="' + clase + '">Modificar</a>' + \
                     '</div><br />'

            value += '<div>' + \
                        '<a href="/proyectos/'+ str(obj.id_proyecto) + '/fases" ' + \
                        'class="' + clase + '">Fases</a>' + \
                     '</div><br />'

            value += '<div>' + \
                        '<a href="/proyectos/'+ str(obj.id_proyecto) + '/tipositems" ' + \
                        'class="' + clase + '">Tipos de Ítem</a>' + \
                     '</div><br />'
                     
            value += '<div>' + \
                        '<a href="/proyectos/'+ str(obj.id_proyecto) + '/rolesproyecto" ' + \
                        'class="' + clase + '">Roles de Proyecto</a>' + \
                     '</div><br />'

            value += '<div>' + \
                        '<a href="/proyectos/'+ str(obj.id_proyecto) + '/miembros" ' + \
                        'class="' + clase + '">Usuarios</a>' + \
                     '</div><br />'

            '''
            value += '<div>' + \
                        '<a href="/proyectos/'+ str(obj.id_proyecto) + '/nomiembros" ' + \
                        'class="' + clase + '">No miembros</a>' + \
                     '</div><br />'
            '''

        if obj.estado == u"No Iniciado":
            if (PoseePermiso('iniciar proyecto', 
                        id_proyecto=obj.id_proyecto).is_met(request.environ) and\
                        obj.numero_fases > 0):
                value += '<div>' + \
                            '<a href="/proyectos/iniciar/' + str(obj.id_proyecto) + '" ' +\
                            'class="' + clase + '">Iniciar</a>' + \
                         '</div><br />'


        if PoseePermiso('eliminar proyecto',
                        id_proyecto=obj.id_proyecto).is_met(request.environ):
            url = "/proyectos/post_delete/%d" % obj.id_proyecto
            value += '<div><form method="POST" action="' + url + '" class="button-to">'+\
                     '<input onclick="return confirm(\'¿Está seguro?\');" value="Eliminar" type="submit" '+\
                     'style="background-color: transparent; float:left; border:0; color: #286571;'+\
                     'display: inline; margin: 0; padding: 0; margin-left: -3px;" class="' + clase + '"/>'+\
                     '</form></div><br />'

        value += '</div>'
        return value
    
    def _do_get_provider_count_and_objs(self, id_proyecto=None, **kw):
        """
        Retorna la Lista los proyectos del sistema sobre
        """
        if id_proyecto:
            proy  = Proyecto.por_id(id_proyecto)
            return 1, [proy]
            
        count, lista = super(ProyectoTableFiller, self).\
                            _do_get_provider_count_and_objs(**kw)
        filtrados = []                    
        for p in lista:
            pp = PoseePermiso(u"modificar proyecto", id_proyecto=p.id_proyecto)
            if pp.is_met(request.environ):
                filtrados.append(p)
            
        return len(filtrados), filtrados         


proyecto_table_filler = ProyectoTableFiller(DBSession)

class ProyectoAddForm(AddRecordForm):
    __model__ = Proyecto
    __omit_fields__ = ['id_proyecto', 'fecha_creacion', 'complejidad_total',
                       'estado', 'fases', 'tipos_de_item', 'codigo',
                       'numero_fases', 'roles']
    __field_order__ = ['nombre', 'descripcion']
    __base_validator__ = ProyectoAddFormValidator
    

proyecto_add_form = ProyectoAddForm(DBSession)


class ProyectoEditForm(EditableForm):
    __model__ = Proyecto
    __hide_fields__ = ['id_proyecto']
    __omit_fields__ = ['fecha_creacion', 'complejidad_total',
                       'estado', 'numero_fases', 'codigo', 'fases', 
                       'tipos_de_item', 'roles']
    __base_validator__ = ProyectoEditFormValidator

proyecto_edit_form = ProyectoEditForm(DBSession)        

class ProyectoEditFiller(EditFormFiller):
    __model__ = Proyecto
    
proyecto_edit_filler = ProyectoEditFiller(DBSession)

    
    
class ProyectoController(CrudRestController):
    """Controlador de Proyectos"""
    #{ Variables
    title = u"Administrar Proyectos"
    #{ Plantillas
    tmp_action = "/proyectos/buscar"
    # No permitir usuarios anonimos (?)
    allow_only = not_anonymous(u"El usuario debe haber iniciado sesión")
    
    #{ Sub Controlador
    fases = FaseController(DBSession)
    tipositems = ProyectoTipoItemController(DBSession)
    miembros = MiembrosProyectoController()
    nomiembros = NoMiembrosProyectoController()
    rolesproyecto = RolesProyectoController(DBSession)
    
    #{ Modificadores
    model = Proyecto
    table = proyecto_table
    table_filler = proyecto_table_filler
    new_form = proyecto_add_form
    edit_form = proyecto_edit_form
    edit_filler = proyecto_edit_filler
    
    
    #para el form de busqueda
    opciones = dict(nombre=u"Nombre de Proyecto",
                   codigo=u"Código",
                   estado=u"Estado",
                   complejidad_total=u"Complejidad Total",
                   numero_fases=u"Número de Fases",
                   fecha_creacion=u"Fecha de Creación"
                   )
    
    #el diccionario opciones de tiene lo que se muestra en 
    #el combobox de selección de filtros,
    #tiene que tener la misma clave que los valores de columnas
    columnas = dict(nombre="texto",
                    codigo="texto",#lider="text",
                    estado="combobox",
                    complejidad_total="entero",
                    numero_fases="entero",
                    fecha_creacion="fecha"
                    )
    
    comboboxes = dict(estado=Proyecto.estados_posibles)
    
    #{ Métodos
    @with_trailing_slash
    @paginate('lista_elementos', items_per_page=5)
    @expose('lpm.templates.proyecto.get_all')
    @expose('json')
    def get_all(self, *args, **kw):
        """ 
        Retorna todos los registros
        Retorna una página HTML si no se especifica JSON
        """
        puede_crear = PoseePermiso("crear proyecto").is_met(request.environ)
        if pylons.request.response_type == 'application/json':
            return dict(lista=self.table_filler.get_value(**kw))
        if not getattr(self.table.__class__, ' ', False):
            proyectos = self.table_filler.get_value(**kw)
        else:
            proyectos = []
            
        tmpl_context.widget = self.table
        atras = '/'
        return dict(lista_elementos=proyectos, 
                    page=self.title,
                    titulo=self.title, 
                    modelo=self.model.__name__, 
                    columnas=self.columnas,
                    opciones=self.opciones,
                    url_action="/proyectos/",
                    puede_crear=puede_crear,
                    comboboxes=self.comboboxes,
                    atras=atras
                    )

    @expose()
    def iniciar(self, id_proyecto):
        """Inicia un proyecto"""
        
        if (not PoseePermiso('iniciar proyecto', 
                        id_proyecto=id_proyecto).is_met(request.environ)):
            flash("No puedes iniciar el proyecto", "warning")
            
        proy = Proyecto.por_id(id_proyecto)
        if not proy.obtener_lider():
            msg = "No puedes iniciar el proyecto. Debes primero asignarle "
            msg += "un lider"
            flash(msg, "warning")
            redirect("/proyectos/")
        proy.iniciar_proyecto()
        flash("El proyecto se ha iniciado correctamente")
        redirect("/proyectos/")
                
    @without_trailing_slash
    @paginate('lista_elementos', items_per_page=5)
    @expose('lpm.templates.proyecto.get_all')
    @expose('json')
    def post_buscar(self, *args, **kw):
        """
        Controlador que recibe los parámetros de búsqueda para 
        devolver el resultado esperado.
        """
        
        puede_crear = PoseePermiso("crear proyecto").is_met(request.environ)
        pp = PoseePermiso('consultar proyecto')
        if not pp.is_met(request.environ):
            flash(pp.message % pp.nombre_permiso, 'warning')
            redirect("/proyectos/")

        tmpl_context.widget = self.table
        buscar_table_filler = ProyectoTableFiller(DBSession)
        buscar_table_filler.filtros = kw
        proyectos = buscar_table_filler.get_value()
        
        atras = '/proyectos/'
        
        return dict(lista_elementos=proyectos, 
                    page=self.title, 
                    titulo=self.title, 
                    modelo=self.model.__name__,
                    columnas=self.columnas,
                    url_action="/proyectos/",
                    puede_crear=puede_crear,
                    comboboxes=self.comboboxes,
                    opciones=self.opciones,
                    atras=atras
                    )
    
    @without_trailing_slash
    @expose('lpm.templates.proyecto.new')
    def new(self, *args, **kw):
        """Display a page to show a new record."""
        tmpl_context.widget = self.new_form
        atras = "/proyectos/"
        return dict(value=kw, page="Nuevo Proyecto", atras=atras)    
    
    @validate(proyecto_add_form, error_handler=new)
    @expose()
    def post(self, *args, **kw):
        if "sprox_id" in kw:
            del kw["sprox_id"]

        proy = Proyecto(**kw)
        DBSession.add(proy)
        DBSession.flush()
        proy.codigo = Proyecto.generar_codigo(proy)

        #Creamos el rol miembro  y lider de proyecto para este proyecto.
        plant_l = Rol.obtener_rol_plantilla(nombre_rol=u"Lider de Proyecto")
        rol_l = Rol.nuevo_rol_desde_plantilla(plantilla=plant_l, id=proy.id_proyecto)

        flash("Se ha creado un nuevo proyecto")
        redirect("/proyectos/")

    @expose('lpm.templates.proyecto.edit')
    def edit(self, id_proyecto,*args, **kw):
        """Despliega una pagina para admistrar un proyecto"""

        pp = PoseePermiso('modificar proyecto', id_proyecto=id_proyecto)
        if not pp.is_met(request.environ):
            flash(pp.message % pp.nombre_permiso, 'warning')
            redirect("/proyectos")
        proyecto = Proyecto.por_id(id_proyecto)
        tmpl_context.widget = self.edit_form
        value = self.edit_filler.get_value(values={'id_proyecto': id_proyecto})
        value['_method'] = 'PUT'
        atras = "/proyectos/"
        return dict(value=value,
                    page="Modificar Proyecto %s" % proyecto.nombre,
                    atras=atras
                    )
    
    @validate(proyecto_edit_form, error_handler=edit)
    @expose()
    def put(self, *args, **kw):
        """Registra los cambios en la edición de un
        proyecto.
        """
        if "sprox_id" in kw:
            del kw["sprox_id"]
        id_proyecto = UrlParser.parse_id(request.url, "proyectos")
        proy = Proyecto.por_id(id_proyecto)
        proy.nombre = unicode(kw["nombre"])
        proy.descripcion = unicode(kw["descripcion"])
        redirect("/proyectos/")
    
    @expose()
    def post_delete(self, id_proyecto):
        proy = Proyecto.por_id(int(id_proyecto))
        p_items = DBSession.query(PropiedadItem).filter(and_(PropiedadItem.id_item_actual ==\
                                                   Item.id_item, Item.id_fase == \
                                                   Fase.id_fase, Fase.id_proyecto ==
                                                   id_proyecto)).all()
        for pi in p_items:
            DBSession.delete(pi)
                                                   
        DBSession.delete(proy)
        flash("Proyecto Eliminado")
        redirect("/proyectos/")
        
    @expose('lpm.templates.index')
    def _default(self, *args, **kw):
        """Maneja las urls no encontradas"""
        flash(_('Recurso no encontrado'), 'warning')
        redirect('/')
        return dict(page='index')


    @with_trailing_slash
    @paginate('lista_elementos', items_per_page=5)
    @expose('lpm.templates.proyecto.get_all')
    @expose('json')
    def get_one(self, *args, **kw):
        id_proyecto = int(args[0])
        puede_crear = PoseePermiso("crear proyecto").is_met(request.environ)
        if pylons.request.response_type == 'application/json':
            return dict(lista=self.table_filler.get_value(id_proyecto=id_proyecto,
                                                          **kw))
        if not getattr(self.table.__class__, ' ', False):
            proyecto = self.table_filler.get_value(id_proyecto=id_proyecto,
                                                    **kw)
        else:
            proyecto = []
            
        tmpl_context.widget = self.table
        atras = '../'
        return dict(lista_elementos=proyecto,
                    page=self.title,
                    titulo=self.title, 
                    modelo=self.model.__name__, 
                    columnas=self.columnas,
                    opciones=self.opciones,
                    url_action="/proyectos/",
                    puede_crear=puede_crear,
                    comboboxes=self.comboboxes,
                    atras=atras
                    )

    #}
