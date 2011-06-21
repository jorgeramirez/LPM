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
from sqlalchemy import desc
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
    tmpl_codigo = u"fase-{posicion}/p-{id_proyecto}"
    estados_posibles = [u'Inicial', u'Desarrollo', u'Completa', 'Comprometida']
    #{ Relaciones
    items = relation('Item', cascade="delete")
    roles = relation('Rol', cascade="delete")
    tipos_de_item = relation('TipoItem', cascade="delete")
    
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

    def crear_item(self, id_tipo, **kw):#todavía no probé
        """ Crear un item en esta fase
            @param id_tipo: el identificador del tipo de ítem
            @param kw: contiene los datos para inicializar su propiedad
        """
        #crear el item
        tipo = TipoItem.por_id(id_tipo)
        self.numero_items += 1
        item = Item()
        item.id_tipo_item = id_tipo
        item.numero = self.numero_items
        item.numero_por_tipo = len(tipo.items) + 1
        item.codigo = Item.generar_codigo(item)
        #su propiedad
        p_item = PropiedadItem()
        p_item.version = 1
        #p_item.complejidad = 5
        #p_item.prioridad = 5
        p_item.complejidad = int(kw["complejidad"])
        p_item.prioridad = int(kw["prioridad"])
        p_item.estado = u"Desaprobado"
        #los atributos de su tipo
        
        for atr in tipo.atributos:
            a_item = AtributosDeItems()
            a_item.id_atributos_por_tipo_item = atr.\
            id_atributos_por_tipo_item
            a_item.valor = atr.valor_por_defecto
                        
            a_por_item = AtributosPorItem()
            a_por_item.atributo = a_item
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
        return cls.tmpl_codigo.format(posicion=fase.posicion,
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
    tmpl_codigo = u"proy-{id_proyecto}"
    estados_posibles = [u'Iniciado', u'No iniciado']
    
    #{ Relaciones
    fases = relation('Fase', cascade="delete")
    tipos_de_item = relation('TipoItem', cascade="delete")
    roles = relation('Rol', cascade="delete")
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
                tipo.codigo = u"ti-base/f-{pos}/p-{id}".format(pos=f.posicion,
                                                               id=self.id_proyecto)
                tipo.nombre = u"Base de Fase %d" % f.posicion
                tipo.descripcion = u"Tipo por defecto de la fase número %d" % f.posicion
                f.tipos_de_item.append(tipo)
                self.tipos_de_item.append(tipo)
                DBSession.add(tipo)
                DBSession.flush()
        
    def crear_fase(self, **kw):
        """ Para agregar fases a un proyecto no iniciado
        se le pasa un  diccionario con los atributos para la nueva fase"""
        if (self.estado == u"No Iniciado"):
            print "Creando fase..."
            self.numero_fases += 1    
            #se inserta en la posicion indicada
            i = int(kw['posicion'])

            ordenado = DBSession.query(Fase).filter_by(id_proyecto=self.id_proyecto).order_by(Fase.posicion.desc())   
            
            for f in ordenado:
                print f.posicion
                if (f.posicion >= i):
                    f.posicion += 1
                    f.codigo = Fase.generar_codigo(f)
                    DBSession.flush()
                           
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
                    f.codigo = Fase.generar_codigo(f)
                    DBSession.flush()
                    
    def eliminar(self):
        """ Elimina el proyecto con todo lo asociado, fases, tipos de items """
        DBSession.delete(self)
        
    def definir_tipo_item(self, id_papa, id_importado=None, mezclar=False, **kw):#todavía no probé
        """ 
            @param id_papa : dice de quien hereda la estructura, el id_fase del papa es el id_fase
            del nuevo item
            @param kw : diccionario que contiene los datos para el nuevo tipo
            @param : importado si se especifica es id del tipo de item proveniente de
            otro proyecto.
            @param : mezclar cuando se repite un nombre en los atributos del tipo de item
            si es True entonces se coloca "import." como prefijo al nombre del
            atributo importado, si es False el atributo en el tipo importado no se
            agrega (sólo queda el del padre) 
        """
        
        papa = TipoItem.por_id(id_papa)
        fase = Fase.por_id(papa.id_fase)
        for hijo in papa.hijos:
            if (hijo.nombre == kw["nombre"]):
                raise NombreTipoItemError()
            
        tipo = TipoItem()  
        #tipo.codigo = kw["codigo"]
        tipo.nombre = kw["nombre"]
        tipo.descripcion = kw["descripcion"]
        fase.tipos_de_item.append(tipo)
        papa.hijos.append(tipo)
        
        if (id_importado):
            importado = TipoItem.por_id(id_importado)
                
            for atr in importado.atributos:
                nuevo_atr = AtributosPorTipoItem()
                nuevo_atr.nombre = atr.nombre
                
                for n in papa.atributos:
                    #si se repite el nombre de atributo se agreaga import. al nombre
                    if (n.nombre == atr.nombre):
                        if (mezclar):
                            nuevo_atr.nombre = "import." + atr.nombre
                            continuar = True
                            break
                        else:
                            continuar = False
                            break

                if (not continuar):#no se agrega este atributo
                    break   
                        
                nuevo_atr.tipo = atr.tipo
                nuevo_atr.valor_por_defecto = atr.valor_por_defecto
                tipo.atributos.append(nuevo_atr)
                DBSession.add(nuevo_atr)
#        else: #Agregado: copiar estructura del padre si no se importa nada
#            for atr in papa.atributos:
#                nuevo_atr = AtributosPorTipoItem()
#                nuevo_atr.nombre = atr.nombre
#                nuevo_atr.tipo = atr.tipo
#                nuevo_atr.valor_por_defecto = atr.valor_por_defecto
#                tipo.atributos.append(nuevo_atr)
#                DBSession.add(nuevo_atr)
        
        self.tipos_de_item.append(tipo)
        DBSession.add(tipo)
        DBSession.flush()
        tipo.codigo = TipoItem.generar_codigo(tipo)
    
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
        
    @classmethod
    def por_nombre(cls, nombre):
        """
        Método de clase que realiza las búsquedas por nombre de 
        proyecto.
        
        @param nomre: nombre del elemento a recuperar
        @type id: C{str}
        @return: el elemento recuperado
        @rtype: L{Proyecto}
        """
        return DBSession.query(cls).filter_by(nombre=nombre).first()
    
    def obtener_lider(self):
        """
        Retorna el lider de este proyecto.
        """
        rol = DBSession.query(Rol).filter(and_( \
                                   Rol.nombre_rol == "Lider de Proyecto", 
                                   Rol.id_proyecto == self.id_proyecto)).first()
        if rol and rol.usuarios:
            return rol.usuarios[0]
        return ""


class TipoItem(DeclarativeBase):
    """
    Clase que define las características
    de un tipo de ítem.
    """
    __tablename__ = 'tbl_tipo_item'
    
    #{ Columnas
    id_tipo_item = Column(Integer, autoincrement=True, primary_key=True)
    codigo = Column(Unicode(50), unique=True)
    nombre = Column(Unicode(50), nullable=False)
    descripcion = Column(Unicode(200), nullable=True)
    id_proyecto = Column(Integer, ForeignKey('tbl_proyecto.id_proyecto',
                                             ondelete="CASCADE"), nullable=True)
    id_fase = Column(Integer, ForeignKey('tbl_fase.id_fase',
                                         ondelete="CASCADE"), nullable=True)
    id_padre = Column(Integer, ForeignKey('tbl_tipo_item.id_tipo_item',
                                          ondelete="CASCADE"), nullable=True)
    
    # template para codificacion
    tmpl_codigo = u"{siglas}-ti-{id}/f-{pos}/p-{proy}"
    #{ Relaciones
    hijos = relation('TipoItem', cascade="delete")
    atributos = relation('AtributosPorTipoItem', cascade="delete")
    items = relation('Item', cascade="delete")
    roles = relation('Rol', cascade="delete")
    #}
    
    @classmethod
    def generar_codigo(cls, tipo):
        """
        Genera el codigo para el elemento pasado como parametro
        """
        words = tipo.nombre.lower().split()
        while words.count("de"):
            words.remove("de")
        siglas = u""
        for w in words:
            siglas += w[0]
        
        #comprobar que las siglas sean únicas.
        query = DBSession.query(TipoItem).filter(TipoItem.codigo.like(siglas + "%"))
        if query.count():
            siglas += str(query.count())
        
        fase = Fase.por_id(tipo.id_fase)
            
        return cls.tmpl_codigo.format(siglas=siglas, id=tipo.id_tipo_item,
                                  pos=fase.posicion, proy=tipo.id_proyecto)

    def es_o_es_hijo(self, id):
        """Verifica si 
        @param id: es este tipo de item o es hijo de ese tipo de ítem"""
        if (self.id_tipo_item == id):
            return True
        
        actual = self
        while (actual.id_padre != None):
            actual = TipoItem.por_id(actual.id_padre)
            if (actual.id_tipo_item == id):
                return True
            
        return False
            
    def agregar_atributo(self, **kw):#todavía no probé
        """ se espera un valor ya verificado
        se lanza una exepcion si se repite en nombre del atributo
        en el tipo de item actual."""
        
        a = AtributosPorTipoItem()
        
        for atr in self.atributos:
            if (atr.nombre == kw["nombre"]):
                raise NombreDeAtributoError()
            
        a.nombre = kw["nombre"]
        a.tipo = kw["tipo"]
        a.valor_por_defecto = kw["valor_por_defecto"]
        self.atributos.append(a)
        DBSession.add(a)
        DBSession.flush()
                   
        #agregar este atributo a los ítems ya creados, no sé si es necesario
        for i in self.items:
            a_item = AtributosDeItems()
            a_item.id_atributos_por_tipo_item = a.\
            id_atributos_por_tipo_item
            a_item.valor = a.valor_por_defecto

            
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
        return DBSession.query(cls).filter_by(id_tipo_item=id).first()

    @classmethod
    def por_nombre(cls, nombre):
        """
        Método de clase que realiza las búsquedas por nombre de 
        Tipo de ÍTem.
        
        @param nomre: nombre del elemento a recuperar
        @type id: C{str}
        @return: el elemento recuperado
        @rtype: L{TipoItem}
        """
        return DBSession.query(cls).filter_by(nombre=nombre).first()

    def puede_eliminarse(self):
        """
        Verifica si el tipo puede eliminarse.
        """
        return (len(self.items) == 0 and self.id_padre != None)


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
        return DBSession.query(cls).filter_by(id_atributos_por_tipo_item=id).one()
    
    def puede_eliminarse(self):
        """
        Verifica si el atributo puede eliminarse.
        """
        tipo = TipoItem.por_id(self.id_tipo_item)
        return len(tipo.items) == 0
        return True

