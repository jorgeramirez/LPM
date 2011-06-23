# -*- coding: utf-8 -*-
"""
Módulo que define el controlador de roles.

@authors:
    - U{Carlos Bellino<mailto:carlosbellino@gmail.com>}
    - U{Nahuel Hernández<mailto:nahuel.11990@gmail.com>}
    - U{Jorge Ramírez<mailto:jorgeramirez1990@gmail.com>}

@since: 1.0
"""
from tgext.crud import CrudRestController
from tg.controllers import RestController
from tg.decorators import (paginate, expose, with_trailing_slash, 
                           without_trailing_slash)
from tg import redirect, request, require, flash, url, validate

from lpm.controllers.validaciones.rol_validator import RolFormValidator
from lpm.model import (DBSession, Usuario, Rol, Permiso, Proyecto, 
                       Fase, TipoItem)
from lpm.lib.sproxcustom import CustomTableFiller, CustomPropertySingleSelectField
from lpm.lib.sproxcustom import WidgetSelectorDojo, MultipleSelectDojo
from lpm.lib.authorization import PoseePermiso, AlgunPermiso

from sprox.tablebase import TableBase
from sprox.fillerbase import TableFiller
#from sprox.dojo.tablebase import DojoTableBase as TableBase
#from sprox.dojo.fillerbase import DojoTableFiller as TableFiller
from sprox.fillerbase import EditFormFiller
#from sprox.formbase import AddRecordForm, EditableForm
from sprox.dojo.formbase import DojoAddRecordForm as AddRecordForm
from sprox.dojo.formbase import DojoEditableForm as EditableForm
from sprox.widgets import PropertySingleSelectField

from tw.forms.fields import PasswordField, TextField, TextArea, Button

from repoze.what.predicates import not_anonymous

from tg import tmpl_context, request

import transaction


class RolTable(TableBase):
    __model__ = Rol
    __headers__ = {'nombre_rol' : u'Nombre de Rol',
                   'codigo' : u"Código", 'creado': u"Fecha Creación",
                   'tipo' : u'Tipo'
                  }
    __omit_fields__ = ['id_rol', 'permisos', 'usuarios',
                       'id_proyecto', 'id_fase', 'id_tipo_item',
                       'descripcion']
    __default_column_width__ = '15em'
    __column_widths__ = {'nombre_rol': "35em",
                         'codigo': "35em",
                         '__actions__' : "50em"
                        }
    
rol_table = RolTable(DBSession)


class RolTableFiller(CustomTableFiller):
    __model__ = Rol
    __omit_fields__ = ['permisos', 'usuarios',
                       'id_proyecto', 'id_fase', 'id_tipo_item',
                       'descripcion']
   
    def __actions__(self, obj):
        """Links de acciones para un registro dado"""
        value = '<div>'
        clase = 'actions'
        url_cont = ""
        contexto = ""
        perm_mod = None
        perm_del = None
        if (obj.tipo == "Sistema"):
            url_cont = "/roles/"
            perm_mod = PoseePermiso('modificar rol')
            perm_del = PoseePermiso('eliminar rol')
        else:
            url_cont = "/rolesplantilla/"
            tipo = obj.tipo.lower()
            if (tipo.find(u"proyecto") >= 0):
                contexto = "proyecto"
                if tipo == "proyecto":
                    perm_mod = PoseePermiso('modificar rol', 
                                            id_proyecto=obj.id_proyecto)
                    perm_del = PoseePermiso('eliminar rol',
                                            id_proyecto=obj.id_proyecto)
                else:
                    perm_mod = PoseePermiso('modificar rol')
                    perm_del = PoseePermiso('eliminar rol')
            elif (tipo.find(u"fase") >= 0):
                contexto = "fase"
                if tipo == "fase":
                    perm_mod = PoseePermiso('modificar rol', 
                                            id_fase=obj.id_fase)
                    perm_del = PoseePermiso('eliminar rol',
                                            id_fase=obj.id_fase)
                else:
                    perm_mod = PoseePermiso('modificar rol')
                    perm_del = PoseePermiso('eliminar rol')
            else:
                contexto = "ti"
                if tipo.find("plantilla") >= 0:
                    perm_mod = PoseePermiso('modificar rol')
                    perm_del = PoseePermiso('eliminar rol')
                else:
                    perm_mod = PoseePermiso('modificar rol', 
                                            id_tipo_item=obj.id_tipo_item)
                    perm_del = PoseePermiso('eliminar rol',
                                            id_tipo_item=obj.id_tipo_item)

            
        if perm_mod.is_met(request.environ):
            value += '<div>' + \
                        '<a href="' +  url_cont + str(obj.id_rol) + "/edit?contexto="+  \
                        contexto + '" class="' + clase + '">Modificar</a>' + \
                     '</div><br />'

        if perm_del.is_met(request.environ):
            value += '<div><form method="POST" action="./' + str(obj.id_rol) + '" class="button-to">'+\
                     '<input type="hidden" name="_method" value="DELETE" />' +\
                     '<input onclick="return confirm(\'Está seguro?\');" value="Delete" type="submit" '+\
                     'style="background-color: transparent; float:left; border:0; color: #286571;'+\
                     'display: inline; margin: 0; padding: 0;" class="' + clase + '"/>'+\
                     '</form></div><br />'
        value += '</div>'
        return value
    
    def _do_get_provider_count_and_objs(self, **kw):
        """
        Se muestra la lista de rol si se tiene un permiso 
        necesario. Caso contrario le muestra sus roles.
        """
        if AlgunPermiso(tipo="Rol").is_met(request.environ):
            return super(RolTableFiller,
                         self)._do_get_provider_count_and_objs(**kw)
        username = request.credentials['repoze.what.userid']
        user = Usuario.by_user_name(username)
        return len(user.roles), user.roles 

rol_table_filler = RolTableFiller(DBSession)


class RolPlantillaTableFiller(RolTableFiller):
    def _do_get_provider_count_and_objs(self, **kw):
        """
        Se muestra la lista de rol si se tiene un permiso 
        necesario.
        """
        if AlgunPermiso(tipo="Rol").is_met(request.environ):
            count, roles = super(RolPlantillaTableFiller,
                                 self)._do_get_provider_count_and_objs(**kw)
        filtrados = []                       
        for r in roles:
            if (r.tipo.find("Plantilla") >= 0):
                filtrados.append(r)
                
        return len(filtrados), filtrados

rol_plantilla_table_filler = RolPlantillaTableFiller(DBSession)


class RolContextoTableFiller(RolTableFiller):
    def _do_get_provider_count_and_objs(self, **kw):
        """
        Se muestra la lista de rol si se tiene un permiso 
        necesario.
        """
        if AlgunPermiso(tipo="Rol").is_met(request.environ):
            query = DBSession.query(Rol).filter(Rol.tipo.in_([u"Proyecto",
                                                u"Fase", u"Tipo de Ítem"]))
            return query.count(), query.all()
        return 0, []

rol_contexto_table_filler = RolContextoTableFiller(DBSession)


class CodProyectoField(PropertySingleSelectField):
    """Dropdown list para codigo de proyecto"""
    def _my_update_params(self, d, nullable=False):
        options = []
        options.append((0, "----------"))
        proyectos = DBSession.query(Proyecto).all()
        for p in proyectos:
            options.append((p.id_proyecto, '%s (%s)' % (p.codigo, 
                    p.nombre)))
        d['options'] = options
        return d
  

class CodFaseField(PropertySingleSelectField):
    """Dropdown list para codigo de fase"""
    def _my_update_params(self, d, nullable=False):
        options = []
        options.append((0, "----------"))
        fases = DBSession.query(Fase).all()
        for f in fases:
            options.append((f.id_fase, '%s (%s)' % (f.codigo, 
                    f.nombre)))
        d['options'] = options
        return d


class CodTipoItemField(PropertySingleSelectField):
    """Dropdown list para codigo de tipo de item"""
    def _my_update_params(self, d, nullable=False):
        options = []
        options.append((0, "----------"))
        tipos = DBSession.query(TipoItem).all()
        for t in tipos:
            options.append((t.id_tipo_item, '%s' % t.codigo))
        d['options'] = options
        return d

#para mejorar el multiple selector hecho en dojo
class PermisosMultipleSelect(MultipleSelectDojo):
    
    def _my_update_params(self, d, nullable=False):
        options, selected = [], []
        permisos = self.get_permisos()
        for p in permisos:
            if d['value'] and (p.id_permiso in d['value']): #seleccionados
                selected.append((p.id_permiso, '%s' % p.nombre_permiso))
            else:
                options.append((p.id_permiso, '%s' % p.nombre_permiso))
        d['options'] = options
        d['selected_options'] = selected
#        a = 1/0
        return d
    
    def get_permisos(self):
        pass


#para mejorar el multiple selector hecho en dojo
class PermisosSistemaMultipleSelect(PermisosMultipleSelect):
    def get_permisos(self):
        return Permiso.permisos_de_sistema()

class PermisosPlantillaTiMultipleSelect(PermisosMultipleSelect):
    def get_permisos(self):
        return Permiso.permisos_ti()
    
class PermisosPlantillaFaseMultipleSelect(PermisosMultipleSelect):
    def get_permisos(self):
        return Permiso.permisos_fases()
    
class PermisosPlantillaProyMultipleSelect(PermisosMultipleSelect):
    def get_permisos(self):
        return Permiso.permisos_proyectos()
    
class PermisosContextoMultipleSelect(PermisosMultipleSelect):
    def get_permisos(self):
        return Permiso.permisos_con_contexto()

class SelectorPermisosSistema(WidgetSelectorDojo):
    default_multiple_select_field_widget_type = PermisosSistemaMultipleSelect

class SelectorPermisosPlantillaProy(WidgetSelectorDojo):
    default_multiple_select_field_widget_type = PermisosPlantillaProyMultipleSelect
    
class SelectorPermisosPlantillaFase(WidgetSelectorDojo):
    default_multiple_select_field_widget_type = PermisosPlantillaFaseMultipleSelect
    
class SelectorPermisosPlantillaTi(WidgetSelectorDojo):
    default_multiple_select_field_widget_type = PermisosPlantillaTiMultipleSelect
    
class SelectorPermisosContexto(WidgetSelectorDojo):
    default_multiple_select_field_widget_type = PermisosContextoMultipleSelect


class RolAddForm(AddRecordForm):
    __model__ = Rol
    __omit_fields__ = ['id_rol', 'usuarios',
                       'codigo', 'creado', 'tipo', 'id_proyecto', 'id_fase',
                       'id_tipo_item']
    __require_fields__ = ['nombre_rol', 'permisos']
    __base_validator__ = RolFormValidator
    __field_order__ = ['nombre_rol', 'descripcion', 'permisos']
    __field_attrs__ = {'descripcion' : {'row': '1'},
                       'nombre_rol': { 'maxlength' : '32'}
                       }
    __widget_selector_type__ = SelectorPermisosSistema
    descripcion = TextArea                         
    
rol_add_form = RolAddForm(DBSession)
    

class RolPlantillaAddForm(RolAddForm):
    def __init__(self, DBS, selector):
        self.__widget_selector_type__ = selector
        super(RolPlantillaAddForm, self).__init__(DBS)
 
    __hide_fields__ = ['tipo', 'id_proyecto', 'id_tipo_item', 'id_fase']
    #__omit_fields__ = ['id_rol', 'usuarios',
    #                   'codigo', 'creado', 'id_proyecto', 'id_fase',
    #                   'id_tipo_item'
    __omit_fields__ = ['id_rol', 'usuarios', 'codigo', 'creado']
    __field_order__ = ['nombre_rol', 'descripcion', 'permisos']
    
    
rol_plantilla_add_form = None
#rol_plantilla_add_form = RolPlantillaAddForm(DBSession)


class RolContextoAddForm(RolAddForm):
    __omit_fields__ = ['id_rol', 'usuarios','codigo', 'creado', 'tipo']
    __field_order__ = ['nombre_rol', 'descripcion',
                        'id_proyecto', 'id_fase', 'id_tipo_item',
                        'permisos']
    __base_validator__ = RolFormValidator
    __widget_selector_type__ = SelectorPermisosContexto
    id_proyecto = CodProyectoField("id_proyecto", label_text="Proyecto")
    id_fase = CodFaseField("id_fase", label_text="Fase")
    id_tipo_item = CodTipoItemField("id_tipo_item", label_text="Tipo de Item")
    descripcion = TextArea
    
rol_contexto_add_form = RolContextoAddForm(DBSession)
    

class RolEditForm(EditableForm):
    __model__ = Rol
    __hide_fields__ = ['id_rol']
    __omit_fields__ = [ 'usuarios',
                       'codigo', 'creado', 'tipo', 'id_proyecto',
                       'id_fase', 'id_tipo_item']
    __require_fields__ = ['nombre_rol', 'permisos']
    __base_validator__ = RolFormValidator
    __field_order__ = ['nombre_rol', 'descripcion', 'permisos']
    __field_attrs__ = {'descripcion' : {'row': '1'},
                       'nombre_rol': { 'maxlength' : '32'}
                       
                      }
    __widget_selector_type__ = SelectorPermisosSistema
    descripcion = TextArea

rol_edit_form = RolEditForm(DBSession)


class RolPlantillaEditForm(RolEditForm):
    def __init__(self, DBS, selector):
        self.__widget_selector_type__ = selector
        super(RolPlantillaEditForm, self).__init__(DBS)

    __hide_fields__ = ['id_rol', 'tipo', 'id_proyecto', 'id_fase', 
                       'id_tipo_item']
    __omit_fields__ = ['usuarios', 'codigo', 'creado']
    __field_order__ = ['id_rol', 'nombre_rol', 'descripcion', 'tipo', 'permisos']

    
rol_plantilla_edit_form = None       
#rol_plantilla_edit_form = RolPlantillaEditForm(DBSession)



class RolContextoEditForm(RolEditForm):
    __omit_fields__ = ['id_rol', 'usuarios','codigo', 'creado', 'tipo']
    __field_order__ = ['nombre_rol', 'descripcion',
                        'id_proyecto', 'id_fase', 'id_tipo_item',
                        'permisos']
    __widget_selector_type__ = SelectorPermisosContexto
    id_proyecto = CodProyectoField("id_proyecto", label_text="Proyecto")
    id_fase = CodFaseField("id_fase", label_text="Fase")
    id_tipo_item = CodTipoItemField("id_tipo_item", label_text="Tipo de Item")
    descripcion = TextArea

rol_contexto_edit_form = RolContextoEditForm(DBSession)        


class RolEditFiller(EditFormFiller):
    __model__ = Rol

rol_edit_filler = RolEditFiller(DBSession)


class RolController(CrudRestController):
    """Controlador de roles"""
    #{ Variables
    title = u"Administrar Roles"
    action = "/roles/"
    rol_tipo = u"Sistema" #indica que el tipo no hay que averiguar.
    #{ Plantillas

    # No permitir usuarios anonimos (?)
    allow_only = not_anonymous(u"El usuario debe haber iniciado sesión")
    
    #{ Modificadores
    model = Rol
    table = rol_table
    table_filler = rol_table_filler
    new_form = rol_add_form
    edit_form = rol_edit_form
    edit_filler = rol_edit_filler

    #para el form de busqueda
    
    #columnas = dict(codigo="texto", nombre_rol="texto", tipo="combobox")
    #tipo_opciones = [u'Plantilla', u'Sistema', u'Proyecto',
    #                    u'Fase', u'Tipo de Ítem']

    opciones = dict(codigo= u'Código',
                    nombre_rol= u'Nombre',
                    tipo=u'Tipo'
                    )
    columnas = dict(codigo='texto',
                    nombre_rol='texto',
                    tipo='combobox'
                    )
    comboboxes = dict(tipo=Rol.tipos_posibles)
 
    #{ Métodos
    @with_trailing_slash
    @paginate('lista_elementos', items_per_page=5)
    @expose('lpm.templates.rol.get_all')
    @expose('json')
    def get_all(self, *args, **kw):
        """ 
        Retorna todos los registros
        Retorna una página HTML si no se especifica JSON
        """
        puede_crear = PoseePermiso("crear rol").is_met(request.environ)
        if request.response_type == 'application/json':
            return self.table_filler.get_value(**kw)
        if not getattr(self.table.__class__, '__retrieves_own_value__', False):
            roles = self.table_filler.get_value(**kw)
        else:
            roles = []
        tmpl_context.widget = self.table
        atras = "/"
        return dict(lista_elementos=roles, 
                    page=self.title, 
                    titulo=self.title, 
                    modelo=self.model.__name__, 
                    columnas=self.columnas,
                    opciones=self.opciones,
                    comboboxes=self.comboboxes,
                    url_action=self.action,
                    puede_crear=puede_crear,
                    atras=atras)

    @expose('lpm.templates.rol.edit')
    def edit(self, *args, **kw):
        """Despliega una pagina para modificar rol"""
        pp = PoseePermiso('modificar rol')
        if not pp.is_met(request.environ):
            flash(pp.message % pp.nombre_permiso, 'warning')
            redirect(self.action)
        tmpl_context.widget = self.edit_form
        value = self.edit_filler.get_value(values={'id_rol': int(args[0])})
#        value['_method'] = 'PUT'
        page = "Rol {nombre}".format(nombre=value["nombre_rol"])
        atras = self.action
        return dict(value=value, page=page, atras=atras)

    @without_trailing_slash
    @expose('lpm.templates.rol.new')
    def new(self, *args, **kw):
        """Despliega una pagina para crear un rol"""
        pp = PoseePermiso('crear rol')
        if not pp.is_met(request.environ):
            flash(pp.message % pp.nombre_permiso, 'warning')
            redirect(self.action)
        tmpl_context.widget = self.new_form
        if request.environ.get('HTTP_REFERER') == "http://" + request.environ.get('HTTP_HOST',) + "/":
            atras = "../"
        else:
            atras = "/roles"
        return dict(value=kw, page="Nuevo Rol", action=self.action, atras=atras)
    
    @validate(rol_add_form, error_handler=new)
    @expose()
    def post(self, *args, **kw):
        """create a new record"""
        pp = PoseePermiso('crear rol')
        if not pp.is_met(request.environ):
            flash(pp.message % pp.nombre_permiso, 'warning')
            redirect(self.action)
        transaction.begin()
        if (not kw.has_key('tipo')):
            kw["tipo"] = self.rol_tipo
        Rol.crear_rol(**kw)
        transaction.commit()
        redirect(self.action)
        
    @validate(rol_edit_form, error_handler=edit)
    @expose()
    def put(self, *args, **kw):
        """update a record"""
        pp = PoseePermiso('modificar rol')
        if not pp.is_met(request.environ):
            flash(pp.message % pp.nombre_permiso, 'warning')
            redirect(self.action)
        id_rol = int(args[0][0])
        if kw.has_key("id_rol"):
            del kw["id_rol"]
        transaction.begin()
        Rol.actualizar_rol(id_rol, **kw)
        transaction.commit()
        redirect(self.action)

    @with_trailing_slash
    @paginate('lista_elementos', items_per_page=5)
    @expose('lpm.templates.rol.get_all')
    @expose('json')
    def post_buscar(self, *args, **kw):
        puede_crear = PoseePermiso("crear rol").is_met(request.environ)
        tmpl_context.widget = self.table
        buscar_table_filler = self.table_filler.__class__(DBSession)
        buscar_table_filler.filtros = kw
        roles = buscar_table_filler.get_value()
        atras = self.action
        return dict(lista_elementos=roles, 
                    page=self.title, 
                    titulo=self.title, 
                    modelo=self.model.__name__, 
                    columnas=self.columnas,
                    opciones=self.opciones,
                    comboboxes=self.comboboxes,
                    url_action=self.action,
                    puede_crear=puede_crear,
                    atras=atras)
    #}
       

class RolPlantillaController(RolController):
    """Controlador de roles de tipo plantilla"""
    #{ Variables
    title = u"Administrar Roles de Plantilla"
    action = "/rolesplantilla/"
    rol_tipo = u"Plantilla" #indica que el tipo no hay que averiguar.

    #{ Modificadores
    model = Rol
    table = rol_table
    table_filler = rol_plantilla_table_filler
    new_form = None
    edit_form = None
    edit_filler = rol_edit_filler

    #para el form de busqueda
    opciones = dict(codigo= u'Código',
                    nombre_rol= u'Nombre',
                    tipo=u'Tipo'
                    )
    columnas = dict(codigo='texto',
                    nombre_rol='texto',
                    tipo='combobox'
                    )
    
    tipos = []
    for i in Rol.tipos_posibles.keys():
        if (i.find("Plantilla") >= 0):
            tipos.append(i)

      
    comboboxes = dict(tipo=tipos)
 
    #{ Métodos
    @with_trailing_slash
    @paginate('lista_elementos', items_per_page=5)
    @expose('lpm.templates.rol.get_all')
    @expose('json')
    def get_all(self, *args, **kw):
        """ 
        Retorna todos los registros
        Retorna una página HTML si no se especifica JSON
        """
        puede_crear = PoseePermiso("crear rol").is_met(request.environ)
        if request.response_type == 'application/json':
            return self.table_filler.get_value(**kw)
        if not getattr(self.table.__class__, '__retrieves_own_value__', False):
            roles = self.table_filler.get_value(**kw)
        else:
            roles = []
        tmpl_context.widget = self.table
        atras = '/'
        return dict(lista_elementos=roles, 
                    page=self.title, 
                    titulo=self.title, 
                    modelo=self.model.__name__, 
                    columnas=self.columnas,
                    opciones=self.opciones,
                    comboboxes=self.comboboxes,
                    url_action=self.action,
                    puede_crear=puede_crear,
                    atras=atras
                    )
        
    @with_trailing_slash
    @paginate('lista_elementos', items_per_page=5)
    @expose('lpm.templates.rol.get_all')
    @expose('json')
    def post_buscar(self, *args, **kw):
        puede_crear = PoseePermiso("crear rol").is_met(request.environ)
        tmpl_context.widget = self.table
        buscar_table_filler = self.table_filler.__class__(DBSession)
        buscar_table_filler.filtros = kw
        roles = buscar_table_filler.get_value()
        #a = 1 / 0
        atras = self.action
        return dict(lista_elementos=roles, 
                    page=self.title, 
                    titulo=self.title, 
                    modelo=self.model.__name__, 
                    columnas=self.columnas,
                    opciones=self.opciones,
                    comboboxes=self.comboboxes,
                    url_action=self.action,
                    puede_crear=puede_crear,
                    atras=atras)
        
    @with_trailing_slash
    @expose('lpm.templates.rol.edit')
    def edit(self, id, *args, **kw):
        """Despliega una pagina para modificar rol"""
#        a = 1/0 
        if (not kw['contexto']):
            redirect('../')
        elif (kw['contexto'] == "proyecto"):
            selector = SelectorPermisosPlantillaProy
        elif (kw['contexto'] == "fase"):
            selector = SelectorPermisosPlantillaFase
        elif (kw['contexto'] == "ti"):
            kw["contexto"] = u"Tipo de Ítem"
            selector = SelectorPermisosPlantillaTi
           
        self.edit_form = RolPlantillaEditForm(DBS=DBSession, selector=selector)     
        tmpl_context.widget = self.edit_form
        rol_plantilla_edit_form = self.edit_form
        
        
        page=u"Editar Rol Plantilla de {contexto}".format(contexto=kw['contexto'])
        
        value = self.edit_filler.get_value(values={'id_rol': int(id)})
        
        #agregado
        if value["tipo"].find("Plantilla") < 0:
            page=u"Editar Rol de {contexto}".format(contexto=kw['contexto'])
            
#        value['_method'] = 'PUT'#?

        if request.environ.get('HTTP_REFERER') == "http://" + request.environ.get('HTTP_HOST',) + "/":
            atras = "../"
        else:
            atras = "/rolesplantilla"
        
        return dict(value=value, page=page, atras=atras)
    
    @without_trailing_slash
    @expose('lpm.templates.rol.new')
    def new(self, contexto=None, *args, **kw):
        page = u"Nuevo Rol Plantilla de {contexto}"
        if (not contexto):
            redirect('../')
        elif (contexto == "proyecto"):
            selector = SelectorPermisosPlantillaProy
            kw['tipo'] = u'Plantilla {contexto}'.format(contexto=contexto)

            if kw.has_key("id_proyecto"): #desde edit de proyecto
                kw["tipo"] = u"Proyecto"
                page = u"Nuevo Rol de {contexto}"

        elif (contexto == "fase"):
            selector = SelectorPermisosPlantillaFase
            kw['tipo'] = u'Plantilla {contexto}'.format(contexto=contexto)
            
            if kw.has_key("id_fase"): #desde edit de fase
                kw["tipo"] = u"Fase"
                page = u"Nuevo Rol de {contexto}"

        elif (contexto == "ti"):
            selector = SelectorPermisosPlantillaTi
            kw['tipo'] = u'Plantilla tipo ítem'
            contexto = u"Tipo de Ítem"
            if kw.has_key("id_tipo_item"): #desde edit de tipo de item
                kw["tipo"] = u"Tipo de Ítem"
                page = u"Nuevo Rol de {contexto}"

            
        self.new_form = RolPlantillaAddForm(DBS=DBSession, selector=selector)     
        tmpl_context.widget = self.new_form
        rol_plantilla_add_form = self.new_form
        
        page = page.format(contexto=contexto)
        
        if request.environ.get('HTTP_REFERER') == "http://" + request.environ.get('HTTP_HOST',) + "/":
            atras = "/"
        else:
            atras = "/rolesplantilla"
        
        return dict(value=kw, page=page, action="../", atras=atras)

    #@validate(rol_plantilla_add_form, error_handler=new)
    @expose()
    def post(self, *args, **kw):
        """ Crea un nuevo rol plantilla o con contexto"""
        pp = None
        if kw["id_proyecto"]:
            pp = PoseePermiso('crear rol', id_proyecto=int(kw["id_proyecto"]))
        elif kw["id_fase"]: 
            pp = PoseePermiso('crear rol', id_fase=int(kw["id_fase"]))
        elif kw["id_tipo_item"]:
            pp = PoseePermiso('crear rol', id_tipo_item=int(kw["id_tipo_item"]))
        else:
            pp = PoseePermiso('crear rol')
        
        if not pp.is_met(request.environ):
            flash(pp.message % pp.nombre_permiso, 'warning')
            redirect(self.action)
        
        Rol.crear_rol(**kw)
        redirect(self.action)

   #@validate(rol_plantilla_edit_form, error_handler=edit)
    @expose()
    def put(self, *args, **kw):
        """actualiza un rol"""
        pp = None
        if kw["id_proyecto"]:
            pp = PoseePermiso('modificar rol', id_proyecto=int(kw["id_proyecto"]))
        elif kw["id_fase"]:    
            pp = PoseePermiso('modificar rol', id_fase=int(kw["id_fase"]))
        elif kw["id_tipo_item"]:
            pp = PoseePermiso('modificar rol', id_tipo_item=int(kw["id_tipo_item"]))
        else:
            pp = PoseePermiso('modificar rol')

        if not pp.is_met(request.environ):
            flash(pp.message % pp.nombre_permiso, 'warning')
            redirect(self.action)

        Rol.actualizar_rol(**kw)
        redirect(self.action)
    
    #}
