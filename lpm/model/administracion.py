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
                                             ondelete="CASCADE",
                                             onupdate="CASCADE"))
    codigo = Column(Unicode(50), unique=True)
    posicion = Column(Integer, nullable=False)
    nombre = Column(Unicode(32), nullable=False)
    descripcion = Column(Unicode(200), nullable=True)
    numero_items = Column(Integer, nullable=False, default=0)
    numero_lb = Column(Integer, nullable=False, default=0)
    estado = Column(Unicode(20), nullable=True, default=u"Inicial")

    # template para codificacion
    tmpl_codigo = u"FASE-{id_fase}-PROY-{id_proyecto}"
    estados_posibles = [u'Inicial', u'Desarrollo', u'Completa', 'Comprometida']
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

    @classmethod
    def generar_codigo(cls, fase):
        """
        Genera el codigo para la fase dada como parametro
        """
        return cls.tmpl_codigo.format(id_fase=fase.id_fase,
                                      id_proyecto=fase.id_proyecto)
     

class Proyecto(DeclarativeBase):
    """
    Clase que define un Proyecto que será administrado por el sistema.
    """
    __tablename__ = 'tbl_proyecto'
    
    #{Columnas
    id_proyecto = Column(Integer, autoincrement=True, primary_key=True)
    codigo = Column(Unicode(50), unique=True)
    nombre = Column(Unicode(32), nullable=False, unique=True)
    descripcion = Column(Unicode(200), nullable=False, default=u"Proyecto LPM")
    fecha_creacion = Column(DateTime, nullable=False, default=datetime.now)
    complejidad_total = Column(Integer, nullable=False, default=0)
    estado = Column(Unicode(20), nullable=False, default=u"No Iniciado")
    numero_fases = Column(Integer, nullable=False, default=0)
    
    #template para codificacion
    tmpl_codigo = u"PROY-{id_proyecto}"
    estados_posibles = [u'Iniciado', u'No iniciado']
    
    #{ Relaciones
    fases = relation('Fase')
    tipos_de_item = relation('TipoItem')
    #}

    @classmethod
    def generar_codigo(cls, proy):
        """
        Genera el codigo para el proyecto pasado como parametro
        """
        return cls.tmpl_codigo.format(id_proyecto=proy.id_proyecto)
    
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
        
    def crear_fase(self, **kw):
        """ Para agregar fases a un proyecto no iniciado
        se le pasa un  diccionario con los atributos para la nueva fase"""
        if (self.estado == u"No Iniciado"):
            print "Creando fase..."
            self.numero_fases += 1
            fase = Fase(**kw)
            self.fases.append(fase)            
            DBSession.add(fase)
            DBSession.flush()
            fase.codigo = Fase.generar_codigo(fase)



    def modificar_fase(self, id_fase, **kw):#todavía no probé
        """Modifica los atributos de una fase"""
        fase = Fase.por_id(id_fase)
        
        #comprueba si se cambió algo
        if (fase.nombre != kw["nombre"]):
            #comprobar si el nuevo nombre no está repetido
            for f in self.fases:
                if (f.nombre == kw["nombre"]):
                    raise NombreFaseError()
            fase.nombre = kw["nombre"]
            
        if (fase.descripcion != kw["descripcion"]):
            fase.descripcion = kw["descripcion"]
            
        #inserta la fase en esa posicion
        pos_ini = fase.posicion
        pos_fin = int(kw["posicion"])
        if (fase.posicion != pos_fin):
            if pos_fin < pos_ini:
                for f in self.fases:
                    if f.posicion >= pos_fin and f.posicion < pos_ini:
                        f.posicion += 1
            elif pos_fin > pos_ini:
                for f in self.fases:
                    if f.posicion > pos_ini and f.posicion <= pos_fin:
                        f.posicion -= 1
            fase.posicion = pos_fin
        
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
        """ @param id_papa : dice de quien hereda la estructura
            @param dict diccionario que contiene los datos para el nuevo tipo
            @param importado si se especifica es id del tipo de item proveniente de
            otro proyecto.
            @param mezclar cuando se repite un nombre en los atributos del tipo de item
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
    
    def obtener_lider(self):
        """
        Retorna el lider de este proyecto.
        """
        rol = DBSession.query(Rol).filter(and_( \
                                   Rol.nombre_rol == "Lider de Proyecto", 
                                   Rol.id_proyecto == self.id_proyecto)).first()
        if rol:
            return rol.usuarios[0]
        return None


class TipoItem(DeclarativeBase):
    """
    Clase que define las características
    de un tipo de ítem.
    """
    __tablename__ = 'tbl_tipo_item'
    
    #{ Columnas
    id_tipo_item = Column(Integer, autoincrement=True, primary_key=True)
    codigo = Column(Unicode(50), unique=True)
    nombre = Column(Unicode(50), unique=True, nullable=False)
    descripcion = Column(Unicode(200), nullable=True)
    id_proyecto = Column(Integer, ForeignKey('tbl_proyecto.id_proyecto',
                         ondelete="CASCADE"), nullable=True)
    id_padre = Column(Integer, ForeignKey('tbl_tipo_item.id_tipo_item'))
    
    # template para codificacion
    tmpl_codigo = u"TI-{id_tipo_item}-PROY-{id_proyecto}"
    #{ Relaciones
    hijos = relation('TipoItem')
    atributos = relation('AtributosPorTipoItem')
    items = relation('Item')
    #}
    
    @classmethod
    def generar_codigo(cls, ti):
        """
        Genera el codigo para el elemento pasado como parametro
        """
        return cls.tmpl_codigo.format(id_tipo_item=ti.id_tipo_item,
                                      id_proyecto=ti.id_proyecto)    
    
    def agregar_atributo(self, **kw):#todavía no probé
        """ se espera un valor ya verificado
        se lanza una exepcion si se repite en nombre del atributo"""
        a = AtributosPorTipoItem()
        
        for atr in self.atributos:
            if (atr.nombre == kw["nombre"]):
                raise NombreDeAtributoError()
            
        a.nombre = kw["nombre"]
        a.tipo = kw["tipo"]
        a.valor_por_defecto = kw["valor_por_defecto"]
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
 
    def modificar_atributo(self, id_atributo, **kw):#todavía no probé
        atributo = AtributosPorTipoItem.por_id(id_atributo)
        
        #comprueba si se cambió algo
        if (atributo.nombre != kw["nombre"]):
            #comprobar si el nuevo nombre no está repetido
            for atr in self.atributos:
                if (atr.nombre == kw["nombre"]):
                    raise NombreDeAtributoError()
            atributo.nombre = kw["nombre"]
            
        if (atributo.tipo != kw["tipo"]):
            #comprobar que no hayan items de ese tipo creados
            if (self.items != []):
                raise TipoAtributoError()
            
            atributo.tipo = kw["tipo"]
            
        if (atributo.valor_por_defecto != kw["valor_por_defecto"]):
            atributo.valor_por_defecto = kw["valor_por_defecto"]

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
    
    def puede_eliminarse(self):
        """
        Verifica si el atributo puede eliminarse.
        """
        tipo_item = TipoItem.por_id(self.id_tipo_item)
        return len(tipo_item.items)

