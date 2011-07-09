# -*- coding: utf-8 -*-
"""
Módulo que define el controlador basico de proyectos.
El mismo se utiliza para listar los proyectos.

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
from tg import redirect, request, require, flash, validate, session
from lpm.model import DBSession, Proyecto, Usuario, Rol
from lpm.lib.sproxcustom import (CustomTableFiller, 
                                 CustomPropertySingleSelectField)
from lpm.lib.authorization import PoseePermiso, AlgunPermiso, Miembro
from lpm.lib.util import UrlParser
from lpm.controllers.proyecto import ProyectoTable
from lpm.controllers.fase_desarrollo import FaseDesarrolloController

from sprox.tablebase import TableBase
from sprox.fillerbase import TableFiller, EditFormFiller, RecordFiller
from sprox.fillerbase import EditFormFiller
from sprox.formbase import AddRecordForm, EditableForm
from sprox.recordviewbase import RecordViewBase
from repoze.what.predicates import not_anonymous, is_anonymous, All

import pylons
from pylons import tmpl_context
from pylons.decorators import rest


import transaction

from tw.forms import TextField


proyectos_desarrollo_table = ProyectoTable(DBSession)


class ProyectosDesarrolloTableFiller(CustomTableFiller):
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
        value += '<div>' + \
                    '<a href="./'+ str(obj.id_proyecto) + '/fases_desarrollo/" ' + \
                    'class="' + clase + '">Seleccionar</a>' + \
                 '</div><br />'

        value += '</div>'
        return value
    
    def _do_get_provider_count_and_objs(self, **kw):
        """
        Retorna la Lista de los proyectos en los cuales el usuario
        es miembro
        """
            
        count, lista = super(ProyectosDesarrolloTableFiller, self).\
                            _do_get_provider_count_and_objs(**kw)
        filtrados = []                    
        for p in lista:
            if (AlgunPermiso(tipo= "Tipo", id_proyecto=p.id_proyecto).is_met(request.environ) and\
                p.estado == u"Iniciado"):
                filtrados.append(p)
            
        return len(filtrados), filtrados         


proyectos_desarrollo_table_filler = ProyectosDesarrolloTableFiller(DBSession)
    
    
class ProyectosDesarrolloController(CrudRestController):
    """Controlador de Proyectos"""
    #{ Variables
    title = u"Proyectos"
    #{ Plantillas
    tmp_action = "./"
    # No permitir usuarios anonimos (?)
    allow_only = not_anonymous(u"El usuario debe haber iniciado sesión")
    
    #{ Sub Controlador
    fases_desarrollo = FaseDesarrolloController(DBSession)
    
    #{ Modificadores
    model = Proyecto
    table = proyectos_desarrollo_table
    table_filler = proyectos_desarrollo_table_filler
    
    
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
        if pylons.request.response_type == 'application/json':
            return dict(lista=self.table_filler.get_value(**kw))
        if not getattr(self.table.__class__, ' ', False):
            proyectos = self.table_filler.get_value(**kw)
        else:
            proyectos = []
            
        tmpl_context.widget = self.table
        atras = './'
        return dict(lista_elementos=proyectos, 
                    page=self.title,
                    titulo=self.title, 
                    modelo=self.model.__name__, 
                    columnas=self.columnas,
                    opciones=self.opciones,
                    url_action="./",
                    puede_crear=False,
                    comboboxes=self.comboboxes,
                    atras=atras
                    )

                
    @without_trailing_slash
    @paginate('lista_elementos', items_per_page=5)
    @expose('lpm.templates.proyecto.get_all')
    @expose('json')
    def post_buscar(self, *args, **kw):
        """
        Controlador que recibe los parámetros de búsqueda para 
        devolver el resultado esperado.
        """
        tmpl_context.widget = self.table
        buscar_table_filler = ProyectosDesarrolloTableFiller(DBSession)
        buscar_table_filler.filtros = kw
        proyectos = buscar_table_filler.get_value()
        
        atras = './'
        
        return dict(lista_elementos=proyectos, 
                    page=self.title, 
                    titulo=self.title, 
                    modelo=self.model.__name__,
                    columnas=self.columnas,
                    url_action="../",
                    puede_crear=False,
                    comboboxes=self.comboboxes,
                    opciones=self.opciones,
                    atras=atras
                    )
    
    @expose('lpm.templates.index')
    def _default(self, *args, **kw):
        """Maneja las urls no encontradas"""
        flash(_('Recurso no encontrado'), 'warning')
        redirect('/')
        return dict(page='index')
    
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

    @expose()
    def get_one(self, *args, **kw):
        pass

    @expose()
    def post_delete(self, *args, **kw):
        pass

    #}
