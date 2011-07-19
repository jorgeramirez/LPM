# -*- coding: utf-8 -*-
"""Test suite for the TG app's models"""
from nose.tools import eq_

from lpm import model
from lpm.tests.models import ModelTest

class TestRol(ModelTest):
    """Unit test case for the ``Rol`` model."""
    klass = model.Rol
    attrs = dict(
        nombre_rol = u"test_group",
        descripcion = u"Test Group",
        tipo=u"Proyecto"
        )


class TestUser(ModelTest):
    """Unit test case for the ``Usuario`` model."""
    
    klass = model.Usuario
    attrs = dict(
        nombre_usuario = u"ignucius",
        email = u"ignucius@example.org"
        )

    def test_obj_creation_username(self):
        """The obj constructor must set the user name right"""
        eq_(self.obj.nombre_usuario, u"ignucius")

    def test_obj_creation_email(self):
        """The obj constructor must set the email right"""
        eq_(self.obj.email, u"ignucius@example.org")

    def test_no_permissions_by_default(self):
        """User objects should have no permission by default."""
        eq_(len(self.obj.permisos), 0)

    def test_getting_by_email(self):
        """Users should be fetcheable by their email addresses"""
        him = model.Usuario.by_email_address(u"ignucius@example.org")
        eq_(him, self.obj)


class TestPermiso(ModelTest):
    """Unit test case for the ``Permiso`` model."""
    
    klass = model.Permiso
    attrs = dict(
        nombre_permiso = u"test_permission",
        descripcion = u"This is a test Description"
        )
