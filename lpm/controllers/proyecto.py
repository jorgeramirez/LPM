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
from tg.decorators import paginate, expose, with_trailing_slash
from tg import redirect, request, require, flash

from lpm.model import DBSession, Proyecto, Usuario
from lpm.lib.sproxcustom import CustomTableFiller
from lpm.lib.authorization import PoseePermiso

from sprox.tablebase import TableBase
from sprox.fillerbase import TableFiller, EditFormFiller
from sprox.fillerbase import EditFormFiller
from sprox.formbase import AddRecordForm, EditableForm

from repoze.what.predicates import not_anonymous

import pylons
from pylons import tmpl_context


class ProyectoTable(TableBase):
    __model__ = Proyecto
    __headers__ = {'id_proyecto': u'ID', 'fecha_creacion': u'Creación',
                   'complejidad_total': u'Complejidad Total', 'estado': u'Estado',
                   'numero_fases': u'Nro. de Fases', 'descripcion': u'Descripción',
                  }
    __omit_fields__ = ['fases', 'tipos_de_item']
    __default_column_width__ = '15em'
    __column_widths__ = {'complejidad_total': "35em",
                         'numero_fases': "35em",
                        }
    
proyecto_table = ProyectoTable(DBSession)


class ProyectoTableFiller(CustomTableFiller):
    __model__ = Proyecto

    def __actions__(self, obj):
        """Links de acciones para un registro dado"""
        value = '<div>'
        if PoseePermiso('modificar proyecto', 
                        id_proyecto=obj.id_proyecto).is_met(request.environ):
            value += '<div>' + \
                        '<a class="edit_link" href="'+ str(obj.id_proyecto) +'/edit" ' + \
                        'style="text-decoration:none">Modificar Proyecto</a>' + \
                     '</div>'
        if PoseePermiso('eliminar proyecto',
                        id_proyecto=obj.id_proyecto).is_met(request.environ):
            value += '<div><form method="POST" action="' + str(obj.id_proyecto) + '" class="button-to">'\
                     '<input type="hidden" name="_method" value="DELETE" />' \
                     '<input class="delete-button" onclick="return confirm(\'Está seguro?\');" value="delete" type="submit" '\
                     'style="background-color: transparent; float:left; border:0; color: #286571; display: inline; margin: 0; padding: 0;"/>'\
                     '</form></div>'
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
        filtrar = True
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


class ProyectoAddForm(AddRecordForm):
    __model__ = Proyecto
    __omit_fields__ = ['id_proyecto', 'fecha_creacion', 'complejidad_total',
                                       'estado', 'numero_fases']
                                           
proyecto_add_form = ProyectoAddForm(DBSession)


class ProyectoEditForm(EditableForm):
    __model__ = Proyecto
    __omit_fields__ = ['id_proyecto', 'fecha_creacion', 'complejidad_total',
                       'estado', 'numero_fases'
                      ]
                                           
proyecto_edit_form = ProyectoEditForm(DBSession)        


class ProyectoEditFiller(EditFormFiller):
    __model__ = Proyecto

proyecto_edit_filler = ProyectoEditFiller(DBSession)


class ProyectoController(CrudRestController):
    """Controlador de Proyectos"""
    #{ Variables
    title = u"Administración de Proyectos"
    # No permitir usuarios anonimos (?)
    allow_only = not_anonymous(u"El usuario debe haber iniciado sesión")
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
        return dict(modelo=self.model.__name__, 
            lista_elementos=proyectos,
            action='/proyectos/buscar',
            page=u'Administrar Proyectos')
        
    @with_trailing_slash
    @paginate('lista_elementos', items_per_page=7)
    @expose('lpm.templates.get_all')
    @expose('json')
    def buscar(self, *args, **kw):
        pp = PoseePermiso('consultar proyecto')
        if not pp.is_met(request.environ):
            flash(pp.message % pp.nombre_permiso)
            redirect("/proyectos")
        buscar_table_filler = ProyectoTableFiller(DBSession)
        if kw.has_key('filtro'):
            buscar_table_filler.filtro = kw['filtro']
            proyectos = buscar_table_filler.get_value()
            tmpl_context.widget = self.table
            return dict(modelo=self.model.__name__, 
                    lista_elementos=proyectos,
                    action='/proyectos/buscar',
                    page=u'Administrar Proyectos')
    
    @expose('lpm.templates.edit')
    def edit(self, *args, **kw):
        """Despliega una pagina para modificar proyecto"""
        pp = PoseePermiso('modificar proyecto', id_proyecto=args[0])
        if not pp.is_met(request.environ):
            flash(pp.message % pp.nombre_permiso)
            redirect("/proyectos")
        return super(ProyectoController, self).edit(*args, **kw)
    #}
