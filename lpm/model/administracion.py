# -*- coding: utf-8 -*-

"""
Este módulo contiene las clases del modelo referentes
al B{Módulo de Administración}

@authors:
    - U{Carlos Bellino<mailto:carlosbellino@gmail.com>}
    - U{Nahuel Hernández<mailto:nahuel.11990@gmail.com>}
    - U{Jorge Ramírez<mailto:jorgeramirez1990@gmail.com>}

@since: 1.0
"""
import os
from datetime import datetime

from sqlalchemy import ForeignKey, Column, and_
from sqlalchemy.types import Integer, Unicode, DateTime
from sqlalchemy.orm import relation, backref
from sqlalchemy.exc import IntegrityError

from lpm.model import DeclarativeBase, DBSession, desarrollo, gestconf
from lpm.model.desarrollo import *
from lpm.model.gestconf import *

#import transaction
""" para probar este módulo, pueden usar
    paster shell development.ini
    
    y después escriben 
    execfile("./lpm/tests/models/test_administracion.py")
    que es el archivo en donde probe el módulo.
"""

__all__ = ['Fase', 'Proyecto', 'TipoItem', 'AtributosPorTipoItem']

class Fase(DeclarativeBase):
    """
    Clase que define un Fase de Proyecto.
    """
    __tablename__ = 'tbl_fase'
    
    #{ Columnas
    id_fase = Column(Integer, autoincrement=True, primary_key=True)
    id_proyecto = Column(Integer, ForeignKey('tbl_proyecto.id_proyecto',
                                              ondelete="CASCADE"))
    posicion = Column(Integer, nullable=False)
    nombre = Column(Unicode(32), nullable=False)
    descripcion = Column(Unicode(200), nullable=True)
    numero_items = Column(Integer, nullable=False, default=0)
    numero_lb = Column(Integer, nullable=False, default=0)
    estado = Column(Unicode(20), nullable=True, default=u"Inicial")
    
    #{ Relaciones
    items = relation('Item')
    
    def lineas_bases(self):# este todavía no probé
        return DBSession.query(LB).join(LB.items, ItemsPorLB.propiedad_item).\
                            filter(and_(PropiedadItem.id_item_actual==Item.id_item,
                                        Item.id_fase==self.id_fase)).all()
    #}
    
    def cambiar_estado(self):
        """ La fase puede tener los estados “Inicial”, “Desarrollo”,
         “Completa” y “Comprometida” """
        pass
    
    def crear_item(self):
        pass
    
    def crear_lb(self):
        pass
     

class Proyecto(DeclarativeBase):
    """
    Clase que define un Proyecto que será administrado por el sistema.
    """
    __tablename__ = 'tbl_proyecto'
    
    #{Columnas
    id_proyecto = Column(Integer, autoincrement=True, primary_key=True)
    nombre = Column(Unicode(32), nullable=False, unique=True)
    descripcion = Column(Unicode(200), nullable=False, default=u"Proyecto LPM")
    fecha_creacion = Column(DateTime, nullable=False, default=datetime.now)
    complejidad_total = Column(Integer, nullable=False, default=0)
    estado = Column(Unicode(20), nullable=False, default=u"No Iniciado")
    numero_fases = Column(Integer, nullable=False, default=0)
    
    #{ Relaciones
    fases = relation('Fase')
    tipos_de_item = relation ('TipoItem')
    #}
    
    def iniciar_proyecto(self):
        """ inicia un proyecto, cambia su estado a iniciado """
        print self.estado
        if (self.estado == u"No Iniciado"):
            print "iniciando proyecto"
            self.estado = u"Iniciado"
            
            for f in self.fases:
                tipo = TipoItem()
                tipo.codigo = u"tipo_fase_%d" % f.posicion
                tipo.descripcion = u"tipo por defecto de la fase número %d" % f.posicion
                self.tipos_de_item.append(tipo)
                DBSession.add(tipo)
        
    def crear_fase(self, dict):
        """ Para agregar fases a un proyecto no iniciado
        se le pasa un  diccionario con los atributos para la nueva fase"""
        if (self.estado == u"No Iniciado"):
            print "creando fase"
            self.numero_fases += 1
            fase = Fase()
            fase.posicion = self.numero_fases
            fase.nombre = dict["nombre"]
            fase.descripcion = dict["descripcion"]
            self.fases.append(fase)
            DBSession.add(fase)

    def eliminar_fase(self, id):
        """elimina la fase de id en un proyecto "No Iniciado" """
        """ guarda al probar, está pensado para usarse en un controlador """
        if(self.estado == u"No Iniciado"):
            self.numero_fases -= 1
            fase = DBSession.query(Fase).filter_by(id_fase=id).one()
            posicion = fase.posicion
            DBSession.delete(fase)
            
            #si se elimina una fase que no está al final
            for f in self.fases:
                if (f.posicion > posicion):
                    f.posicion -= 1
                    
    def eliminar(self):
        """ Elimina el proyecto con todo lo asociado, fases, tipos de items """
        DBSession.delete(self)
        
    #creo que esto va acá
    def definir_tipo_item(self, id_papa, id_importado=None, mezclar=False):
        """ id_papa dice de quien hereda la estructura
            importado si se especifica es id del tipo de item proveniente de
            otro proyecto.
            mezclar indica, en caso de que id_importado tenga un valor, si las estructuras del
            padre y del importado se deben mezclar """
        pass


class TipoItem(DeclarativeBase):
    """
    Clase que define las características
    de un tipo de ítem.
    """
    __tablename__ = 'tbl_tipo_item'
    
    #{ Columnas
    id_tipo_item = Column(Integer, autoincrement=True, primary_key=True)
    codigo = Column(Unicode(32), nullable=False)
    descripcion = Column(Unicode(200), nullable=True)
    id_proyecto = Column(Integer, ForeignKey('tbl_proyecto.id_proyecto',
                         ondelete="CASCADE"), nullable=True)
    id_padre = Column(Integer, ForeignKey('tbl_tipo_item.id_tipo_item'))
    
    #{ Relaciones
    
    #tipo_hijo = relation('TipoItem', backref=backref('tipo_padre', remote_side=id_tipo_item))
    atributos = relation('AtributosPorTipoItem')
    items = relation('Item')
    #}
    
    def agregar_atributo(self):
        pass
    
    def modificar_atributo(self, id_atributo, dict):
        pass


class AtributosPorTipoItem(DeclarativeBase):
    """
    Clase que define que atributos posee un determinado
    tipo de ítem.
    """
    __tablename__ = 'tbl_atributos_por_tipo_item'
    
    #{ Columnas
    id_atributos_por_tipo_item = Column(Integer, autoincrement=True, 
                                        primary_key=True)
    nombre = Column(Unicode(32), nullable=False)
    tipo = Column(Unicode(32), nullable=False)
    valor_por_defecto = Column(Unicode(32), nullable=True)
    id_tipo_item = Column(Integer, ForeignKey('tbl_tipo_item.id_tipo_item'))
    #}

