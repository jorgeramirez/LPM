# -*- coding: utf-8 -*-
"""
Modulo que contiene clases bases que guardan
relacion con el módulo sprox

@authors:
    - U{Carlos Bellino<mailto:carlosbellino@gmail.com>}
    - U{Nahuel Hernández<mailto:nahuel.11990@gmail.com>}
    - U{Jorge Ramírez<mailto:jorgeramirez1990@gmail.com>}

@since: 1.0
"""

from sprox.fillerbase import TableFiller
from sprox.widgets import PropertySingleSelectField

from tw.dojo.selectshuttle import DojoSelectShuttleField
from sprox.widgets import PropertyMixin
from sprox.widgetselector import SAWidgetSelector

from sqlalchemy import and_
from sqlalchemy.sql import func

from lpm.model import DBSession

__all__ = ['CustomTableFiller']

class CustomTableFiller(TableFiller):
    """
    Clase base utilizada para rellenar una tabla.
    Añade la capacidad de filtrado de elementos.
    """
    __filtros = {}

    def get_filtros(self):
        return self.__filtros
        
    def set_filtros(self, filtros):
        """
        Setea los filtros enviados por el formulario de busqueda. 
        Los mismos hay que parsearlos al formato apropiado
        """
        self.__filtros = {}
        #contiene el nombre de la columna
        col_tmp = "filter-type-{i}" 
        #contiene el valor para esa columna.
        val_tmp_txt = "texto-{i}"   
        val_tmp_combo = "combobox-{i}"
        for i in xrange(0, len(filtros) / 2):
            for tmp in [val_tmp_txt, val_tmp_combo]:
                val_key = tmp.format(i=i) #valor del filtro
                _fk = filtros[col_tmp.format(i=i)] #key para self.__filtros
                if filtros.has_key(val_key):
                    if self.__filtros.has_key(_fk):
                        self.__filtros[_fk].append(filtros[val_key])
                    else:
                        self.__filtros[_fk] = [filtros[val_key]]
                    break
    filtros = property(get_filtros, set_filtros)
    
    def _do_get_provider_count_and_objs(self, **kw): #sobreescribimos el método
        """
        Este método define como la consulta a la base de
        datos se debe realizar.
        """
        filtrados = []
        query = DBSession.query(self.__entity__)
        if not self.filtros:
            return query.count, query.all()
        mapper = self.__entity__.__mapper__
        for fil_col, fil_val_list in self.filtros.items(): #filtrado OR
            col = mapper.columns.get(fil_col)
            col_type = col.type.__visit_name__
            res = []
            if col_type == 'integer':
                for i, fvl in enumerate(fil_val_list):
                    fil_val_list[i] = int(fvl)
                res = query.filter(col.in_(fil_val_list)).all()
            elif col_type == 'unicode':
                for fvl in fil_val_list:
                    res.extend(query.filter(col.ilike(fvl)).all())
            filtrados.extend(res)
        filtrados = self.__remover_duplicados(filtrados)
        return len(filtrados), filtrados

    def __remover_duplicados(self, l):
        l2 = []
        for i in l:
            if i not in l2:
                l2.append(i)
        return l2


class CustomPropertySingleSelectField(PropertySingleSelectField):
    """
    Clase que proporciona un combobox. La misma extiende de 
    L{PropertySingleSelectField} y agrega el campo accion
    utilizado para controlar el metodo _my_update_params.
    """
    accion = None
    
    def __init__(self, id=None, parent=None, children=[], **kw):
        if "accion" in kw:
            self.accion = kw["accion"]
            del kw["accion"]
        super(CustomPropertySingleSelectField, self).__init__(id, parent, 
                                                              children, **kw)
    def _my_update_params(self, d, nullable=False):
        """Metodo utilizado para cargar el combobox"""
        #debe sobreescribirse.
        pass

class MultipleSelectDojo(DojoSelectShuttleField, PropertyMixin):
    """
    Clase que proporciona un widget para selección multiple. 
    La misma extiende de 
    L{DojoSelectShuttleField} y L{PropertyMixin} y cambia el template
    utilizado por defecto que no está muy trabajado.
    """
    template = 'lpm.templates.dojo.selectshuttle'
    def update_params(self, d):
        #en este orden no se pierden los selected_options
        super(MultipleSelectDojo, self).update_params(d)
        self._my_update_params(d)

class WidgetSelectorDojo(SAWidgetSelector):
    default_multiple_select_field_widget_type = MultipleSelectDojo


