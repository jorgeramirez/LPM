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
from tg.decorators import paginate, expose, with_trailing_slash
from tg import redirect

from lpm.model import DBSession, Fase
from lpm.lib.sproxcustom import BuscarTableFiller

from sprox.tablebase import TableBase
from sprox.fillerbase import TableFiller, EditFormFiller
from sprox.fillerbase import EditFormFiller
from sprox.formbase import AddRecordForm, EditableForm

import pylons
from pylons import tmpl_context


class FaseTable(TableBase):
    __model__ = Fase
    __headers__ = { 'id_fase': u'ID',
                    'nombre': u'Nombre',
                    'posicion': u'Posicion',
                    'numero_items': u'Nro. de Items', 
                    'numero_lb': u'Nro de Linea Base',
                    'estado':u'Estado',
                    'descripcion': u'Descripcion'
                  }
    __omit_fields__ = ['items', 'id_proyecto']
    __default_column_width__ = '15em'
    __column_widths__ = { 'descripcion': "35em" }
    
fase_table = FaseTable(DBSession)

class FaseTableFiller(TableFiller):
    __model__ = Fase

fase_table_filler = FaseTableFiller(DBSession)

class FaseAddForm(AddRecordForm):
    __model__ = Fase
    __omit_fields__ = ['id_fase', 'numero_items', 'numero_lb',
                       'estado']

fase_add_form = FaseAddForm(DBSession)

class FaseEditForm(EditableForm):
    __model__ = Fase
    __omit_fields__ = ['id_fase', 'numero_items', 'numero_lb',
                       'estado']

fase_edit_form = FaseEditForm(DBSession)

class FaseEditFiller(EditFormFiller):
    __model__ = Fase

fase_edit_filler = FaseEditFiller(DBSession)

class FaseBuscarTableFiller(BuscarTableFiller):
    """
    Clase que se utiliza para completar L{FaseTable}
    con el resultado de la búsqueda
    """
    __model__ = Fase

class FaseController(CrudRestController):
    """Controlador de Fases"""
    #{ Variables
    title = u"Administración de Fases"
    #{ Modificadores
    model = Fase
    table = fase_table
    table_filler = fase_table_filler
    new_form = fase_add_form
    edit_form = fase_edit_form
    edit_filler = fase_edit_filler

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
            fases = self.table_filler.get_value(**kw)
        else:
            fases = []
        tmpl_context.widget = self.table
        return dict(modelo=self.model.__name__, 
                    lista_elementos=fases,
                    action='/fases/buscar')

    @with_trailing_slash
    @paginate('lista_elementos', items_per_page=10)
    @expose('lpm.templates.get_all')
    @expose('json')
    def buscar(self, *args, **kw):
        buscar_table_filler = FaseBuscarTableFiller(DBSession)
        if kw.has_key('filtro'):
            buscar_table_filler.filtro = kw['filtro']
        fases = buscar_table_filler.get_value()
        tmpl_context.widget = self.table
        return dict(modelo=self.model.__name__, 
                    lista_elementos=fases,
                    action='/fases/buscar')
    #}
