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

from sqlalchemy import Table, ForeignKey, Column
from sqlalchemy.types import Unicode, Integer, DateTime
from sqlalchemy.orm import relation, synonym

from lpm.model import DeclarativeBase, metadata, DBSession

__all__ = ['Usuario', 'Rol', 'Permiso']


#{ Association tables


# This is the association table for the many-to-many relationship between
# groups and permissions. This is required by repoze.what.
group_permission_table = Table('tg_group_permission', metadata,
    Column('group_id', Integer, ForeignKey('tg_group.group_id',
        onupdate="CASCADE", ondelete="CASCADE"), primary_key=True),
    Column('permission_id', Integer, ForeignKey('tg_permission.permission_id',
        onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)
)

# This is the association table for the many-to-many relationship between
# groups and members - this is, the memberships. It's required by repoze.what.
user_group_table = Table('tg_user_group', metadata,
    Column('user_id', Integer, ForeignKey('tg_user.user_id',
        onupdate="CASCADE", ondelete="CASCADE"), primary_key=True),
    Column('group_id', Integer, ForeignKey('tg_group.group_id',
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

    nombre_rol = Column(Unicode(16), unique=True, nullable=False)

    descripcion = Column(Unicode(255))

    creado = Column(DateTime, default=datetime.now)
    
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

    _password = Column('password', Unicode(80),
                       info = {'rum': {'field':'Password'}})

    creado = Column(DateTime, default=datetime.now)
    
    ''' esto tiene que estar en las otras clases
    #{ Relaciones
    regs_historial_item = relation("HistorialItems", backref="usuario")
    regs_historial_lb = relation("HistorialLB", backref="usuario")
    '''
    
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

    nombre_permiso = Column(Unicode(100), unique=True, nullable=False)

    descripcion = Column(Unicode(255))

    #{ Relations

    roles = relation(Rol, secondary=group_permission_table,
                      backref='permisos')

    #{ Special methods

    def __repr__(self):
        return ('<Permission: name=%r>' % self.nombre_permiso).encode('utf-8')

    def __unicode__(self):
        return self.nombre_permiso

    #}


#}
