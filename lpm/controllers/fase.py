# -*- coding: utf-8 -*-
"""
Módulo que define el controlador de fases.

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
from lpm.lib.authorization import PoseePermiso, AlgunPermiso
from lpm.lib.util import UrlParser
from lpm.controllers.tipoitem import TipoItemController, TipoItemTableFiller
from lpm.controllers.validaciones.fase_validator import FaseFormValidator
from lpm.controllers.miembros_fase import MiembrosFaseController
from lpm.controllers.no_miembros_fase import NoMiembrosFaseController
from lpm.controllers.roles_fase import RolesFaseController
from sprox.tablebase import TableBase
from sprox.fillerbase import TableFiller, EditFormFiller
from sprox.fillerbase import EditFormFiller
from sprox.formbase import AddRecordForm, EditableForm

from repoze.what.predicates import not_anonymous

import pylons
from pylons import tmpl_context

import transaction


class FaseTable(TableBase):
    __model__ = Fase
    __headers__ = { 'id_fase': u'ID',
                    'nombre': u'Nombre',
                    'posicion': u'Posición',
                    'numero_items': u'Nro. de Ítems', 
                    'estado': u'Estado',
                    'codigo': u'Código'
                  }
    __omit_fields__ = ['items', 'id_proyecto', 'id_fase', 
                       'numero_lb', 'descripcion', 'roles', 'tipos_de_item']
    __default_column_width__ = '15em'
    __column_widths__ = { 'descripcion': "35em", '__actions__': "50em"}
    
fase_table = FaseTable(DBSession)


class FaseTableFiller(CustomTableFiller):
    __model__ = Fase
    
    def __actions__(self, obj):
        """Links de acciones para un registro dado"""
        value = '<div>'
        clase = 'actions_fase'
        id_proyecto = UrlParser.parse_id(request.url, "proyectos")
        url_proy = "/proyectos/"
        if not id_proyecto:
            #desde el submenu fase.
            id_proyecto = UrlParser.parse_id(request.url, "proyectos_fase")
            url_proy = "/proyectos_fase/"
            
        url_cont = url_proy + "%d/fases/"
        url_cont %= id_proyecto

        if PoseePermiso('modificar fase',
                        id_fase=obj.id_fase).is_met(request.environ):
            value += '<div>' + \
                        '<a href="'+ url_cont + str(obj.id_fase) + '/edit" ' + \
                        'class="' + clase + '">Modificar</a>' + \
                     '</div><br />'

            value += '<div>' + \
                        '<a href="'+ url_cont + str(obj.id_fase) + '/rolesfase" ' + \
                        'class="' + clase + '">Roles de Fase</a>' + \
                     '</div><br />'


            value += '<div>' + \
                        '<a href="'+ url_cont + str(obj.id_fase) + '/tipositems" ' + \
                        'class="' + clase + '">Tipos de Ítem</a>' + \
                     '</div><br />'


            value += '<div>' + \
                        '<a href="'+ url_cont + str(obj.id_fase) + '/miembrosfase" ' + \
                        'class="' + clase + '">Miembros</a>' + \
                     '</div><br />'

            value += '<div>' + \
                        '<a href="'+ url_cont + str(obj.id_fase) + '/nomiembrosfase" ' + \
                        'class="' + clase + '">No miembros</a>' + \
                     '</div><br />'
                     

        proy = Proyecto.por_id(obj.id_proyecto)
        if proy.estado != "Iniciado" and \
            PoseePermiso('eliminar fase',
                         id_fase=obj.id_fase).is_met(request.environ):
            
            value += '<div><form method="POST" action="' + str(obj.id_fase) + '" class="button-to">'+\
                     '<input type="hidden" name="_method" value="DELETE" />' +\
                     '<input onclick="return confirm(\'¿Está seguro?\');" value="Eliminar" type="submit" '+\
                     'style="background-color: transparent; float:left; border:0; color: #286571; display: inline;'+\
                     'margin: 0; padding: 0; margin-left: -3px; margin-top: -3px;' + clase + '"/>'+\
                     '</form></div><br />'
                     
        value += '</div>'
        return value
    
    def _do_get_provider_count_and_objs(self, id_proyecto=None, id_fase=None, **kw):
        """
        Retorna las fases del proyecto en cuestión
        """
        if id_fase:
            fase  = Fase.por_id(id_fase)
            return 1, [fase]

        count, lista = super(FaseTableFiller, self).\
                            _do_get_provider_count_and_objs(**kw)
        filtrados = []                    
        if id_proyecto:
            id_proyecto = int(id_proyecto)
            #ap = AlgunPermiso(tipo='Fase', id_proyecto=id_proyecto).is_met(request.environ)

            for f in lista:
                if f.id_proyecto == id_proyecto:
                    if AlgunPermiso(tipo='Fase', 
                                    id_fase=f.id_fase).is_met(request.environ):
                        filtrados.append(f)
                
        return len(filtrados), filtrados
                   

fase_table_filler = FaseTableFiller(DBSession)


class PosicionField(CustomPropertySingleSelectField):
    """
    Dropdown field para las posiciones disponibles
    """
    def _my_update_params(self, d, nullable=False):
        
        id_proyecto = UrlParser.parse_id(request.url, "proyectos")
        
        if not id_proyecto:
            id_proyecto = UrlParser.parse_id(request.url, "proyectos_fase")
        
        if id_proyecto:
            proy = Proyecto.por_id(id_proyecto)
            
        options = []
        id_fase = UrlParser.parse_id(request.url, "fases")

        if id_fase:
            fase = Fase.por_id(id_fase)
            proy = Proyecto.por_id(fase.id_proyecto)
            
        if self.accion == "edit":
                options.append((fase.posicion, str(fase.posicion)))
                if (proy.estado != u"Iniciado"):
                    pos = range(1, proy.numero_fases + 1)
                    pos.pop(fase.posicion - 1)
                    options.extend(pos)
                    
        elif self.accion == "new":
            if (not id_proyecto):
                return d
            
            np = proy.numero_fases + 1
            options.append((np, str(np)))
            options.extend(range(1, np))
        d['options'] = options
        return d


class FaseAddForm(AddRecordForm):
    __model__ = Fase
    __omit_fields__ = ['id_fase', 'numero_items', 'numero_lb',
                       'estado', 'id_proyecto', 'codigo', 'items',
                       'roles', 'tipos_de_item']
    __base_validator__ = FaseFormValidator
    posicion = PosicionField("posicion", accion="new")

fase_add_form = FaseAddForm(DBSession)


class FaseEditForm(EditableForm):
    __model__ = Fase
    __hide_fields__ = ['id_fase', 'numero_items', 'numero_lb',
                       'estado', 'codigo', 'id_proyecto', 'items',
                       'roles', 'tipos_de_item']
    __base_validator__ = FaseFormValidator
    posicion = PosicionField("posicion", accion="edit")

fase_edit_form = FaseEditForm(DBSession)


class FaseEditFiller(EditFormFiller):
    __model__ = Fase

fase_edit_filler = FaseEditFiller(DBSession)


class FaseController(CrudRestController):
    """Controlador de Fases"""

        
    #{ Variables
    title = u"Fases de proyecto: %s"
    allow_only = not_anonymous(u"El usuario debe haber iniciado sesión")
    
    #{plantillas
    #tmp_action = "/proyectos/%d/fases/"
    #tmp_action_fase = "/proyectos_fase/%d/fases/" #desde submenu fase
    tmp_action = "./"
    #Subcontrolador
    tipositems = TipoItemController(DBSession)
    miembrosfase = MiembrosFaseController()
    nomiembrosfase = NoMiembrosFaseController()
    rolesfase = RolesFaseController(DBSession)
    
    #{ Modificadores

                     
    model = Fase
    table = fase_table
    table_filler = fase_table_filler     
    new_form = fase_add_form
    edit_form = fase_edit_form
    edit_filler = fase_edit_filler
    
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
        id_proyecto = UrlParser.parse_id(request.url, "proyectos")
        atras = "../"
        if not id_proyecto:
            id_proyecto = UrlParser.parse_id(request.url, "proyectos_fase")
            atras = "../../"
        
        puede_crear = PoseePermiso("crear fase", 
                                   id_proyecto=id_proyecto).is_met(request.environ)
        proy = Proyecto.por_id(id_proyecto)
        if proy.estado == "Iniciado":
            puede_crear = False

        titulo = self.title % proy.nombre
        fases = self.table_filler.get_value(id_proyecto=id_proyecto, **kw)
        tmpl_context.widget = self.table
  
        
        
        return dict(lista_elementos=fases, 
                    page=titulo,
                    titulo=titulo, 
                    modelo=self.model.__name__, 
                    columnas=self.columnas,
                    opciones=self.opciones,
                    url_action=self.tmp_action,
                    puede_crear=puede_crear,
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
        id_proyecto = UrlParser.parse_id(request.url, "proyectos")
        #action = self.tmp_action % id_proyecto
        if not id_proyecto:
            id_proyecto = UrlParser.parse_id(request.url, "proyectos_fase")
            #action = self.tmp_action_fase % id_proyecto     

        puede_crear = PoseePermiso("crear fase", 
                                   id_proyecto=id_proyecto).is_met(request.environ)

        proy = Proyecto.por_id(id_proyecto)
        if proy.estado == "Iniciado":
            puede_crear = False
            
        titulo = self.title % proy.nombre
        tmpl_context.widget = self.table
        buscar_table_filler = FaseTableFiller(DBSession)
        buscar_table_filler.filtros = kw
        fases = buscar_table_filler.get_value(id_proyecto=id_proyecto)
        atras = '../'
        
        return dict(lista_elementos=fases, 
                    page=titulo, 
                    titulo=titulo, 
                    modelo=self.model.__name__,
                    columnas=self.columnas,
                    url_action=self.tmp_action,
                    puede_crear=puede_crear,
                    comboboxes=self.comboboxes,
                    opciones=self.opciones,
                    atras=atras
                    )
    
    @without_trailing_slash
    @expose('lpm.templates.fases.new')
    def new(self, *args, **kw):
        """Display a page to show a new record."""
        id_proyecto = UrlParser.parse_id(request.url, "proyectos")
        atras = "./"
        if not id_proyecto:
            id_proyecto = UrlParser.parse_id(request.url, "proyectos_fase")
            atras = "../../"
        
        
        if not id_proyecto:
            redirect(atras)
        tmpl_context.widget = self.new_form
        return dict(value=kw, page="Nueva Fase", atras=atras)
    
    @expose()
    def post_delete(self, id):
        """Elimina una fase de la bd si el proyecto no está iniciado"""
        fase = Fase.por_id(id)
        proy = Proyecto.por_id(fase.id_proyecto)
        proy.eliminar_fase(id)
        flash("Fase eliminada")
        redirect("../")

        
    @validate(fase_add_form, error_handler=new)
    @expose()
    def post(self, *args, **kw):
        if "sprox_id" in kw:
            del kw["sprox_id"]
        id_proyecto = UrlParser.parse_id(request.url, "proyectos")
        atras = "./"
        
        if not id_proyecto:
            id_proyecto = UrlParser.parse_id(request.url, "proyectos_fase")
            atras = "../../"
        
        proy = Proyecto.por_id(id_proyecto)
        fase = proy.crear_fase(**kw)
        
        #Creamos el rol miembro  de fase
        #plant_m = Rol.obtener_rol_plantilla(nombre_rol=u"Miembro de Fase")
        #rol_m = Rol.nuevo_rol_desde_plantilla(plantilla=plant_m, 
        #                                      id=fase.id_fase)
        
        flash("Fase Creada")
        redirect(atras)
        
    
    @expose('lpm.templates.fases.edit')
    def edit(self, *args, **kw):
        """Despliega una pagina para realizar modificaciones"""
        id_fase = UrlParser.parse_id(request.url, "fases")
        fase = Fase.por_id(int(id_fase))
        id_proyecto = UrlParser.parse_id(request.url, "proyectos")
        atras = "./"
        if not id_proyecto:
            id_proyecto = UrlParser.parse_id(request.url, "proyectos_fase")
            atras = "../../"
            
        pp = PoseePermiso('modificar fase', id_fase=id_fase)
        if not pp.is_met(request.environ):
            flash(pp.message % pp.nombre_permiso, 'warning')
            redirect("./")
            
        tmpl_context.widget = FaseEditForm(DBSession)
        value = self.edit_filler.get_value(values={'id_fase': id_fase})
        page = u"Modificar Fase: %s" % value["nombre"]
        return dict(value=value,
                    page=page,
                    atras=atras)
 
        
    @validate(fase_edit_form, error_handler=edit)
    @expose()
    def put(self, *args, **kw):
        """update"""
        if "sprox_id" in kw:
            del kw["sprox_id"]
        id_proyecto = int(kw["id_proyecto"])
        id_fase = int(kw["id_fase"])
        del kw["id_fase"]
        pp = PoseePermiso('modificar fase', id_fase=id_fase)
        if not pp.is_met(request.environ):
            flash(pp.message % pp.nombre_permiso, 'warning')
            redirect("../")

        proy = Proyecto.por_id(id_proyecto)
        proy.modificar_fase(id_fase, **kw)
        flash("Fase modificada")
        redirect("./")

    @with_trailing_slash
    @paginate('lista_elementos', items_per_page=5)
    @expose('lpm.templates.fases.get_all')
    @expose('json')
    def get_one(self, *args, **kw):
        id_proyecto = UrlParser.parse_id(request.url, "proyectos")
        action = "./"
        atras = '../'
        if not id_proyecto:
            id_proyecto = UrlParser.parse_id(request.url, "proyectos_fase")
            atras = "/proyectos_fase/"
            
        id_fase = int(args[0])
        puede_crear = PoseePermiso("crear fase", 
                                   id_proyecto=id_proyecto).is_met(request.environ)
        proy = Proyecto.por_id(id_proyecto)
        
        if proy.estado == "Iniciado":
            puede_crear = False
            
        if pylons.request.response_type == 'application/json':
            return dict(lista=self.table_filler.get_value(id_fase=id_fase, **kw))
        if not getattr(self.table.__class__, ' ', False):
            fase = self.table_filler.get_value(id_fase=id_fase, **kw)
        else:
            fase = []
            
        tmpl_context.widget = self.table
        titulo = self.title % proy.nombre
        
        return dict(lista_elementos=fase, 
                    page=titulo,
                    titulo=titulo, 
                    modelo=self.model.__name__, 
                    columnas=self.columnas,
                    opciones=self.opciones,
                    url_action=action,
                    puede_crear=puede_crear,
                    comboboxes=self.comboboxes,
                    atras=atras
                    )
    #}
