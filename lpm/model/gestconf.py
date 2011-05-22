# -*- coding: utf-8 -*-

"""
Este módulo contiene las clases del modelo referentes
al B{Módulo de Gestión de Configuración}

Ejemplo de utilización de L{ItemsPorLB}, L{LB} y L{PropiedadItem}::

    lb = LB()
    iplb = ItemsPorLB()
    iplb.propiedad_item = PropiedadItem()
    lb.items.append(iplb)

Iterar sobre los objetos PropiedadItem via ItemsPorLB::

    for iplb in lb.items:
        print iplb.propiedad_item

@authors:
    - U{Carlos Bellino<mailto:carlosbellino@gmail.com>}
    - U{Nahuel Hernández<mailto:nahuel.11990@gmail.com>}
    - U{Jorge Ramírez<mailto:jorgeramirez1990@gmail.com>}

@since: 1.0
"""
import os
from datetime import datetime

from sqlalchemy import ForeignKey, Column
from sqlalchemy.types import Integer, Unicode, DateTime
from sqlalchemy.orm import relation, backref

from lpm.model import *

__all__ = ['LB', 'HistorialLB', 'ItemsPorLB']

class LB(DeclarativeBase):
    """
    Clase que define un Linea Base.
    """
    __tablename__ = 'tbl_lb'
    
    #{ Columnas
    id_lb = Column(Integer, autoincrement=True, primary_key=True)
    numero = Column(Integer, nullable=False)
    estado = Column(Unicode(20), nullable=True, default=u"Cerrada")
    codigo = Column(Unicode(50), unique=True)
    
    # template para codificacion
    tmpl_codigo = u"LB-{id_lb}"
    #{ Relaciones
    items = relation("ItemsPorLB", backref='lb')
    #}
    
    def agregar_item(self, item): #jorge
        """
        Agrega un ítem al conjunto de ítems de la Línea Base
        
        @param item: El ítem a insertar
        @type item: L{Item}
        @raises BloquearItemError: si no se ejecuta con exito L{bloquear}
        """
        item.bloquear()
        iplb = ItemsPorLB()
        iplb.propiedad_item = PropiedadItem.por_id(item.id_propiedad_item)
        self.items.append(iplb)
    
    def romper(self):
        """
        Rompe una linea base
        """
        pass
    
    @classmethod
    def por_id(cls, id):
        """
        Método de clase que realiza las búsquedas por identificador
        de ítem.
        
        @param id: identificador del ítem
        @type id: C{Integer}
        @return: el elemento recuperado
        @rtype: L{ItemsPorLB}
        """
        return DBSession.query(cls).filter_by(id_lb=id).one()




class HistorialLB(DeclarativeBase):
    """
    Clase que define un historial de modificaciones
    hechas sobre los las Líneas Bases.
    """
    __tablename__ = 'tbl_historial_lb'
    
    #{ Columnas
    id_historial_lb = Column(Integer, autoincrement=True, primary_key=True)
    tipo_operacion = Column(Unicode(45), nullable=False)
    fecha_modificacion = Column(DateTime, nullable=False, default=datetime.now)
    id_usuario = Column(Integer, ForeignKey('tg_user.id_usuario',
                                            onupdate="CASCADE", 
                                            ondelete="CASCADE"))
    id_lb = Column(Integer, ForeignKey('tbl_lb.id_lb'))
    
    #{ Relaciones
    usuario = relation("Usuario", backref="historial_lb")
    lb = relation("LB", backref="historial_lb")
    #}
    
    
class ItemsPorLB(DeclarativeBase):
    """
    Clase que define el conjunto de ítems que forman parte
    de una línea base
    """
    __tablename__ = 'tbl_items_por_lb'
    
    #{ Columnas
    id_item_por_lb = Column(Integer, autoincrement=True, primary_key=True)
    id_item = Column(Integer, 
                     ForeignKey('tbl_propiedad_item.id_propiedad_item',
                                onupdate="CASCADE", ondelete="CASCADE"))
    id_lb = Column(Integer, ForeignKey('tbl_lb.id_lb',
                                        onupdate="CASCADE", ondelete="CASCADE"))
    
    #{ Relaciones
    propiedad_item = relation('PropiedadItem', backref='item_lb_assocs')
    #}
    
    @classmethod
    def filter_by_id_item(cls, id):
        """
        Método de clase que realiza las búsquedas por identificador
        de ítem.
        
        @param id: identificador del ítem
        @type id: C{Integer}
        @return: el elemento recuperado
        @rtype: L{ItemsPorLB}
        """
        return DBSession.query(cls).filter_by(id_item=id).one()
