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
from tg import session

from sprox.fillerbase import TableFiller
from sprox.widgets import PropertySingleSelectField

from tw.dojo.selectshuttle import DojoSelectShuttleField
from sprox.widgets import PropertyMixin
from sprox.widgetselector import SAWidgetSelector

from sqlalchemy import and_, between
from sqlalchemy.sql import func

from lpm.model import DBSession

__all__ = ['CustomTableFiller']

class CustomTableFiller(TableFiller):
    """
    Clase base utilizada para rellenar una tabla.
    Añade la capacidad de filtrado de elementos.
    """
    __filtros = {}
    cualquiera = ""
    
    def get_filtros(self):
        return self.__filtros
        
    def set_filtros(self, filtros):
        """
        Setea los filtros enviados por el formulario de busqueda.
        Los mismos hay que parsearlos al formato apropiado
        """
        self.__filtros = {}
        self.buscar_enteros = True

        #contaminado código
        if (filtros.has_key('cualquiera')):
            self.cualquiera = filtros['cualquiera']
            try:
                int(self.cualquiera)
            except:
                self.buscar_enteros = False
        else:
            for fil_col, fil_val_list in filtros.items():
                if (not self.__entity__.__mapper__.columns.has_key(fil_col)):
                    continue
                if (type(filtros[fil_col]).__name__ == 'list'):
                    self.__filtros[fil_col] = fil_val_list
                else:
                    self.__filtros[fil_col] = [fil_val_list]

    filtros = property(get_filtros, set_filtros)
    
    def _do_get_provider_count_and_objs(self, order=None, **kw): #sobreescribimos el método
        """
        Este método define como la consulta a la base de
        datos se debe realizar.
        """
        filtrados = []
        query = DBSession.query(self.__entity__)
        mapper = self.__entity__.__mapper__
        res = []
        
# p = " "

        if not self.filtros:
            if (self.cualquiera == ""):
                if (order):
                    return query.count, query.order_by(order).all()
                else:
                    return query.count, query.all()
            
            #contaminando código
            for key in mapper.columns.keys():
                column = mapper.columns.get(key)
                 
# p = p + "/" + str(column) + ":" + column.type.__visit_name__
                if column.type.__visit_name__ == 'unicode':

                    res.extend(query.filter(column.ilike(self.cualquiera + "%")).all())
#                    query = query.filter(column.ilike(self.cualquiera + "%"))
                elif (column.type.__visit_name__ == 'integer' and self.buscar_enteros):
                    entero = int(self.cualquiera)
                    res.extend(query.filter(column.in_([entero])).all())
#                    query = query.filter(column.in_([entero]))
                    
                filtrados.extend(res)
# session["print"] = p
# session.save()
            filtrados = self.__remover_duplicados(filtrados)
            return len(filtrados), filtrados
# p = ""
        for fil_col, fil_val_list in self.filtros.items(): #filtrado OR
            col = mapper.columns.get(fil_col)
            col_type = col.type.__visit_name__
            
# p = p + "/" + str(col) + ":" + col_type
            if col_type == 'integer':
                lista = []
                for i, fvl in enumerate(fil_val_list):
                    try:
                        lista.append(int(fvl))
                    except:
                        continue
                res = query.filter(col.in_(lista)).all()
            elif col_type == 'unicode':
                for fvl in fil_val_list:
                    res.extend(query.filter(col.ilike(fvl)).all())
            elif col_type == 'datetime':
                for i in range(0, len(fil_val_list), 2):
                    date0 = fil_val_list[i]
                    date1 = fil_val_list[i + 1]
                    if (date0 == '' or date1 == ''):
                        continue
                    res.extend(query.filter(col.between(date0, date1)))
                           
            filtrados.extend(res)
# session["print"] = p
# session.save()
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
    css = []
    params = {}
    def update_params(self, d):
        #en este orden no se pierden los selected_options
        super(MultipleSelectDojo, self).update_params(d)
        self._my_update_params(d)

class WidgetSelectorDojo(SAWidgetSelector):
    default_multiple_select_field_widget_type = MultipleSelectDojo


