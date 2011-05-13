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

from lpm.model import *
from lpm.model.excepciones import *



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
    
    def cambiar_estado(self): #jorge (falta probar)
        """
        Cambia el estado de la fase. La fase puede estar en uno de 
        los siguientes estados:
            - Inicial
            - Desarrollo
            - Completa
            - Comprometida
        """
        if self.numero_lb == 0:
            self.estado = u"Inicial"
        else:
            items_lb_cerrada = 0
            salir = False
            for lb in self.lineas_bases():
                if lb.estado == u"Cerrada":
                    items_lb_cerrada += len(lb.items)
                elif lb.estado == u"Para-Revisar" and  \
                     self.estado == u"Completa":
                    self.estado = u"Comprometida"
                    salir = True
                    break
                else:
                    self.estado = u"Desarrollo"
                    salir = True
                    break

            if not salir:
                if items_lb_cerrada == len(self.items):
                    proyecto = Proyecto.por_id(self.id_proyecto)
                    ok_completa = True
                    if self.posicion < proyecto.numero_fases:
                        for item in self.items:
                            if len(Relacion.relaciones_como_anterior(item.id_item)) == 0:
                                ok_completa = False
                                self.estado = u"Desarrollo"
                                break
                    if ok_completa:
                        self.estado = u"Completa"
                else:
                    self.estado = u"Desarrollo"

    def crear_item(self, id_tipo):#todavía no probé
        """ Crear un itema en la esta fase
        dict contiene los datos para inicializarlo"""
        #crear el item
        item = Item()
        item.id_tipo_item = id_tipo
        #su propiedad
        p_item = PropiedadItem()
        p_item.version = 1
        p_item.complejidad = 5
        p_item.prioridad = 5
        p_item.estado = u"Desaprobado"
        #los atributos de su tipo
        tipo = TipoItem.por_id(id_tipo)
        
        for atr in tipo.atributos:
            a_item = AtributosDeItems()
            a_item.valor = atr.valor_por_defecto
            a_item.id_atributos_por_tipo_de_item = atr.\
            id_atributos_por_tipo_item
            
            a_por_item = AtributosPorItem()
            a_por_item.atributos = a_item
            p_item.atributos.append(a_por_item)
            DBSession.add(a_item)
            DBSession.add(a_por_item)
                      
        item.propiedad_item_versiones.append(p_item)
        DBSession.add(p_item)
        DBSession.flush()
        
        item.id_propiedad_item = p_item.id_propiedad_item
        self.items.append(item)
        DBSession.add(item)

    def crear_lb(self): #jorge
        """Crea una nueva Línea Base en esta fase"""
        lb_new = LB(numero=self.numero_lb)
        self.numero_lb += 1
        DBSession.add(lb_new)

    @classmethod
    def por_id(cls, id):
        """
        Método de clase que realiza las búsquedas por identificador.
        
        @param id: identificador del elemento a recuperar
        @type id: C{Integer}
        @return: el elemento recuperado
        @rtype: L{Fase}
        """
        return DBSession.query(cls).filter_by(id_fase=id).one()    
     

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

    def modificar_fase(self, id, dict):#todavía no probé
        fase = Fase.por_id(id)
        
        #comprueba si se cambió algo
        if (fase.nombre != dict["nombre"]):
            #comprobar si el nuevo nombre no está repetido
            for f in self.fases:
                if (f.nombre == dict["nombre"]):
                    raise NombreFaseError()
            fase.nombre = dict["nombre"]
            
        if (fase.descripcion != dict["descripcion"]):
            fase.descripcion = dict["descripcion"]
            
        #inserta la fase en esa posicion
        if (fase.posicion != dict["posicion"]):
            for f in self.fases:
                if (fase.posicion < dict["posicion"]):
                    if (f.posicion >= fase.posicion and f.posicion < dict["posicion"]):
                        f.posicion -= 1
                else:
                    if (f.posicion <= fase.posicion and f.posicion > dict["posicion"]):
                        f.posicion += 1
        
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
        
    def definir_tipo_item(self, id_papa, dict, id_importado=None, mezclar=False):#todavía no probé
        """ id_papa dice de quien hereda la estructura
            dict diccionario que contiene los datos para el nuevo tipo
            importado si se especifica es id del tipo de item proveniente de
            otro proyecto.
            mezclar cuando se repite un nombre en los atributos del tipo de item
            si es True entonces se coloca "import." como prefijo al nombre del
            atributo importado, si es False el atributo en el tipo importado no se
            agrega (sólo queda el del padre) """
        
        papa = TipoItem.por_id(id_papa)
        
        for hijo in papa.hijos:
            if (hijo.codigo == dict["codigo"]):
                raise CodigoTipoItemError()
            
        tipo = TipoItem()  
        tipo.codigo = dict["codigo"]
        tipo.descripcion = dict["descripcion"]
        papa.hijos.append(tipo)
        
        if (id_importado):
            importado = TipoItem.por_id(id_importado)
                
            for atr in importado.atributos:
                nuevo_atr = AtributosPorTipoItem()
                nuevo_atr.nombre = atr.nombre
                
                for n in papa.atributos:
                    #si se repite el nombre de atribito se agreaga import. al nombre
                    if (n.nombre == atr.nombre):
                        if (mezclar):
                            nuevo_atr.nombre = "import." + atr.nombre
                            continuar = True
                            break
                        else:
                            continuar = False
                            break

                if (not continuar):#no se agreaga este atributo
                    break   
                        
                nuevo_atr.tipo = atr.tipo
                nuevo_atr.valor_por_defecto = atr.valor_por_defecto
                tipo.atributos.append(nuevo_atr)
                DBSession.add(nuevo_atr)
        
        self.tipos_de_item.append(tipo)
        DBSession.add(tipo)
    
    def eliminar_tipo_item(self, id):
        """ elimina un tipo de item si no hay items de ese tipo creados"""
        tipo = TipoItem.por_id(id)
        if (tipo.items == []):
            DBSession.delete(tipo)
    
    @classmethod
    def por_id(cls, id):
        """
        Método de clase que realiza las búsquedas por identificador.
        
        @param id: identificador del elemento a recuperar
        @type id: C{Integer}
        @return: el elemento recuperado
        @rtype: L{Proyecto}
        """
        return DBSession.query(cls).filter_by(id_proyecto=id).one()      


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
    
    hijos = relation('TipoItem')#, backref=backref('tipo_padre', remote_side=id_tipo_item))
    atributos = relation('AtributosPorTipoItem')
    items = relation('Item')
    #}
    
    def agregar_atributo(self, dict):#todavía no probé
        """ se espera un valor ya verificado
        se lanza una exepcion si se repite en nombre del atributo"""
        a = AtributosPorTipoItem()
        
        for atr in self.atributos:
            if (atr.nombre == dict["nombre"]):
                raise NombreDeAtributoError()
            
        a.nombre = dict["nombre"]
        a.tipo = dict["tipo"]
        a.valor_por_defecto = dict["valor"]
        self.atributos.append(a)
        #DBSession.add(a)
        DBSession.flush()
        
        #agregar este atributo a los ítems ya creados, no sé si es necesario
        for i in self.items:
            a_item = AtributosDeItems()
            a_item.valor = a.valor_por_defecto
            a_item.id_atributos_por_tipo_de_item = a.\
            id_atributos_por_tipo_item
            
            a_por_item = AtributosPorItem()
            a_por_item.atributo = a_item
            p_item = PropiedadItem.por_id(i.id_propiedad_item)
            p_item.atributos.append(a_por_item)
            DBSession.add(a_item)
            DBSession.add(a_por_item)      
 
    def modificar_atributo(self, id_atributo, dict):#todavía no probé
        atributo = AtributosPorTipoItem.por_id(id_atributo)
        
        #comprueba si se cambió algo
        if (atributo.nombre != dict["nombre"]):
            #comprobar si el nuevo nombre no está repetido
            for atr in self.atributos:
                if (atr.nombre == dict["nombre"]):
                    raise NombreDeAtributoError()
            atributo.nombre = dict["nombre"]
            
        if (atributo.tipo != dict["tipo"]):
            #comprobar que no hayan items de ese tipo creados
            if (self.items != []):
                raise TipoAtributoError()
            
            atributo.tipo = dict["tipo"]
            
        if (atributo.valor_por_defecto != dict["valor"]):
            atributo.valor_por_defecto = dict["valor"]

    @classmethod
    def por_id(cls, id):
        """
        Método de clase que realiza las búsquedas por identificador.
        
        @param id: identificador del elemento a recuperar
        @type id: C{Integer}
        @return: el elemento recuperado
        @rtype: L{TipoItem}
        """        
        return DBSession.query(cls).filter_by(id_tipo_item=id).one()


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
    _tipos_permitidos = [u"Numérico", u"Texto", u"Fecha"]
    
    @classmethod
    def por_id(cls, id):
        """
        Método de clase que realiza las búsquedas por identificador.
        
        @param id: identificador del elemento a recuperar
        @type id: C{Integer}
        @return: el elemento recuperado
        @rtype: L{AtributoPorTipoItem}
        """        
        return DBSession.query(cls).filter_by(id_atributo_por_tipo_item=id).one()

