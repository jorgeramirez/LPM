# -*- coding: utf-8 -*-
"""
Módulo que define el controlador de fases para acceder a las 
líneas base con las que se puede trabajar.

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

from lpm.model import DBSession, Fase, Proyecto, Rol
from lpm.lib.sproxcustom import (CustomTableFiller,
                                 CustomPropertySingleSelectField)
from lpm.lib.authorization import PoseePermiso, AlgunPermiso, Miembro
from lpm.lib.util import UrlParser
from lpm.controllers.tipoitem import TipoItemController, TipoItemTableFiller
from lpm.controllers.validaciones.fase_validator import FaseFormValidator
from lpm.controllers.miembros_fase import MiembrosFaseController
from lpm.controllers.no_miembros_fase import NoMiembrosFaseController
from lpm.controllers.roles_fase import RolesFaseController
from lpm.controllers.fase import FaseTable
from lpm.controllers.lineabase import LineaBaseController

from sprox.tablebase import TableBase
from sprox.fillerbase import TableFiller, EditFormFiller
from sprox.fillerbase import EditFormFiller
from sprox.formbase import AddRecordForm, EditableForm

from repoze.what.predicates import not_anonymous

import pylons
from pylons import tmpl_context

import transaction

    
fases_gestconf_table = FaseTable(DBSession)


class FasesGestConfTableFiller(CustomTableFiller):
    __model__ = Fase
    
    def __actions__(self, obj):
        """Links de acciones para un registro dado"""
        value = '<div>'
        clase = 'actions_fase'
        id_proyecto = UrlParser.parse_id(request.url, "proyectos_gestconf")
        url_proy = "/proyectos_gestconf/"

        url_cont = url_proy + "%d/fases/"
        url_cont %= id_proyecto


        value += '<div>' + \
                    '<a href="'+ url_cont + str(obj.id_fase) + '/lbs/" ' + \
                    'class="' + clase + '">Seleccionar</a>' + \
                 '</div>'
        value += '</div>'
        return value
    
    def _do_get_provider_count_and_objs(self, id_proyecto=None, **kw):
        """
        Retorna las fases del proyecto en cuestión
        """

        count, lista = super(FasesGestConfTableFiller, self).\
                            _do_get_provider_count_and_objs(**kw)
        filtrados = []                    
        if id_proyecto:
            id_proyecto = int(id_proyecto)
            #ap = AlgunPermiso(tipo='Fase', id_proyecto=id_proyecto).is_met(request.environ)
            
            #se listan las fases del proyecto
            for f in lista:
                if f.id_proyecto == id_proyecto and \
                   AlgunPermiso(tipo="Tipo", 
                                id_fase=f.id_fase).is_met(request.environ):
                    filtrados.append(f)
                    
        return len(filtrados), filtrados
                   

fases_gestconf_table_filler = FasesGestConfTableFiller(DBSession)


class FasesGestConfController(CrudRestController):
    """Controlador de Fases en Desarrollo"""
        
    #{ Variables
    title = u"Fases de proyecto: %s"
    allow_only = not_anonymous(u"El usuario debe haber iniciado sesión")
    
    #Subcontrolador
    lbs = LineaBaseController(DBSession)
    
    #{ Modificadores

    model = Fase
    table = fases_gestconf_table
    table_filler = fases_gestconf_table_filler
    
    opciones = dict(nombre= u'Nombre',
                    posicion= u'Posición',
                    numero_items= u'Nro. de Ítems', 
                    estado= u'Estado',
                    codigo= u'Código'
                    )
                    
    columnas = dict(nombre='texto',
                    posicion='entero',
                    numero_items='entero', 
                    estado='combobox',
                    codigo='texto'
                    )
                    
    comboboxes = dict(estado=Fase.estados_posibles)
    
    #{ Métodos
    @with_trailing_slash
    @paginate('lista_elementos', items_per_page=5)
    @expose('lpm.templates.fases.get_all')
    @expose('json')
    def get_all(self, *args, **kw):
        """ 
        Retorna todos los registros
        Retorna una página HTML si no se especifica JSON
        """
        id_proyecto = UrlParser.parse_id(request.url, "proyectos_gestconf")
        
        proy = Proyecto.por_id(id_proyecto)

        titulo = self.title % proy.nombre
        atras = "../"
        fases = self.table_filler.get_value(id_proyecto=id_proyecto, **kw)
        tmpl_context.widget = self.table
        
        return dict(lista_elementos=fases, 
                    page=titulo,
                    titulo=titulo, 
                    modelo=self.model.__name__, 
                    columnas=self.columnas,
                    opciones=self.opciones,
                    url_action='./',
                    puede_crear=False,
                    comboboxes=self.comboboxes,
                    atras=atras
                    )
    
    @without_trailing_slash
    @paginate('lista_elementos', items_per_page=5)
    @expose('lpm.templates.fases.get_all')
    @expose('json')
    def post_buscar(self, *args, **kw):
        """
        Controlador que recibe los parámetros de búsqueda para 
        devolver el resultado esperado.
        """
        id_proyecto = UrlParser.parse_id(request.url, "proyectos_gestconf")
        
        proy = Proyecto.por_id(id_proyecto)

        titulo = self.title % proy.nombre
        atras = "../"
        buscar_table_filler = FasesGestConfTableFiller(DBSession)
        buscar_table_filler.filtros = kw
        fases = buscar_table_filler.get_value(id_proyecto=id_proyecto, **kw)
        tmpl_context.widget = self.table
        
        return dict(lista_elementos=fases, 
                    page=titulo,
                    titulo=titulo, 
                    modelo=self.model.__name__, 
                    columnas=self.columnas,
                    opciones=self.opciones,
                    url_action='../',
                    puede_crear=False,
                    comboboxes=self.comboboxes,
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
    def post_delete(self, id):
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
    #}
