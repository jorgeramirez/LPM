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
        self.__filtros = filtros

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
        for fil_col, fil_val in self.filtros.items():
            col = mapper.columns.get(fil_col)
            col_type = col.type.__visit_name__
            if col_type == 'integer':
                res = query.filter(col == int(fil_val)).all()
            elif col_type == 'unicode':
                res = query.filter(col.ilike("%" + fil_val + "%")).all()
            elif col_type == 'datetime':
                res = query.filter(col == fil_val).all() #FIXME
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
