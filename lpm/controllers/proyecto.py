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
from tg import redirect, request, require, flash, validate

from lpm.model import DBSession, Proyecto, Usuario, Rol
from lpm.lib.sproxcustom import CustomTableFiller
from lpm.lib.authorization import PoseePermiso
from lpm.controllers.fase import FaseController

from sprox.tablebase import TableBase
from sprox.fillerbase import TableFiller, EditFormFiller
from sprox.fillerbase import EditFormFiller
from sprox.formbase import AddRecordForm, EditableForm
from sprox.widgets import PropertySingleSelectField

from repoze.what.predicates import not_anonymous

import pylons
from pylons import tmpl_context

import transaction


class ProyectoTable(TableBase):
    __model__ = Proyecto
    __headers__ = {'id_proyecto': u'ID', 'fecha_creacion': u'Creación',
                   'complejidad_total': u'Complejidad Total', 'estado': u'Estado',
                   'numero_fases': u'Nro. de Fases', 'descripcion': u'Descripción',
                   'project_leader': 'Lider de Proyecto'
                  }
    __omit_fields__ = ['fases', 'tipos_de_item']
    __default_column_width__ = '15em'
    __column_widths__ = {'complejidad_total': "35em",
                         'numero_fases': "35em",
                         '__actions__' : "50em"
                        }
    __add_fields__ = {'project_leader':None}
    
proyecto_table = ProyectoTable(DBSession)


class ProyectoTableFiller(CustomTableFiller):
    __model__ = Proyecto
    __add_fields__ = {'project_leader': None}
    
    def project_leader(self, obj):
        lider = obj.obtener_lider()
        if lider:
            return lider.nombre + " " + lider.apellido + ", " + lider.nombre_usuario
        return None
    
    def __actions__(self, obj):
        """Links de acciones para un registro dado"""
        value = '<div>'
        style = 'text-align:left; margin-top:2px;';
        style += 'font-family:sans-serif; font-size:12;'        
        if PoseePermiso('modificar proyecto', 
                        id_proyecto=obj.id_proyecto).is_met(request.environ):
            value += '<div>' + \
                        '<a href="'+ str(obj.id_proyecto) +'/edit" ' + \
                        'style="' + style + '">Modificar</a>' + \
                     '</div><br />'
        if PoseePermiso('eliminar proyecto',
                        id_proyecto=obj.id_proyecto).is_met(request.environ):
            value += '<div><form method="POST" action="' + str(obj.id_proyecto) + '" class="button-to">'+\
                     '<input type="hidden" name="_method" value="DELETE" />' +\
                     '<input onclick="return confirm(\'Está seguro?\');" value="Delete" type="submit" '+\
                     'style="background-color: transparent; float:left; border:0; color: #286571;'+\
                     'display: inline; margin: 0; padding: 0;' + style + '"/>'+\
                     '</form></div><br />'
        if PoseePermiso('administrar proyecto',
                        id_proyecto=obj.id_proyecto).is_met(request.environ):
            value += '<div>' + \
                        '<a href="' + str(obj.id_proyecto) + '/fases/' +\
                        '" style="' + style + '">Administrar</a>' + \
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

proyecto_table_filler = ProyectoTableFiller(DBSession)


class ProjectLeaderField(PropertySingleSelectField):

    def _my_update_params(self, d, nullable=False):
        usuarios = DBSession.query(Usuario).all()
        options = [(u.id_usuario, '%s (%s)'%(u.nombre_usuario, u.nombre))
                            for u in usuarios]
        d['options'] = options
        return d

class ProyectoAddForm(AddRecordForm):
    __model__ = Proyecto
    __omit_fields__ = ['id_proyecto', 'fecha_creacion', 'complejidad_total',
                       'estado', 'numero_fases', 'fases', 'tipos_de_item']
    __field_order__ = ['nombre', 'descripcion', 'project_leader']
    project_leader = ProjectLeaderField('id_lider')


                                           
proyecto_add_form = ProyectoAddForm(DBSession)


class ProyectoEditForm(EditableForm):
    __model__ = Proyecto
    __omit_fields__ = ['id_proyecto', 'fecha_creacion', 'complejidad_total',
                       'estado', 'numero_fases', 'fases', 'tipos_de_item'
                      ]
    project_leader = ProjectLeaderField('id_lider')

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
    #{ Modificadores
    model = Proyecto
    table = proyecto_table
    table_filler = proyecto_table_filler
    new_form = proyecto_add_form
    edit_form = proyecto_edit_form
    edit_filler = proyecto_edit_filler

    #{ Métodos
    @with_trailing_slash
    @paginate('lista_elementos', items_per_page=7)
    @expose('lpm.templates.get_all')
    @expose('json')
    def get_all(self, *args, **kw):
        """ 
        Retorna todos los registros
        Retorna una página HTML si no se especifica JSON
        """
        if pylons.request.response_type == 'application/json':
            return self.table_filler.get_value(**kw)
        if not getattr(self.table.__class__, '__retrieves_own_value__', False):
            proyectos = self.table_filler.get_value(**kw)
        else:
            proyectos = []
        tmpl_context.widget = self.table
        retorno = self.retorno_base()
        retorno["lista_elementos"] = proyectos
        return retorno

    def retorno_base(self):
        """Retorno basico para buscar() y get_all()"""
        return {"action": self.tmp_action, 
                "page": self.title,
                "titulo": self.title,
                "modelo": self.model.__name__}
                
    @without_trailing_slash
    @paginate('lista_elementos', items_per_page=7)
    @expose('lpm.templates.get_all')
    @expose('json')
    def buscar(self, *args, **kw):
        pp = PoseePermiso('consultar proyecto')
        if not pp.is_met(request.environ):
            flash(pp.message % pp.nombre_permiso, 'warning')
            redirect("/proyectos")
        buscar_table_filler = ProyectoTableFiller(DBSession)
        if kw.has_key('filtro'):
            buscar_table_filler.filtro = kw['filtro']
        proyectos = buscar_table_filler.get_value()
        tmpl_context.widget = self.table
        retorno = self.retorno_base()
        retorno["lista_elementos"] = proyectos
        return retorno
    
    @expose('lpm.templates.edit')
    def edit(self, *args, **kw):
        """Despliega una pagina para modificar proyecto"""
        pp = PoseePermiso('modificar proyecto', id_proyecto=args[0])
        if not pp.is_met(request.environ):
            flash(pp.message % pp.nombre_permiso, 'warning')
            redirect("/proyectos")
        return super(ProyectoController, self).edit(*args, **kw)
        
    @without_trailing_slash
    @expose('lpm.templates.new')
    def new(self, *args, **kw):
        """Display a page to show a new record."""
        tmpl_context.widget = self.new_form
        return dict(value=kw, modelo=self.model.__name__)    
    
    @validate(proyecto_add_form, error_handler=new)
    @expose()
    def post(self, *args, **kw):
        if "sprox_id" in kw:
            del kw["sprox_id"]
        id_proy_lider = int(kw["id_lider"])
        del kw["id_lider"]
        transaction.begin()
        proy = Proyecto(**kw)
        lider = Usuario.por_id(id_proy_lider)
        rol_template = Rol.obtener_template(nombre_rol=u"Lider de Proyecto")
        rol_nuevo = Rol()
        rol_nuevo.nombre_rol = rol_template.nombre_rol + " " + proy.nombre
        rol_nuevo.descripcion = rol_template.descripcion
        rol_nuevo.id_fase = 0
        rol_nuevo.id_tipo_item = 0
        rol_nuevo.usuarios.append(lider)
        for perm in rol_template.permisos:
            perm.roles.append(rol_nuevo)
        DBSession.add(proy)
        DBSession.flush()
        rol_nuevo.id_proyecto = proy.id_proyecto
        DBSession.add(rol_nuevo)
        transaction.commit()
        redirect("./")
    #}
