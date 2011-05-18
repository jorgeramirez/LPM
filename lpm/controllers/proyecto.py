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
from tg import redirect, request

from lpm.model import DBSession, Proyecto
from lpm.lib.sproxcustom import BuscarTableFiller
from lpm.lib.authorization import PoseePermiso

from sprox.tablebase import TableBase
from sprox.fillerbase import TableFiller, EditFormFiller
from sprox.fillerbase import EditFormFiller
from sprox.formbase import AddRecordForm, EditableForm

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


class ProyectoTableFiller(TableFiller):
    __model__ = Proyecto

    def __actions__(self, obj):
        """Links de acciones para un registro dado"""
        value = '<div>'
        if PoseePermiso('modificar proyecto', 
           id_proyecto=obj.id_proyecto).is_met(request.environ):
            value += '<div>' + \
                        '<a class="edit_link" href="'+ str(obj.id_proyecto) +'/edit" ' + \
                        'style="text-decoration:none">editar</a>' + \
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
        
proyecto_table_filler = ProyectoTableFiller(DBSession)


class ProyectoAddForm(AddRecordForm):
        __model__ = Proyecto
        __omit_fields__ = ['id_proyecto', 'fecha_creacion', 'complejidad_total',
                                           'estado', 'numero_fases']
                                           
proyecto_add_form = ProyectoAddForm(DBSession)


class ProyectoEditForm(EditableForm):
        __model__ = Proyecto
        __omit_fields__ = ['id_proyecto', 'fecha_creacion', 'complejidad_total',
                                           'estado', 'numero_fases']
                                           
proyecto_edit_form = ProyectoEditForm(DBSession)        


class ProyectoEditFiller(EditFormFiller):
        __model__ = Proyecto
        
proyecto_edit_filler = ProyectoEditFiller(DBSession)


class ProyectoBuscarTableFiller(BuscarTableFiller):
        """
        Clase que se utiliza para completar L{ProyectoTable}
        con el resultado de la búsqueda
        """
        __model__ = Proyecto


class ProyectoController(CrudRestController):
    """Controlador de Proyectos"""
    #{ Variables
    title = u"Administración de Proyectos"

    #{ Modificadores
    model = Proyecto
    table = proyecto_table
    table_filler = proyecto_table_filler
    new_form = proyecto_add_form
    edit_form = proyecto_edit_form
    edit_filler = proyecto_edit_filler

    #{ Métodos
    @with_trailing_slash
    @paginate('lista_elementos', items_per_page=10)
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
            action='/proyectos/buscar')
        
    @with_trailing_slash
    @paginate('lista_elementos', items_per_page=10)
    @expose('lpm.templates.get_all')
    @expose('json')
    def buscar(self, *args, **kw):
        buscar_table_filler = ProyectoBuscarTableFiller(DBSession)
        if kw.has_key('filtro'):
            buscar_table_filler.filtro = kw['filtro']
            proyectos = buscar_table_filler.get_value()
            tmpl_context.widget = self.table
            return dict(modelo=self.model.__name__, 
                    lista_elementos=proyectos,
                    action='/proyectos/buscar')
    #}
