## Lambda Project Manager
    A simple project management system.

## Authors:
    * Carlos Bellino
    * Nahuel Hernández
    * Jorge Ramírez


## Installation and Setup


Install ``LPM`` using the setup.py script::

    $ cd LPM
    $ python setup.py install

Create the project database for any model classes defined::

    $ paster setup-app development.ini

Start the paste http server::

    $ paster serve development.ini

While developing you may want the server to reload after changes in package files (or its dependencies) are saved. This can be achieved easily by adding the --reload option::

    $ paster serve --reload development.ini

Then you are ready to go.


## TODO

1. Hacer el mapeo de las tablas del diagrama E/R en clases dentro de la carpeta Model
2. Creación de proyectos:
	-Permitir agregar/eliminar fases mientras el proyecto no esté iniciado.
	-a la hora de crear fases, suponiendo que proyecto.numero_de_fases = n,
	 poner fase.posicion = n+1 e incrementar el numero de fases del proyecto.
  
