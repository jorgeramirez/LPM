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

#TODO
(no voy a escribir en inglés)
1. Hacer el mapeo de las tablas del diagrama E/R en clases dentro de la carpeta Model
