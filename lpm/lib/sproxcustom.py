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
from lpm.model import DBSession

__all__ = ['BuscarTableFiller']

class BuscarTableFiller(TableFiller):
    """
    Clase Base que se utiliza para completar
    la tabla con el resultado de la búsqueda
    """
    __filtro = None

    def get_filtro(self):
        return self.__filtro
        
    def set_filtro(self, filtro):
        self.__filtro = unicode(filtro)

    filtro = property(get_filtro, set_filtro)

    def _do_get_provider_count_and_objs(self, **kw): #sobreescribimos el método
        """
        Este método define como la consulta a la base de
        datos se debe realizar.
        """
        ## TODO falta verificar y que funcione para distintos
        ## tipos de datos a la hora de buscar
        filtrados = []
        base_query = DBSession.query(self.__model__)
        if not self.__filtro:
            filtrados = base_query.all()
        else:
            mapper = self.__model__.__mapper__
            for key in mapper.columns.keys():
                column = mapper.columns.get(key)
                if column.type.__visit_name__ != 'unicode':
                    continue
                rec = base_query.filter(column.ilike("%" + self.filtro + "%"))
                filtrados.extend(rec)
                filtrados = self.__remover_duplicados(filtrados)
        return len(filtrados), filtrados
    
    def __remover_duplicados(self, l):
        l2 = []
        for i in l:
            if i not in l2:
                l2.append(i)
        return l2
