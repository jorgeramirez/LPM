# -*- coding: utf-8 -*-

"""
Este módulo contiene las clases del modelo referentes
al B{Módulo de Desarrollo}

Ejemplo de utilización de L{PropiedadItem}, L{RelacionPorItem} y L{Relacion}::
    pi = PropiedadItem()
    rpi = RelacionPorItem()
    rpi.relacion = Relacion()
    pi.relaciones.append(rpi)

Iterar sobre los objetos Relacion via RelacionPorItem::
    for rpi in pi.relaciones:
        print rpi.revisar
        print rpi.relacion

@authors:
    - U{Carlos Bellino<mailto:carlosbellino@gmail.com>}
    - U{Nahuel Hernández<mailto:nahuel.11990@gmail.com>}
    - U{Jorge Ramírez<mailto:jorgeramirez1990@gmail.com>}

@since: 1.0
"""
import os
from datetime import datetime

from sqlalchemy import ForeignKey, Column, and_
from sqlalchemy.types import Integer, Unicode, Boolean, LargeBinary, DateTime
from sqlalchemy.orm import relation, synonym, backref

from lpm.model import *
from lpm.model.excepciones import *



__all__ = ['Item', 'PropiedadItem', 'RelacionPorItem',
           'Relacion', 'AtributosDeItems', 'ArchivosExternos',
            'ArchivosPorItem', 'HistorialItems', 'AtributosPorItem']


class Item(DeclarativeBase):
    """
    Clase que representa al Item en su versión
    actual
    """
    __tablename__ = 'tbl_item'
    
    #{ Columnas
    id_item = Column(Integer, autoincrement=True, primary_key=True)
    numero = Column(Integer, nullable=False)
    numero_por_tipo = Column(Integer, nullable=False)
    id_tipo_item = Column(Integer,
                          ForeignKey('tbl_tipo_item.id_tipo_item'),
                          nullable=False)
    id_fase = Column(Integer, ForeignKey('tbl_fase.id_fase', ondelete="CASCADE"),
                     nullable=False)
    id_propiedad_item = Column(Integer)

    

    #{ Relaciones
    propiedad_item_versiones = relation('PropiedadItem')
    
    #}
    
    def aprobar(self): #jorge (falta probar)
        """
        Aprueba un ítem.
        
        Las transiciones de estado pueden ser:
            - Revisión-Desbloq al de Aprobado
            - Desaprobado al de Aprobado
        
        @raises CondicionAprobarError: No cumple las condiciones de 
            aprobación del ítem
        """
        p_item = PropiedadItem.por_id(self.id_propiedad_item)
        fase = Fase.por_id(self.id_fase)
        anteriores_count = DBSession.query(Relacion).filter_by( \
            id_posterior=self.id_item).count()
        
        if fase.posicion > 1 and anteriores_count == 0:
            raise CondicionAprobarError( \
                u"El ítem debe tener al menos un antecesor o padre")
                        
        for rel in p_item.relaciones:
            if rel.id_anterior == self.id_item: 
                continue
            item_ant = Item.por_id(rel.id_anterior)
            p_item_ant = PropiedadItem.por_id(item_ant.id_propiedad_item)
            iplb = ItemsPorLB.filter_by_id_item(p_item_ant.id_propiedad_item)
            if iplb.lb.estado != u"Cerrada":
                raise CondicionAprobarError( \
                    "Todos los antecesores y padres " + 
                    "deben estar en una LB cerrada")
        
        if p_item.estado == u"Desaprobado":
            for rel in p_item.relaciones:
                if rel.id_anterior != self.id_item:
                    id = rel.id_anterior
                else:
                    id = rel.id_posterior
                item_rel = Item.por_id(id)
                item_rel.revisar(self.id_item)
                    
        p_item.estado = u"Aprobado"
        DBSession.add(p_item)

    def desaprobar(self): 
        pass
    
    def bloquear(self): #jorge
        """
        Bloquea un ítem, lo que implica que el mismo no puede
        ser modificado.
        
        @raises BloquearItemError: el estado del L{Item} es distinto al 
            de aprobado
        """
        p_item = PropiedadItem.por_id(self.id_propiedad_item)
        if p_item.estado != u"Aprobado":
            raise BloquearItemError()
        p_item.estado = u"Bloqueado"
        DBSession.add(p_item)
            
    def desbloquear(self):
        pass
    
    def revisar(self, id_origen):#nahuel
        """id_origen es el id de un Item desde el que se produjo el cambio """
        pass
    
    def eliminar(self): #jorge
        """
        Elimina un ítem
        """
        p_item = PropiedadItem.por_id(self.id_propiedad_item)
        p_item.estado = u"Eliminado"
        DBSession.add(p_item)
    
    def revivir(self):
        pass
    
    def modificar(self, dict):
        """ se le pasa un diccionario y con los nuevos valores y se compara con los actuales
        para ver que cambió para colocar en el historial """
        pass
    
    def _crear_propiedad_item(self):
        """ ayuda a modificar() """
        pass
    
    def revertir(self, version):
        pass
    
    def calcular_impacto(self):
        pass
    
    @classmethod
    def por_id(cls, id):
        """
        Método de clase que realiza las búsquedas por identificador.
        
        @param id: identificador del elemento a recuperar
        @type id: C{Integer}
        @return: el elemento recuperado
        @rtype: L{Item}
        """
        return DBSession.query(cls).filter_by(id_item=id).one()    

class PropiedadItem(DeclarativeBase):
    """
    Clase que contiene los atributos básicos de 
    un L{Item}
    """
    __tablename__ = 'tbl_propiedad_item'
    
    #{ Columnas
    id_propiedad_item = Column(Integer, autoincrement=True, primary_key=True)
    version = Column(Integer, nullable=False)
    complejidad = Column(Integer, nullable=False)
    prioridad = Column(Integer, nullable=False)
    estado = Column(Unicode(20), nullable=False)
    id_item_actual = Column(Integer, ForeignKey('tbl_item.id_item',
                            ondelete = "CASCADE"))
    
    #{ Relaciones
    relaciones = relation('RelacionPorItem')
    archivos = relation('ArchivosPorItem')
    atributos = relation('AtributosPorItem')
    #}
    
    def modificar_atributo(self):
        pass
    
    def agregar_relacion(self):#nahuel
        pass
    
    def eliminar_relacion(self):#nahuel
        pass
    
    @classmethod
    def por_id(cls, id):
        """
        Método de clase que realiza las búsquedas por identificador.
        
        @param id: identificador del elemento a recuperar
        @type id: C{Integer}
        @return: el elemento recuperado
        @rtype: L{PropiedadItem}
        """
        return DBSession.query(cls).filter_by(id_propiedad_item=id).one()
    

        
class RelacionPorItem(DeclarativeBase):
    """
    Clase que asocia los ítems con sus relaciones
    """
    __tablename__ = 'tbl_relacion_por_item'
    
    #{Columnas
    id_relacion_por_item = Column(Integer, autoincrement=True, 
                                  primary_key=True)
    id_propiedad_item = Column(Integer, 
                               ForeignKey('tbl_propiedad_item.id_propiedad_item',
                               ondelete="CASCADE"))
    id_relacion = Column(Integer, ForeignKey('tbl_relacion.id_relacion',
                         ondelete="CASCADE"))
    revisar = Column(Boolean, nullable=False, default=False)
   
    #{ Relaciones
    relacion = relation("Relacion")
    #}


class Relacion(DeclarativeBase):
    """
    Clase que define una relación entre ítems.
    """
    __tablename__ = 'tbl_relacion'
    
    #{ Columnas
    id_relacion = Column(Integer, autoincrement=True, primary_key=True)
    tipo = Column(Unicode(45), nullable=False)

    id_anterior = Column(Integer, ForeignKey('tbl_item.id_item'))
    id_posterior = Column(Integer, ForeignKey('tbl_item.id_item'))
    
    #{ Métodos de clase
    @classmethod
    def relaciones_como_posterior(cls, id_item):
        """
        Recupera las relaciones en las que el ítem esta como
        hijo o sucesor, dependiendo del tipo de relación
        de ítem dado.
        
        @param id: el identificador del ítem hijo o sucesor
        @type id: C{Integer}
        @return: las relaciones
        @rtype: L{Relacion}
        """
        return DBSession.query(cls).filter_by(id_posterior=id_item).all()

    @classmethod
    def relaciones_como_anterior(cls, id_item):
        """
        Recupera las relaciones en las que el ítem esta como
        padre o antecesor, dependiendo del tipo de relación
        de ítem dado.
        
        @param id: el identificador del ítem padre o antecesor
        @type id: C{Integer}
        @return: las relaciones
        @rtype: L{Relacion}
        """
        DBSession.query(cls).filter_by(id_anterior=id_item).all()
    #}

    
class AtributosDeItems(DeclarativeBase):
    """
    Clase que define el valor para un atributo del item. Dicho atributo
    forma parte del conjunto de atributos del L{TipoItem}.
    """
    __tablename__ = 'tbl_atributos_de_items'
    
    #{ Columnas
    id_atributos_de_items = Column(Integer, 
                                   autoincrement=True, primary_key=True)
    id_atributos_por_tipo_item = Column(Integer,
        ForeignKey('tbl_atributos_por_tipo_item.id_atributos_por_tipo_item'),
        nullable=False,)
    _valor = Column(Unicode(200), nullable=False)
    
    def _get_valor(self):
        """ dependiendo del tipo retorna un valor"""
        pass
    
    def _set_valor(self, valor):
        """ dependiendo del tipo del valor, verifica que sea válido,
         si no lanza una excepción (?) """
        pass
    
    valor = synonym('_valor', descriptor=property(_get_valor, _set_valor))
    
    #}


class AtributosPorItem(DeclarativeBase):
    """
    Clase que asocia un ítem con sus atributos
    """
    __tablename__ = 'tbl_atributos_por_item'
    
    #{ Columnas
    id_atributos_por_item = Column(Integer, autoincrement=True, 
                                   primary_key=True)
    id_propiedad_item = Column(Integer,
        ForeignKey('tbl_propiedad_item.id_propiedad_item'))
    id_atributos_de_items = Column(Integer,
        ForeignKey('tbl_atributos_de_items.id_atributos_de_items'))

    #{ Relaciones
    atributos = relation("AtributosDeItems")
    #}
    
    def modificar_atributo(self, id, valor):
        pass


class ArchivosExternos(DeclarativeBase):
    """
    Clase que representa un archivo externo que puede ser adjuntado a un
    L{Item}
    """
    __tablename__ = 'tbl_archivos_externos'
    
    #{ Columnas
    id_archivo_externo = Column(Integer, autoincrement=True, primary_key=True)
    archivo = Column(LargeBinary(2048), nullable=False)
    nombre_archivo = Column(Unicode(50), nullable=False)
    #}


class ArchivosPorItem(DeclarativeBase):
    """
    Clase que asocia un ítem con sus archivos externos
    """
    __tablename__ = 'tbl_archivos_por_item'
    
    #{ Columnas
    id_archivos_por_item = Column(Integer, autoincrement=True, primary_key=True)
    id_propiedad_item = Column(Integer, 
        ForeignKey('tbl_propiedad_item.id_propiedad_item'))  #parte izquierda de la relación
    id_archivo_externo = Column(Integer,
        ForeignKey('tbl_archivos_externos.id_archivo_externo')) #parte derecha de la relación
    
    #{ Relaciones
    archivos = relation("ArchivosExternos")
    #} 
    
    def agregar_archivo(self):
        pass


class HistorialItems(DeclarativeBase):
    """
    Clase que define un historial de modificaciones
    hechas sobre los ítems.
    """
    __tablename__ = 'tbl_historial_item'
    
    #{ Columnas
    id_historial_items = Column(Integer, autoincrement=True, primary_key=True)
    tipo_modificacion = Column(Unicode(45), nullable=False)
    fecha_modificacion = Column(DateTime, nullable=False, default=datetime.now)
    id_usuario = Column(Integer, ForeignKey('tg_user.id_usuario'))
    id_item = Column(Integer, 
        ForeignKey('tbl_propiedad_item.id_propiedad_item'))
    
    #{ Relaciones
    usuario = relation("Usuario", backref="historial_item")
    #}
   
    
    
