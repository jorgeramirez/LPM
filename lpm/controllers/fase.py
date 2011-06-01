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
from tg import redirect, request, validate

from lpm.model import DBSession, Fase, Proyecto
from lpm.lib.sproxcustom import (CustomTableFiller,
                                 CustomPropertySingleSelectField)
from lpm.lib.authorization import PoseePermiso
from lpm.lib.util import UrlParser

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
                    'posicion': u'Posicion',
                    'numero_items': u'Nro. de Items', 
                    'estado':u'Estado',
                    'codigo': u'Código'
                  }
    __omit_fields__ = ['items', 'id_proyecto', 'id_fase',
                       'numero_lb', 'descripcion']
    __default_column_width__ = '15em'
    __column_widths__ = { 'descripcion': "35em", '__actions__': "50em"}
    
fase_table = FaseTable(DBSession)


class FaseTableFiller(CustomTableFiller):
    __model__ = Fase

    def __actions__(self, obj):
        """Links de acciones para un registro dado"""
        value = '<div>'
        style = 'text-align:left; margin-top:2px;';
        style += 'font-family:sans-serif; font-size:12;'
        if PoseePermiso('modificar fase', 
                        id_fase=obj.id_fase).is_met(request.environ) or True:
            value += '<div>' + \
                        '<a href="'+ str(obj.id_fase) +'/edit" ' + \
                        'style="' + style + '">Modificar</a>' + \
                     '</div><br />'
        if PoseePermiso('administrar lb',
                        id_fase=obj.id_fase).is_met(request.environ) or True:
            value += '<div>' + \
                        '<a href="'+ str(obj.id_fase) + "/lbs/"\
                        '" style="' + style + '">LBs</a>' + \
                     '</div><br />'
        if PoseePermiso('administrar tipos de item',
                        id_fase=obj.id_fase).is_met(request.environ) or True:
            value += '<div>' + \
                        '<a href="'+ str(obj.id_fase) + "/tipo_items/"\
                        '" style="' + style + '">Tipos de Ítems</a>' + \
                     '</div><br />'
        if PoseePermiso('administrar items',
                        id_fase=obj.id_fase).is_met(request.environ) or True:
            value += '<div>' + \
                        '<a href="'+ str(obj.id_fase) + "/items/"\
                        '" style="'+ style +'">Ítems</a>' + \
                     '</div><br />'
        if PoseePermiso('eliminar fase',
                        id_fase=obj.id_fase).is_met(request.environ) or True:
            value += '<div><form method="POST" action="' + str(obj.id_fase) + '" class="button-to">'+\
                     '<input type="hidden" name="_method" value="DELETE" />' +\
                     '<input onclick="return confirm(\'Está seguro?\');" value="Eliminar" type="submit" '+\
                     'style="background-color: transparent; float:left; border:0; color: #286571; display: inline;'+\
                     'margin: 0; padding: 0;' + style + '"/>'+\
                     '</form></div><br />'
        #administrar lb es simbolico, FIXME, compound predicate checker(?)
        value += '</div>'
        return value

fase_table_filler = FaseTableFiller(DBSession)


class PosicionField(CustomPropertySingleSelectField):
    """
    Dropdown field para las posiciones disponibles
    """
    def _my_update_params(self, d, nullable=False):
        id_proyecto = UrlParser.parse_id(request.url, "proyectos")
        if not id_proyecto: return d
        proy = Proyecto.por_id(id_proyecto)
        pos_usadas, pos_disp, options = [], [], []
        for fase in proy.fases:
            pos_usadas.append(fase.posicion)
        for i in xrange(1, proy.numero_fases + 1):
            if i not in pos_usadas:
                pos_disp.append(i)
        if self.accion == "edit":
            id_fase = UrlParser.parse_id(request.url, "fases")
            if id_fase:
                fase = Fase.por_id(id_fase)
                options.append((fase.posicion, str(fase.posicion)))
        elif self.accion == "new":
            options.append((None, "----------"))
        for pos in pos_disp:
            options.append((pos, str(pos)))
        d['options'] = options
        return d


class FaseAddForm(AddRecordForm):
    __model__ = Fase
    __omit_fields__ = ['id_fase', 'numero_items', 'numero_lb',
                       'estado', 'id_proyecto', 'codigo', 'items']
    posicion = PosicionField("posicion", accion="new")

fase_add_form = FaseAddForm(DBSession)


class FaseEditForm(EditableForm):
    __model__ = Fase
    __hide_fields__ = ['id_fase', 'numero_items', 'numero_lb',
                       'estado', 'codigo', 'id_proyecto', 'items']
    posicion = PosicionField("posicion", accion="edit")

fase_edit_form = FaseEditForm(DBSession)


class FaseEditFiller(EditFormFiller):
    __model__ = Fase

fase_edit_filler = FaseEditFiller(DBSession)


class FaseController(CrudRestController):
    """Controlador de Fases"""
    #{ Variables
    title = u"Administración de Fases"
    allow_only = not_anonymous(u"El usuario debe haber iniciado sesión")
    #{plantillas
    tmp_from_proyecto_action = "/proyectos/%d/fases/buscar"
    tmp_from_proyecto_titulo = "Fases de: %s"
    tmp_action = "/fases/buscar"
    #{ Modificadores
    model = Fase
    table = fase_table
    table_filler = fase_table_filler
    new_form = fase_add_form
    edit_form = fase_edit_form
    edit_filler = fase_edit_filler
    #{ Métodos
    @with_trailing_slash
    @paginate('lista_elementos', items_per_page=5)
    @expose('lpm.templates.get_all')
    @expose('json')
    def get_all(self, *args, **kw):
        """ 
        Retorna todos los registros
        Retorna una página HTML si no se especifica JSON
        """
        retorno = self.retorno_base()
        if not getattr(self.table.__class__, '__retrieves_own_value__', False):
            fases = self.table_filler.get_value(**kw)
        else:
            fases = []
        id_proyecto = UrlParser.parse_id(request.url, "proyectos")
        if id_proyecto:
            #filtramos por el identificador de proyecto.
            if fases:
                self.__reducir(fases, id_proyecto)
            proy = Proyecto.por_id(id_proyecto)
            self.__cambiar_retorno(retorno, proy)
        if pylons.request.response_type == 'application/json':
            return fases
        retorno["lista_elementos"] = fases
        tmpl_context.widget = self.table
        return retorno
    
    def __reducir(self, fases, id_proyecto):
        """Reduce la lista dada, filtrando por id_proyecto"""
        c = 0
        while True:
            if fases[c]['id_proyecto'] != str(id_proyecto):
                fases.pop(c)
            else:
                c += 1
            if c == len(fases):
                break
    
    def retorno_base(self):
        """Retorno basico para buscar() y get_all()"""
        return {"action": self.tmp_action, 
                "page": self.title,
                "titulo": self.title,
                "modelo": self.model.__name__}
    
    def __cambiar_retorno(self, ret, proy):
        """
        Modifica el retorno basico para buscar() y get_all() de manera
        tal a que siga teniendo el url desde donde vinimos.
        """
        ret["action"] = self.tmp_from_proyecto_action % proy.id_proyecto
        ret["titulo"] = self.tmp_from_proyecto_titulo % proy.nombre
        ret["page"] = "Administrar Proyectos"
    
    @without_trailing_slash
    @paginate('lista_elementos', items_per_page=5)
    @expose('lpm.templates.get_all')
    @expose('json')
    def buscar(self, *args, **kw):
        retorno = self.retorno_base()
        buscar_table_filler = FaseTableFiller(DBSession)
        if kw.has_key('filtro'):
            buscar_table_filler.filtro = kw['filtro']
        fases = buscar_table_filler.get_value()
        tmpl_context.widget = self.table
        id_proyecto = UrlParser.parse_id(request.url, "proyectos")
        if id_proyecto:
            #filtramos por el identificador de proyecto.
            id_proyecto = UrlParser.parse_id(request.url, "proyectos")
            if fases:
                self.__reducir(fases, id_proyecto)
            proy = Proyecto.por_id(id_proyecto)
            self.__cambiar_retorno(retorno, proy)
        retorno["lista_elementos"] = fases
        return retorno

    @without_trailing_slash
    @expose('lpm.templates.new')
    def new(self, *args, **kw):
        """Display a page to show a new record."""
        tmpl_context.widget = self.new_form
        return dict(value=kw, modelo=self.model.__name__)
    
    @validate(fase_add_form, error_handler=new)
    @expose()
    def post(self, *args, **kw):
        if "sprox_id" in kw:
            del kw["sprox_id"]
        id_proyecto = UrlParser.parse_id(request.url, "proyectos")
        if id_proyecto:
            transaction.begin()
            proy = Proyecto.por_id(id_proyecto)
            proy.crear_fase(**kw)
            transaction.commit()
        redirect("./")
    #}
