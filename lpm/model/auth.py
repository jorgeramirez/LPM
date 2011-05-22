# -*- coding: utf-8 -*-
"""
Auth* related model.

This is where the models used by :mod:`repoze.who` and :mod:`repoze.what` are
defined.

It's perfectly fine to re-use this definition in the LPM application,
though.

"""
import os
from datetime import datetime
import sys
try:
    from hashlib import sha1
except ImportError:
    sys.exit('ImportError: No module named hashlib\n'
             'If you are on python2.4 this library is not part of python. '
             'Please install it. Example: easy_install hashlib')

from sqlalchemy import Table, ForeignKey, Column, and_
from sqlalchemy.types import Unicode, Integer, DateTime
from sqlalchemy.orm import relation, synonym

from lpm.model import DeclarativeBase, metadata, DBSession

__all__ = ['Usuario', 'Rol', 'Permiso']


#{ Association tables


# This is the association table for the many-to-many relationship between
# groups and permissions. This is required by repoze.what.
group_permission_table = Table('tg_group_permission', metadata,
    Column('id_rol', Integer, ForeignKey('tg_group.id_rol',
        onupdate="CASCADE", ondelete="CASCADE"), primary_key=True),
    Column('id_permiso', Integer, ForeignKey('tg_permission.id_permiso',
        onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)
)

# This is the association table for the many-to-many relationship between
# groups and members - this is, the memberships. It's required by repoze.what.
user_group_table = Table('tg_user_group', metadata,
    Column('id_usuario', Integer, ForeignKey('tg_user.id_usuario',
        onupdate="CASCADE", ondelete="CASCADE"), primary_key=True),
    Column('id_rol', Integer, ForeignKey('tg_group.id_rol',

        onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)
)


#{ The auth* model itself


class Rol(DeclarativeBase):
    """
    Group definition for :mod:`repoze.what`.

    Only the ``group_name`` column is required by :mod:`repoze.what`.
    Pero se usa un 'translation' a "nombre_rol" y "usuarios"
    """

    __tablename__ = 'tg_group'

    #{ Columns

    id_rol = Column(Integer, autoincrement=True, primary_key=True)
    codigo = Column(Unicode(50), unique=True)
    nombre_rol = Column(Unicode(70), nullable=False)
    descripcion = Column(Unicode(100))
    creado = Column(DateTime, default=datetime.now)
    #template para el codigo (usar metodo format)
    tmpl_codigo = "ROL-{id_rol}-{tipo}"
    #Para relacionar un rol con un recurso específico
    id_proyecto = Column(Integer)
    
    id_fase = Column(Integer)
    
    id_tipo_item = Column(Integer)

    #{ Relations

    usuarios = relation('Usuario', secondary=user_group_table, backref='roles')

    #{ Special methods

    def __repr__(self):
        return ('<Rol: name=%s>' % self.nombre_rol).encode('utf-8')

    def __unicode__(self):
        return self.nombre_rol

    def es_rol_sistema(self):
        """
        Indica si el rol es un rol a nivel de sistema.
        @return: True en caso de ser un rol de sistema, sino False
        @rtype: C{bool}
        """
        return (self.id_proyecto + self.id_fase + self.id_tipo_item) == 0
    
    @classmethod
    def obtener_template(cls, **kw):
        """
        Obtiene un rol utilizado como template, para la creación de 
        otros roles
        
        @param kw: posee el identificador o el nombre del rol.
        """
        base_query = DBSession.query(Rol)
        if "id" in kw:
            rol = base_query.filter_by(id_rol=int(kw["id"])).one()
        elif "nombre_rol" in kw:
            rol = base_query.filter_by(nombre_rol=unicode(kw["nombre_rol"])).one()
        return rol
    #}


# The 'info' argument we're passing to the email_address and password columns
# contain metadata that Rum (http://python-rum.org/) can use generate an
# admin interface for your models.
class Usuario(DeclarativeBase):
    """
    User definition.

    This is the user definition used by :mod:`repoze.who`, which requires at
    least the ``user_name`` column.
    Pero se usa un 'translation' a "nombre_usuario" y "roles"
    """
    __tablename__ = 'tg_user'

    #{ Columns

    id_usuario = Column(Integer, autoincrement=True, primary_key=True)
    nombre_usuario = Column(Unicode(32), unique=True, nullable=False)
    email = Column(Unicode(100), unique=True, nullable=False,
                           info = {'rum': {'field':'Email'}})
    nombre = Column(Unicode(50))
    apellido = Column(Unicode(50))
    telefono = Column(Unicode(15))
    nro_documento = Column(Integer)

    _password = Column('password', Unicode(80),
                       info = {'rum': {'field':'Password'}})

    creado = Column(DateTime, default=datetime.now)
    
    #{ Special methods
    def __repr__(self):
        return ('<User: name=%r, email=%r, display=%r>' % (
                self.nombre_usuario, self.email, self.nombre)).encode('utf-8')

    def __unicode__(self):
        return self.nombre or self.nombre_usuario

    #{ Getters and setters

    @property
    def permisos(self):
        """Return a set with all permissions granted to the user."""
        perms = set()
        for g in self.roles:
            perms = perms | set(g.permisos)
        return perms

    @classmethod
    def by_email_address(cls, mail):
        """Return the user object whose email address is ``email``."""
        return DBSession.query(cls).filter_by(email = mail).first()

    @classmethod
    def by_user_name(cls, username):
        """Return the user object whose user name is ``username``."""
        return DBSession.query(cls).filter_by(nombre_usuario = username).first()

    @classmethod
    def por_id(cls, id):
        """
        Método de clase que realiza las búsquedas por identificador.
        
        @param id: identificador del elemento a recuperar
        @type id: C{Integer}
        @return: el elemento recuperado
        @rtype: L{Usuario}
        """        
        return DBSession.query(cls).filter_by(id_usuario=id).one()
    
    def _set_password(self, password):
        """Hash ``password`` on the fly and store its hashed version."""
        # Make sure password is a str because we cannot hash unicode objects
        if isinstance(password, unicode):
            password = password.encode('utf-8')
        salt = sha1()
        salt.update(os.urandom(60))
        hash = sha1()
        hash.update(password + salt.hexdigest())
        password = salt.hexdigest() + hash.hexdigest()
        # Make sure the hashed password is a unicode object at the end of the
        # process because SQLAlchemy _wants_ unicode objects for Unicode cols
        if not isinstance(password, unicode):
            password = password.decode('utf-8')
        self._password = password

    def _get_password(self):
        """Return the hashed version of the password."""
        return self._password

    password = synonym('_password', descriptor=property(_get_password,
                                                        _set_password))

    #}

    def validate_password(self, password):
        """
        Check the password against existing credentials.

        :param password: the password that was provided by the user to
            try and authenticate. This is the clear text version that we will
            need to match against the hashed one in the database.
        :type password: unicode object.
        :return: Whether the password is valid.
        :rtype: bool

        """
        hash = sha1()
        if isinstance(password, unicode):
            password = password.encode('utf-8')
        hash.update(password + str(self.password[:40]))
        return self.password[40:] == hash.hexdigest()


class Permiso(DeclarativeBase):
    """
    Permission definition for :mod:`repoze.what`.

    Only the ``permission_name`` column is required by :mod:`repoze.what`.
    Pero se usa un 'translation' a "nombre_permiso"

    """

    __tablename__ = 'tg_permission'

    #{ Columns

    id_permiso = Column(Integer, autoincrement=True, primary_key=True)
    nombre_permiso = Column(Unicode(32), unique=True, nullable=False)
    descripcion = Column(Unicode(100))

    #{ Relations

    roles = relation(Rol, secondary=group_permission_table,
                      backref='permisos')

    #{ Special methods

    def __repr__(self):
        return ('<Permission: name=%r>' % self.nombre_permiso).encode('utf-8')

    def __unicode__(self):
        return self.nombre_permiso

    @classmethod
    def por_nombre_permiso(cls, np):
        """
        Método de clase que realiza las búsquedas por nombre de permiso.
        
        @param np: nombre del permiso
        @type np: C{unicode}
        @return: el elemento recuperado
        @rtype: L{Permiso}
        """
        return DBSession.query(Permiso).filter_by(nombre_permiso=np).one()
        
    @classmethod
    def por_id(cls, id):
        """
        Método de clase que realiza las búsquedas por identificador.
        
        @param id: identificador del elemento a recuperar
        @type id: C{Integer}
        @return: el elemento recuperado
        @rtype: L{Permiso}
        """        
        return DBSession.query(cls).filter_by(id_permiso=id).one()
    #}


#}
