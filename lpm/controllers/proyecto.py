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
from lpm.model import DBSession, Proyecto, Usuario, Rol
from lpm.lib.sproxcustom import (CustomTableFiller, 
                                 CustomPropertySingleSelectField)
from lpm.lib.authorization import PoseePermiso, AlgunPermiso
from lpm.lib.util import UrlParser
from lpm.controllers.fase import FaseController, FaseTableFiller, FaseTable
from lpm.controllers.tipoitem import TipoItemController, TipoItemTableFiller

from sprox.tablebase import TableBase
from sprox.fillerbase import TableFiller, EditFormFiller
from sprox.fillerbase import EditFormFiller
from sprox.formbase import AddRecordForm, EditableForm

from repoze.what.predicates import not_anonymous, is_anonymous, All

import pylons
from pylons import tmpl_context

import transaction

from tw.forms import TextField

class ProyectoTable(TableBase):
    __model__ = Proyecto
    __headers__ = {'id_proyecto': u'ID', 'fecha_creacion': u'Creación',
                   'complejidad_total': u'Compl.', 'estado': u'Estado',
                   'numero_fases': u'#Fases', 'descripcion': u'Descripción',
                   'project_leader': 'Lider', 'codigo': u"Código"
                  }
    __omit_fields__ = ['fases', 'tipos_de_item', 'id_proyecto', 'descripcion']
    __default_column_width__ = '15em'
    __field_order__ = ['codigo', 'nombre', 'numero_fases', 'estado',
                        'project_leader', 'complejidad_total',
                        'fecha_creacion']
    __column_widths__ = {'complejidad_total': "25em",
                         'numero_fases': "35em",
                         '__actions__' : "50em",
                         'codigo': "30em"
                        }
    __field_attrs__ = {'completidad_total': { 'text-aling' : 'center'}}
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

        if PoseePermiso('eliminar proyecto',
                        id_proyecto=obj.id_proyecto).is_met(request.environ):
            value += '<div><form method="POST" action="' + str(obj.id_proyecto) + '" class="button-to">'+\
                     '<input type="hidden" name="_method" value="DELETE" />' +\
                     '<input onclick="return confirm(\'Está seguro?\');" value="Delete" type="submit" '+\
                     'style="background-color: transparent; float:left; border:0; color: #286571;'+\
                     'display: inline; margin: 0; padding: 0;" class="' + clase + '"/>'+\
                     '</form></div><br />'

        if obj.estado == u"No Iniciado":
            if PoseePermiso('iniciar proyecto', 
                        id_proyecto=obj.id_proyecto).is_met(request.environ):
                value += '<div>' + \
                            '<a href="/proyectos/' + str(obj.id_proyecto) + '/iniciar/" ' +\
                            'class="' + clase + '">Iniciar</a>' + \
                         '</div><br />'
        value += '</div>'
        return value
    
    def _do_get_provider_count_and_objs(self, **kw):
        """
        Sobreescribimos este método para poder listar
        solamente los proyectos para los cuales tenemos
        algun permiso.
        """
        count, filtrados = super(ProyectoTableFiller, self). \
                                 _do_get_provider_count_and_objs(**kw)
        if count == 0:
            return count, filtrados
        pks = []
        nombre_usuario = request.credentials['repoze.what.userid']
        usuario = Usuario.by_user_name(nombre_usuario)
        for r in usuario.roles:
            if r.es_rol_sistema():
                for p in r.permisos:
                    if p.nombre_permiso.find("proyecto") > 0 and \
                       p.nombre_permiso != u"consultar proyecto":
                        return count, filtrados
            elif r.id_proyecto != 0 and r.id_proyecto not in pks:
                pks.append(r.id_proyecto)
        c = 0
        while True:
            if filtrados[c].id_proyecto not in pks:
                filtrados.pop(c)
            else:
                c += 1
            if c == len(filtrados):
                break
            
        return len(filtrados), filtrados
    
        if AlgunPermiso(patron="tipo item").is_met(request.environ):
            id_proyecto = UrlParser.parse_id(request.url, "proyectos")
            filtrados = DBSession.query(TipoItem).all()
            if id_proyecto:
                proy = Proyecto.por_id(id_proyecto)
                filtrados = proy.tipos_de_item
            return len(filtrados), filtrados
        return 0, []

proyecto_table_filler = ProyectoTableFiller(DBSession)


class LiderField(CustomPropertySingleSelectField):
    """Dropdown list para líder de proyecto
    al crear por defecto se selecciona el usuario actual"""
    def _my_update_params(self, d, nullable=False):
        options = []
        if self.accion == "edit":
            id_proyecto = UrlParser.parse_id(request.url, "proyectos")
            if id_proyecto:
                proy = Proyecto.por_id(id_proyecto)
                lider = proy.obtener_lider()
                options.append((lider.id_usuario, '%s (%s)'%(lider.nombre_usuario, 
                                lider.nombre + " " + lider.apellido)))
                if (PoseePermiso('asignar-desasignar rol').is_met(request.environ)):
                    usuarios = DBSession.query(Usuario).\
                        filter(Usuario.id_usuario!=lider.id_usuario).all()
                    for u in usuarios:
                        options.append((u.id_usuario, '%s (%s)'%(u.nombre_usuario, 
                        u.nombre + " " + u.apellido)))
                        
        elif self.accion == "new":
            user = Usuario.by_user_name(request.identity['repoze.who.userid'])
            options.append((user.id_usuario, '%s (%s)'%(user.nombre_usuario, 
                        user.nombre + " " + user.apellido)))
            usuarios = DBSession.query(Usuario).\
                filter(Usuario.id_usuario != user.id_usuario).all()
            for u in usuarios:
                options.append((u.id_usuario, '%s (%s)'%(u.nombre_usuario, 
                    u.nombre + " " + u.apellido)))
                    
        d['options'] = options
        return d


class ProyectoAddForm(AddRecordForm):
    __model__ = Proyecto
    __omit_fields__ = ['id_proyecto', 'fecha_creacion', 'complejidad_total',
                       'estado', 'fases', 'tipos_de_item', 'codigo',
                       'numero_fases']
    __field_order__ = ['nombre', 'descripcion']
    __base_validator__ = ProyectoAddFormValidator
    
    if PoseePermiso('asignar-desasignar rol').is_met(request.environ):
        lider = LiderField('lider', label_text="Lider", accion="new")
        __field_order__.append('lider')

proyecto_add_form = ProyectoAddForm(DBSession)


class ProyectoEditForm(EditableForm):
    __model__ = Proyecto
    __hide_fields__ = ['id_proyecto']
    __omit_fields__ = ['fecha_creacion', 'complejidad_total',
                       'estado', 'numero_fases', 'codigo', 'fases', 
                       'tipos_de_item']
    __base_validator__ = ProyectoEditFormValidator
    if PoseePermiso('asignar-desasignar rol').is_met(request.environ):
        lider = LiderField('lider', label_text="Lider", 
                           accion="edit")

proyecto_edit_form = ProyectoEditForm(DBSession)        

class ProyectoEditFiller(EditFormFiller):
    __model__ = Proyecto
    
proyecto_edit_filler = ProyectoEditFiller(DBSession)



    
#tabla_fases_filler = FasesProyectoTableFiller(DBSession)
    
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
    tipositems = TipoItemController(DBSession)
    #{ Modificadores
    model = Proyecto
    table = proyecto_table
    table_filler = proyecto_table_filler
    new_form = proyecto_add_form
    edit_form = proyecto_edit_form
    edit_filler = proyecto_edit_filler
    tabla_fases_filler = None#tabla_fases_filler
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
            return self.table_filler.get_value(**kw)
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
            redirect("/proyectos")

        tmpl_context.widget = self.table
        buscar_table_filler = ProyectoTableFiller(DBSession)
        buscar_table_filler.filtros = kw
        proyectos = buscar_table_filler.get_value()
        atras = '/proyectos'
        
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
    
    
    @expose('lpm.templates.proyecto.edit')
    def edit(self, *args, **kw):
        """Despliega una pagina para realizar modificaciones"""
        '''
        pp = PoseePermiso('modificar proyecto', id_proyecto=args[0])
        if not pp.is_met(request.environ):
            flash(pp.message % pp.nombre_permiso, 'warning')
            redirect("/proyectos")
        '''
        tmpl_context.widget = self.edit_form
        id_proyecto = UrlParser.parse_id(request.url, "proyectos")
        value = self.edit_filler.get_value(values={'id_proyecto': id_proyecto})
        value['_method'] = 'PUT'#?
        if request.environ.get('HTTP_REFERER') == "http://" + request.environ.get('HTTP_HOST',) + "/":
            atras = "../"
        else:
            atras = "/proyectos"
        return dict(value=value, page="Modificar Proyecto", atras=atras)
        
    @without_trailing_slash
    @expose('lpm.templates.proyecto.new')
    def new(self, *args, **kw):
        """Display a page to show a new record."""
        tmpl_context.widget = self.new_form
        if request.environ.get('HTTP_REFERER') == "http://" + request.environ.get('HTTP_HOST',) + "/":
            atras = "../"
        else:
            atras = "/proyectos"
        return dict(value=kw, page="Nuevo Proyecto", atras=atras)    
    
    @validate(proyecto_add_form, error_handler=new)
    @expose()
    def post(self, *args, **kw):
        if "sprox_id" in kw:
            del kw["sprox_id"]
        id_proy_lider = int(kw["lider"])
        del kw["lider"]
        #transaction.begin()
        proy = Proyecto(**kw)
        lider = Usuario.por_id(id_proy_lider)
        nombre_lider = lider.nombre_usuario
        rol_template = Rol.obtener_rol_plantilla(nombre_rol=u"Lider de Proyecto")
        rol_nuevo = Rol(id_fase=0, id_tipo_item=0)
        rol_nuevo.nombre_rol = rol_template.nombre_rol
        rol_nuevo.descripcion = rol_template.descripcion
        rol_nuevo.tipo = u"Proyecto"
        rol_nuevo.usuarios.append(lider)
        for perm in rol_template.permisos:
            perm.roles.append(rol_nuevo)
        DBSession.add_all([proy, rol_nuevo])
        DBSession.flush()
        rol_nuevo.id_proyecto = proy.id_proyecto
        rol_nuevo.codigo = Rol.generar_codigo(rol_nuevo)
        proy.codigo = Proyecto.generar_codigo(proy)
        #transaction.commit()
        
        #después de crear el proyecto, si el usuario actual es el lider
        #se redirige a la interface de administración del nuevo proyecto.
        if (nombre_lider == request.identity['repoze.who.userid']):
            redirect("/proyectos/administrar/%s" % str(proy.id_proyecto))
        else:
            redirect("/proyectos")

    @validate(proyecto_edit_form, error_handler=edit)
    @expose()
    def put(self, *args, **kw):
        """Registra los cambios en la edición de un
        proyecto.
        """
        if "sprox_id" in kw:
            del kw["sprox_id"]
        id_proyecto = UrlParser.parse_id(request.url, "proyectos")
        transaction.begin()
        proy = Proyecto.por_id(id_proyecto)
        proy.nombre = unicode(kw["nombre"])
        proy.descripcion = unicode(kw["descripcion"])
        transaction.commit()
        redirect("../")
    
    @expose('lpm.templates.proyecto.administrar')
    def administrar(self, id_proyecto, *args, **kw):
        """Despliega una pagina para admistrar un proyecto"""

        pp = PoseePermiso('modificar proyecto', id_proyecto=id_proyecto)
        if not pp.is_met(request.environ):
            flash(pp.message % pp.nombre_permiso, 'warning')
            redirect("/proyectos")
        proyecto = Proyecto.por_id(id_proyecto)
        iniciado = (proyecto.estado == u'Iniciado')
        
        puede_crear_fase = (not iniciado and
                            PoseePermiso('crear fase', id_proyecto=id_proyecto).\
                            is_met(request.environ))
        
        puede_crear_ti = (iniciado and
                            PoseePermiso('crear tipo item', id_proyecto=id_proyecto).\
                            is_met(request.environ))
        
        tmpl_context.widget = self.edit_form
        
            
        tmpl_context.tabla_fases = FasesProyectoTableFiller(DBSession)
        tmpl_context.tabla_ti = TiProyectoTableFiller(DBSession)
        
        value = self.edit_filler.get_value(values={'id_proyecto': id_proyecto})
        
        fases = self.fases.get_all()['value']#tabla_fases_filler.get_value()
        tipo_items = self.tipositem.get_all()['value']#self.tabla_ti_filler.get_value()
        
        return dict(value=value,
                    page="Administrar Proyecto %s" % proyecto.nombre,
                    fases=fasas,
                    tipo_items=tipo_items,
                    puede_crear_fase=puede_crear_fases,
                    puede_crear_ti=puede_crear_ti,
                    iniciado=iniciado
                    )
    
    
    @without_trailing_slash
    @paginate('lista_elementos', items_per_page=5)
    @expose('lpm.templates.proyecto.get_all')
    @expose('json')
    def mis_proyectos(self, *args, **kw):
#        ia = is_anonymous()
#        if ia.is_met(request.environ):
#            flash(ia.message, 'warning')
#            redirect("/")
        tmpl_context.widget = self.table
        
        class mp_filler(ProyectoTableFiller):
            """
            TableFiller temporal utilizado para recuperar los proyectos del
            usuario actual.
            """
            def _do_get_provider_count_and_objs(self, **kw):
                count, proys = super(mp_filler, 
                                    self)._do_get_provider_count_and_objs(**kw)
                filtrados = []
                for p in proys:
                    if p.obtener_lider().nombre_usuario == \
                       request.credentials["repoze.what.userid"]:
                        filtrados.append(p)
                return len(filtrados), filtrados
                
        proyectos = mp_filler().get_value(**kw)
        retorno = self.retorno_base()
        retorno["lista_elementos"] = proyectos
        retorno["page"] =  "Mis Proyectos"
        return dict(value=value,
                    page="Administrar Proyecto %s" % proyecto.nombre,
                    fases=fasas,
                    tipo_items=tipo_items,
                    puede_crear_fase=puede_crear_fases,
                    puede_crear_ti=puede_crear_ti,
                    iniciado=iniciado
                    )
    #}
