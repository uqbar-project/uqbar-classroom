# Classroom

GitHub course administration tool for managing courses and assignments in a teaching organization.

Classroom is a command-line application designed to simplify the administration of programming courses using GitHub. It helps instructors manage courses, student rosters, groups, assignments, repositories, and feedback repositories without having to perform these operations manually through the GitHub web interface.

This project was motivated by the closure of GitHub Classroom and aims to provide an alternative tool for replacing it.

Documentation: [English](#english) · [Español](#español)

---

# English

## Table of Contents

- [Purpose](#purpose)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [GitHub Client Configuration](#github-client-configuration)
- [Courses](#courses)
- [Groups](#groups)
- [Assignments](#assignments)
- [License](#license)

## Purpose

Classroom is intended for instructors who use GitHub as part of their courses.

The application provides a command-line interface for managing a GitHub organization used for a course. It can:

- configure and authenticate a GitHub client;
- create and manage courses;
- keep track of courses locally;
- create and manage groups;
- create assignments from GitHub template repositories, both individually and for groups;
- create repositories for specific GitHub users, such as teachers;
- inspect assignments and their repositories.

The application is designed to automate repetitive administrative tasks while keeping the GitHub organization as the source of truth for repositories and users.

Classroom deliberately does not maintain course information on an external server. This avoids maintenance tasks and dependencies on infrastructure other than GitHub. As a consequence, the application does not maintain a relationship between GitHub usernames and students' real names. That relationship must be maintained outside Classroom.

The remaining requirements are implemented through naming conventions applied to the entities exposed by the GitHub API.

A course is represented by a combination of:

- a GitHub organization;
- an academic year;
- a semester;
- a course section.

The resulting course name follows the convention:

`<organization>-<year>s<semester>c<section>`

For example, `obj1unq-2026s2c1` represents section 1 of the second semester of 2026 for the `obj1unq` course organization.

Each course has a GitHub team with the same name containing the GitHub accounts of its students.

Groups are organized into **groupings**. A grouping represents a particular way of dividing the students of a course into groups. This makes it possible to use different group configurations for different assignments. The default grouping is `group`.

Each group is represented by a GitHub team following the convention:

`<course>-<grouping>-<number>`

For example, `obj1unq-2026s2c1-group-1` represents group 1 of the `group` grouping in course `obj1unq-2026s2c1`.

An assignment represents an exercise and is created from a [GitHub template repository](https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-template-repository).

Assignments can be individual or group-based. Individual assignments create one repository per student. Group assignments create one repository per group in the selected grouping.

## Prerequisites

Before using Classroom, you need:

- **Python 3.14 or newer**.
- A **GitHub organization** that will contain the course repositories.
- A GitHub account with sufficient administrative permissions in that organization.
- A [GitHub OAuth App](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/creating-an-oauth-app) configured for the application using `http://127.0.0.1/callback` as redirect URI.

The GitHub user used by Classroom must have the permissions required to create repositories, manage teams and memberships, and perform the other administrative operations required by the application.

## Installation

Clone this repository and install the application using your preferred Python environment.

For example:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

After installation, the `classroom` command should be available:

```bash
classroom --help
```

Each command also provides its own help:

```bash
classroom client --help
classroom login --help
classroom logout --help
classroom whoami --help
classroom course --help
classroom groups --help
classroom assignment --help
```

Some commands provide additional examples and explanations through their epilog:

```bash
classroom course --help
classroom groups --help
classroom assignment --help
```

## GitHub Client Configuration

Classroom uses a [GitHub OAuth App](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/creating-an-oauth-app) to authenticate users.

### Create a GitHub OAuth App

In GitHub, go to:

https://github.com/settings/developers

and open **OAuth Apps**.

Create a new OAuth App and configure the application according to the authentication flow used by Classroom.
You must to use `http://127.0.0.1/callback` as redirect URI

GitHub provides a **Client ID** and **Client Secret** for the application.

The Client ID and Client Secret can then be configured with:

```bash
classroom client CLIENT_ID CLIENT_SECRET
```

For example:

```bash
classroom client my-client-id my-client-secret
```

The configured client ID can be inspected with:

```bash
classroom client
```

The client secret can be explicitly requested with:

```bash
classroom client --show-secret
```

Both values can be removed with:

```bash
classroom client --delete
```

### Local storage

Classroom deliberately stores the two pieces of information differently.

The **Client Secret** is sensitive and is stored using the operating system's keyring through the `keyring` Python package. The secret is therefore not stored as plain text in the application's configuration files.

The **Client ID**, which is not considered a secret, is stored as part of Classroom's local configuration.

Classroom uses `platformdirs` to determine the appropriate operating-system-specific directory for this configuration. `platformdirs` does not itself store the configuration; it provides the application with a standard location in which to do so.

The same configuration directory can also be used for other persistent application settings required by future Classroom features.

After configuring the client, authenticate with GitHub using:

```bash
classroom login
```

The authenticated user can be checked with:

```bash
classroom whoami
```

To log out:

```bash
classroom logout
```

There is an important detail about the authentication mechanism. Classroom uses the browser as the authentication agent, so the login information is associated with both Classroom and the browser.

As a result, if a new login is attempted after logging out, the browser may reuse the previously authenticated session instead of asking for a different user. The HTML page generated after login therefore provides a link inviting the user to log out of the browser as well. After doing so, the next login will ask for a username and password again.

## Courses

A course represents a course section managed by Classroom.

A course is identified by:

- GitHub organization;
- academic year;
- semester;
- course section.

For example:

```bash
classroom course -o obj1unq -y 2026 -s 2 -c 2 roster.txt
```

The roster file contains one GitHub username per line.

### Current course

Classroom can keep a **current course** so that it does not have to be specified in every command.

For example:

```bash
classroom course -o obj1unq -y 2026 -s 2 -c 2 --set-current
```

After that, commands that operate on a course can omit the organization, year, semester, and course options:

```bash
classroom assignment -t https://github.com/obj1unq/pepitaEnunciado
```

The current course is only a convenience for commands that operate on a course. Commands that modify the definition of a course require the course to be specified explicitly, helping prevent accidental modifications to the wrong course.

The current course can be cleared with:

```bash
classroom course --unset
```

### Tracked courses

Classroom also keeps track of courses locally.

Tracked courses act as a **memory aid**: they allow the application to remember courses that have been configured previously, even when they are not the current course.

To see the current course and tracked courses:

```bash
classroom course
```

A course can be removed from the local tracked-course configuration with:

```bash
classroom course -o obj1unq -y 2026 -s 2 -c 2 --untrack
```

Untracking a course only removes the local reference. It does not delete the course or its GitHub resources.

### Updating a course

An existing course can be updated by providing a new roster:

```bash
classroom course -o obj1unq -y 2026 -s 2 -c 2 --update roster.txt
```

### Deleting a course

A course can be deleted with:

```bash
classroom course -o obj1unq -y 2026 -s 2 -c 2 --delete
```

Course modification commands require the course to be explicitly specified.

## Groups

Groups are organized into **groupings**. A grouping represents a particular way of dividing the students of a course into groups. This makes it possible to use different group configurations for different assignments.

The default grouping is `group`.

A grouping is created or updated from a roster file. Each line represents one group, with GitHub usernames separated by spaces.

For example:

```text
user1 user2
user3 user4
```

This roster creates two groups: group 1 contains `user1` and `user2`, while group 2 contains `user3` and `user4`.

Groups are represented by **GitHub teams**, following the convention:

```text
<course>-<grouping>-<number>
```

For example:

```text
obj1unq-2026s2c2-group-1
```

represents group 1 of the `group` grouping in course `obj1unq-2026s2c2`.

### Creating and managing groups

To create the default grouping from a roster:

```bash
classroom groups groups.txt
```

To create a specific grouping:

```bash
classroom groups -g tp1 tp1-groups.txt
```

To show the groups in the default grouping:

```bash
classroom groups
```

To show the groups for a specific course:

```bash
classroom groups -o obj1unq -y 2026 -s 2 -c 2
```

To show a specific grouping:

```bash
classroom groups -g tp1
```

To delete all groups in the default grouping:

```bash
classroom groups --delete
```

To delete all groups in a specific grouping:

```bash
classroom groups -g tp1 --delete
```

When a roster is provided, the command creates or updates the grouping to match its contents. Running the same command multiple times is safe.

The `--delete` option removes all groups belonging to the selected grouping. It cannot be used together with a roster.

If neither a roster nor `--delete` is provided, the command only displays the groups in the selected grouping.

The `--grouping` option is useful when the same course needs different group configurations for different assignments. For example, `group` can contain the groups used throughout the course, while `tp1` and `tp2` can contain different groupings for specific assignments.

## Assignments

An assignment is created from a GitHub template repository.

For example:

```bash
classroom assignment -t https://github.com/obj1unq/pepitaEnunciado
```

If no name is specified, the template repository name is used as the assignment name.

A custom name can be provided with:

```bash
classroom assignment \
    -t https://github.com/obj1unq/pepitaEnunciado \
    -n tp1
```

The `--private` option creates private repositories:

```bash
classroom assignment \
    -t https://github.com/obj1unq/pepitaEnunciado \
    --private
```

### Individual assignments

By default, an assignment is individual. For each student in the course team, Classroom creates a repository in the organization.

Repository names follow the convention:

```text
COURSE_ASSIGNMENT_USERNAME
```

For example:

```text
obj1unq-2026s2c2_pepitaEnunciado_lgassman
obj1unq-2026s2c2_pepitaEnunciado_dfortini
```

The student is then added as a collaborator with the appropriate permissions.

Classroom also creates the `feedback` branch and the feedback baseline used by the feedback workflow.

The repository is then prepared so that a pull request can be used to compare the student's work against the feedback baseline.

### Group assignments

An assignment can also be created for the groups of a course using the `--group` option:

```bash
classroom assignment \
    -t https://github.com/obj1unq/pepitaEnunciado \
    --group
```

By default, the `group` grouping is used. A specific grouping can also be selected:

```bash
classroom assignment \
    -t https://github.com/obj1unq/pepitaEnunciado \
    --group tp1
```

For each group in the selected grouping, Classroom creates a repository in the organization.

Repository names follow the convention:

```text
COURSE_ASSIGNMENT_GROUPING-NUMBER
```

For example, for group 1 of the `group` grouping:

```text
obj1unq-2026s2c2_pepitaEnunciado_group-1
```

The repository is assigned to the corresponding GitHub team, so all members of the group have access to it.

Groups are obtained from the selected grouping in the course. If the specified grouping does not exist, assignment creation fails indicating that the grouping does not exist.

Group assignments make it possible to use different student divisions for different exercises. For example, a course can have a `group` grouping for the usual groups and a `tp1` grouping with a different division for a particular assignment.

### Creating repositories for specific users

Normally, an individual assignment is created for every student in the course.

The `--user` option allows specific GitHub users to be processed instead:

```bash
classroom assignment \
    -t https://github.com/obj1unq/pepitaEnunciado \
    --user lgassman another_user
```

This is useful when an instructor also needs an assignment repository for themselves, for example to prepare or test feedback.

The users specified with `--user` replace the course roster for that operation; they are not added to the list of students.

The `--user` option cannot be combined with `--group`.

### Listing assignments

To list all assignments for the current course:

```bash
classroom assignment
```

A specific course can be selected explicitly:

```bash
classroom assignment -o obj1unq -y 2026 -s 2 -c 2
```

Classroom searches the organization's repositories using the course prefix and determines the assignment names from the repository naming convention.

The output also shows how many repositories have been generated for each assignment.

### Inspecting an assignment

To inspect the repositories belonging to a particular assignment:

```bash
classroom assignment -n tp1
```

Classroom automatically determines whether the repositories correspond to an individual assignment, a group assignment, or a combination of both.

For individual assignments, it reports:

- student repositories and their commit counts;
- students who do not have a repository;
- students who have a repository but have not made any commits beyond the feedback baseline;
- repositories belonging to users who are not students.

For group assignments, it reports:

- the repositories for each grouping and their commit counts;
- groups that do not have a repository;
- groups that have a repository but have not made any commits beyond the feedback baseline;
- the members of each group.

Users who are not students may appear in an individual assignment, but their commits are not tracked.

## License

Classroom is free software distributed under the terms of the **GNU General Public License v3.0 (GPLv3)**.

You are free to use, copy, modify, and redistribute the software. If you redistribute modified versions, the resulting work must remain available under the GPLv3 and its corresponding source code must be made available under the terms of the license.

See the [`LICENSE`](LICENSE) file for the complete license text.

---

# Español

## Tabla de contenidos

- [Propósito](#propósito)
- [Requisitos previos](#requisitos-previos)
- [Instalación](#instalación)
- [Configuración del cliente de GitHub](#configuración-del-cliente-de-github)
- [Cursos](#cursos)
- [Grupos](#grupos)
- [Assignments](#assignments-1)
- [Licencia](#licencia)

## Propósito

Classroom es una herramienta de línea de comandos pensada para docentes que utilizan GitHub en sus cursos.

Pensada como reemplazo de GitHub Classroom debido a que se publicó el cierre de la plataforma.

La mayor diferencia con respecto a GitHub Classroom es la decisión intencional de no tener información en un servidor. Se busca con esto no tener tareas de mantenimiento ni depender de infraestructura más allá de GitHub. Esto genera algunas limitaciones con respecto a lo ofrecido por GitHub Classroom: no se maneja una relación entre nombre de usuario de GitHub y nombre real del estudiante, teniendo que mantener esta relación por fuera de la herramienta. El resto de los requerimientos se resuelven manteniendo convenciones de nombres sobre las entidades que la API de GitHub expone.

- Una cátedra de una materia está representada como una organización de GitHub. La misma ya debe existir previamente al uso de esta herramienta.

- Un curso se representa como una combinación de cátedra (organización), año, semestre (1 o 2) y comisión (un número). Esto se suele representar con el patrón `<orga>-<year>s<semester>c<comisión>`. Si bien podría evitarse el nombre de la cátedra en el curso, se decidió mantenerla como parte del nombre del curso porque facilita, cuando se clonan repositorios en los ambientes locales, la correcta identificación del mismo.

  Por ejemplo: `obj1unq-2026s2c1` corresponde a la comisión 1 del segundo semestre del año 2026 de la cátedra `obj1unq`.

- Por cada curso se genera un team con el mismo nombre, que incluye todos los usuarios de GitHub de los estudiantes.

- Se pueden formar grupos en un curso. Puede haber distintos sets de grupos, soportando así el requerimiento de que para un ejercicio grupal se dividan los estudiantes de cierta manera y que para otro ejercicio la división sea de otra manera. El *grouping* es el concepto que se asocia a cada partición.

  Si no se desea trabajar con distintas particiones, se utiliza el *grouping* por defecto: `group`. Cada grupo tiene un número y se genera un team llamado `<curso>-<grouping>-<nro>` con sus integrantes.

  Por ejemplo, `obj1unq-2026s2c1-group-1` corresponde al grupo 1 de la partición `group` del curso `obj1unq-2026s2c1`.

- Cada ejercicio es representado por el concepto de *assignment*. Se construye para un curso particular, a partir de un [template repository](https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-template-repository) de GitHub.

  El *assignment* tiene un nombre que, por defecto, es el nombre del repositorio template. Por ejemplo, si se usa `https://github.com/wollok/pepita` y no se especifica el nombre, se utiliza `pepita`.

  El *assignment* puede ser grupal o individual. Si es individual, para cada estudiante se genera un repositorio dentro de la organización que se llama `<curso>_<assignment>_<usuario_de_github>`.

  Para el ejemplo anterior, al estudiante con usuario `lgassman` se le generaría el repositorio `https://github.com/obj1unq/obj1unq-2026s2c1_pepita_lgassman`.

  Si el *assignment* es grupal, se genera un repositorio para cada grupo siguiendo el patrón `<curso>_<assignment>_<grouping>-<nro>`.

  Para el ejemplo anterior, para el grupo 1 se generaría el repositorio `https://github.com/obj1unq/obj1unq-2026s2c5_pepita_group-1`.

## Funcionalidades

La aplicación proporciona una interfaz de consola para:

- configurar y autenticar un cliente de GitHub;
- crear y administrar cursos;
- crear y administrar grupos;
- crear assignments a partir de repositorios template de GitHub, tanto individuales como grupales;
- crear repositorios para usuarios específicos de GitHub, como docentes;
- consultar assignments y sus repositorios.

Se busca una especial robustez en el uso de la API de GitHub, tanto para reintentar requests reintentables como para que las operaciones sean idempotentes. De esta manera, si un comando que crea o modifica entidades falla parcialmente, puede ejecutarse nuevamente hasta completar la operación, sin generar inconsistencias ni duplicar las entidades ya creadas.

## Requisitos previos

Para utilizar Classroom se necesita:

- **Python 3.14 o superior**.
- Una **organización de GitHub** que contenga los repositorios de los cursos.
- Un usuario de GitHub con permisos administrativos suficientes dentro de esa organización.
- Una [GitHub OAuth App](https://docs.github.com/en/apps/oauth-apps/creating-an-oauth-app) configurada para la aplicación, usando `http://127.0.0.1/callback` como `redirect URI`,  lo cual otorga un par de `client_id`/`client_secret` que esta aplicación requiere en su configuración.

El usuario utilizado por Classroom debe tener los permisos necesarios para crear repositorios, administrar equipos y membresías y realizar las demás operaciones administrativas requeridas.

## Instalación

Cloná este repositorio e instalá la aplicación utilizando el entorno de Python que prefieras.

Por ejemplo:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

Después de instalarla, el comando `classroom` debería estar disponible:

```bash
classroom --help
```

Cada comando tiene además su propia ayuda:

```bash
classroom client --help
classroom login --help
classroom logout --help
classroom whoami --help
classroom course --help
classroom groups --help
classroom assignment --help
```

Algunos comandos incluyen ejemplos y explicaciones adicionales:

```bash
classroom course --help
classroom groups --help
classroom assignment --help
```

## Configuración del cliente de GitHub

Classroom utiliza una [GitHub OAuth App](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/creating-an-oauth-app) para autenticar a los usuarios.

### Crear una GitHub OAuth App

En GitHub, ingresá a:

https://github.com/settings/developers

y abrí la sección **OAuth Apps**.

Creá una nueva OAuth App y configurala de acuerdo con el flujo de autenticación utilizado por Classroom.
Usá `http://127.0.0.1/callback` en el campo redirect URI


GitHub proporcionará un **Client ID** y un **Client Secret** para la aplicación.

Estos valores se deben configurar en Classroom mediante:

```bash
classroom client CLIENT_ID CLIENT_SECRET
```

Por ejemplo:

```bash
classroom client my-client-id my-client-secret
```

Para consultar el Client ID configurado:

```bash
classroom client
```

Para mostrar explícitamente el Client Secret:

```bash
classroom client --show-secret
```

Para eliminar ambos valores:

```bash
classroom client --delete
```

### Almacenamiento local

Classroom almacena ambos valores de manera diferente.

El **Client Secret** es información sensible y se almacena mediante el keyring del sistema operativo utilizando el paquete Python `keyring`. De esta manera, el secret no se guarda como texto plano en los archivos de configuración de la aplicación.

El **Client ID**, que no es un secreto, se almacena como parte de la configuración local de Classroom.

Classroom utiliza `platformdirs` para determinar el directorio apropiado para esa configuración según el sistema operativo. `platformdirs` no almacena la configuración por sí mismo: proporciona a la aplicación una ubicación estándar donde hacerlo.

Ese mismo directorio de configuración puede utilizarse para otras configuraciones persistentes que necesiten futuras funcionalidades de Classroom.

Una vez configurado el cliente, iniciá sesión con:

```bash
classroom login
```

Para consultar el usuario autenticado:

```bash
classroom whoami
```

Para desloguearse:

```bash
classroom logout
```

Aunque hay un detalle importante: el mecanismo de OAuth utilizado usa el navegador como agente de autenticación. Esto hace que los datos del login estén asociados, además de a Classroom, al navegador.

Es probable que, si se intenta un nuevo login luego de desloguearse, el navegador reutilice los datos obtenidos anteriormente y no ofrezca la posibilidad de cambiar de usuario. Por eso, el HTML generado luego del login ofrece un link para invitar al usuario a desloguearse también del navegador. Luego de esto, el login volverá a solicitar usuario y contraseña.

## Cursos

Un curso representa una comisión administrada por Classroom.

Un curso se identifica mediante:

- organización de GitHub;
- año académico;
- semestre;
- número de comisión.

Por ejemplo:

```bash
classroom course -o obj1unq -y 2026 -s 2 -c 2 roster.txt
```

El archivo de roster contiene un usuario de GitHub por línea.

### Curso actual

Classroom permite establecer un **curso actual**, de modo que no sea necesario especificarlo en cada comando.

Por ejemplo:

```bash
classroom course -o obj1unq -y 2026 -s 2 -c 2 --set-current
```

A partir de ese momento, los comandos que operan sobre un curso pueden omitir la organización, año, semestre y comisión:

```bash
classroom assignment -t https://github.com/obj1unq/pepitaEnunciado
```

El curso actual es solamente una comodidad para los comandos que operan sobre un curso. Los comandos que modifican la definición de un curso requieren que el curso sea especificado explícitamente, para reducir el riesgo de modificar accidentalmente el curso equivocado.

El curso actual se puede limpiar con:

```bash
classroom course --unset
```

### Cursos trackeados

Classroom también mantiene localmente una lista de cursos trackeados.

Los cursos trackeados funcionan como una **ayuda memoria**: permiten recordar cursos que fueron configurados anteriormente aunque no sean el curso actual.

Para consultar el curso actual y la lista de cursos trackeados:

```bash
classroom course
```

Un curso puede eliminarse de la configuración local mediante:

```bash
classroom course -o obj1unq -y 2026 -s 2 -c 2 --untrack
```

Destrackear un curso solamente elimina la referencia local. No elimina el curso ni sus recursos de GitHub.

### Actualizar un curso

Un curso existente puede actualizarse proporcionando un nuevo roster:

```bash
classroom course -o obj1unq -y 2026 -s 2 -c 2 --update roster.txt
```

### Eliminar un curso

Un curso puede eliminarse mediante:

```bash
classroom course -o obj1unq -y 2026 -s 2 -c 2 --delete
```

Los comandos que modifican cursos requieren que el curso sea especificado explícitamente.

## Grupos

Los grupos de un curso se organizan en **groupings**. Un grouping representa una forma particular de particionar a los estudiantes de un curso en grupos. Esto permite utilizar distintas divisiones para diferentes assignments.

El grouping utilizado por defecto se llama `group`.

Para crear o modificar un grouping se utiliza un archivo de roster. Los grupos se numeran según el orden en el que aparecen en el roster, comenzando desde 1. Cada línea corresponde a un grupo, separando los usuarios de GitHub por espacios.

Por ejemplo:

```text
usuario1 usuario2
usuario3 usuario4
```

Este roster genera dos grupos: el grupo 1 tiene `usuario1` y `usuario2`, mientras que el grupo 2 tiene `usuario3` y `usuario4`.

Los grupos se representan mediante **teams de GitHub**, siguiendo la convención:

```text
<curso>-<grouping>-<número>
```

Por ejemplo:

```text
obj1unq-2026s2c2-group-1
```

representa el grupo 1 del grouping `group` del curso `obj1unq-2026s2c2`.

### Crear y administrar grupos

Para crear el grouping por defecto a partir de un roster:

```bash
classroom groups groups.txt
```

Para crear un grouping específico:

```bash
classroom groups -g tp1 tp1-groups.txt
```

Para mostrar los grupos del grouping por defecto:

```bash
classroom groups
```

Para mostrar los grupos de un curso específico:

```bash
classroom groups -o obj1unq -y 2026 -s 2 -c 2
```

Para mostrar un grouping específico:

```bash
classroom groups -g tp1
```

Para eliminar todos los grupos del grouping por defecto:

```bash
classroom groups --delete
```

Para eliminar todos los grupos de un grouping específico:

```bash
classroom groups -g tp1 --delete
```

Cuando se proporciona un roster, el comando crea o actualiza el grouping para que coincida con su contenido. Ejecutar el mismo comando varias veces es seguro.

La opción `--delete` elimina todos los grupos pertenecientes al grouping seleccionado y no puede utilizarse junto con un roster.

Si no se proporciona un roster ni `--delete`, el comando solamente muestra los grupos del grouping seleccionado.

La opción `--grouping` permite mantener distintas configuraciones de grupos para un mismo curso. Por ejemplo, `group` puede contener los grupos utilizados habitualmente durante el curso, mientras que `tp1` y `tp2` pueden contener distintas divisiones de estudiantes para assignments específicos.

## Assignments

Un assignment se crea a partir de un repositorio template de GitHub.

Por ejemplo:

```bash
classroom assignment -t https://github.com/obj1unq/pepitaEnunciado
```

Si no se especifica un nombre, se utiliza como nombre del assignment el nombre del repositorio template.

También se puede indicar un nombre personalizado:

```bash
classroom assignment \
    -t https://github.com/obj1unq/pepitaEnunciado \
    -n tp1
```

La opción `--private` permite crear repositorios privados:

```bash
classroom assignment \
    -t https://github.com/obj1unq/pepitaEnunciado \
    --private
```

### Assignments individuales

Por defecto, un assignment es individual. Para cada estudiante del equipo del curso, Classroom crea un repositorio dentro de la organización.

Los nombres siguen la convención:

```text
CURSO_ASSIGNMENT_USUARIO
```

Por ejemplo:

```text
obj1unq-2026s2c2_pepitaEnunciado_usuario1
obj1unq-2026s2c2_pepitaEnunciado_usuario2
```

Luego se agrega al estudiante como colaborador con los permisos correspondientes.

Classroom también crea la rama `feedback` y el baseline utilizado por el mecanismo de feedback.

Finalmente, el repositorio queda preparado para utilizar un pull request que permita comparar el trabajo del estudiante con el baseline de feedback.

### Assignments grupales

Un assignment también puede crearse para los grupos de un curso utilizando la opción `--group`:

```bash
classroom assignment \
    -t https://github.com/obj1unq/pepitaEnunciado \
    --group
```

Por defecto se utiliza el grouping `group`. También se puede especificar un grouping particular:

```bash
classroom assignment \
    -t https://github.com/obj1unq/pepitaEnunciado \
    --group tp1
```

Para cada grupo del grouping seleccionado se crea un repositorio dentro de la organización.

Los nombres siguen la convención:

```text
CURSO_ASSIGNMENT_GROUPING-NUMERO
```

Por ejemplo, para el grupo 1 del grouping `group`:

```text
obj1unq-2026s2c2_pepitaEnunciado_group-1
```

El repositorio se asigna al team de GitHub correspondiente al grupo, por lo que todos sus integrantes tienen acceso al repositorio.

Los grupos se obtienen a partir del grouping existente en el curso. Si el grouping especificado no existe, la creación del assignment falla indicando que no existe dicho grouping.

Los assignments grupales permiten utilizar distintas divisiones de estudiantes para diferentes ejercicios. Por ejemplo, un curso puede tener un grouping `group` para los grupos habituales y otro grouping `tp1` con una división diferente para un assignment particular.

### Crear repositorios para usuarios específicos

Normalmente, un assignment individual se crea para todos los estudiantes del curso.

La opción `--user` permite procesar usuarios específicos de GitHub:

```bash
classroom assignment \
    -t https://github.com/obj1unq/pepitaEnunciado \
    --user lgassman otro_usuario
```

Esto resulta útil cuando un docente necesita tener también un repositorio del assignment, por ejemplo para preparar o probar el feedback.

Los usuarios especificados mediante `--user` reemplazan al roster del curso para esa operación; no se agregan a la lista de estudiantes.

La opción `--user` no puede combinarse con `--group`.

### Listar los assignments

Para listar todos los assignments del curso actual:

```bash
classroom assignment
```

También se puede especificar explícitamente el curso:

```bash
classroom assignment -o obj1unq -y 2026 -s 2 -c 2
```

Classroom busca los repositorios de la organización utilizando el prefijo del curso y obtiene los nombres de los assignments a partir de la convención de nombres de los repositorios.

El resultado también indica cuántos repositorios fueron generados para cada assignment.

### Consultar un assignment

Para consultar los repositorios correspondientes a un assignment particular:

```bash
classroom assignment -n tp1
```

Classroom identifica automáticamente si los repositorios corresponden a un assignment individual, grupal o a una combinación de ambos.

En los assignments individuales, indica:

- los repositorios de los estudiantes y la cantidad de commits;
- los estudiantes que no tienen un repositorio;
- los estudiantes que tienen un repositorio pero no realizaron commits más allá del baseline de feedback;
- los repositorios correspondientes a usuarios que no son estudiantes.

En los assignments grupales, indica:

- los repositorios de cada grouping y la cantidad de commits;
- los grupos que no tienen un repositorio;
- los grupos que tienen un repositorio pero no realizaron commits más allá del baseline de feedback;
- los integrantes de cada grupo.

Los usuarios que no son estudiantes pueden aparecer en un assignment individual, pero no se realiza seguimiento de sus commits.

## Licencia

Classroom es software libre distribuido bajo los términos de la **GNU General Public License v3.0 (GPLv3)**.

El software puede utilizarse, copiarse, modificarse y redistribuirse libremente. Si se redistribuye una versión modificada, el trabajo resultante debe mantenerse disponible bajo GPLv3 y su código fuente correspondiente debe estar disponible bajo los términos de la licencia.

Ver el archivo [`LICENSE`](LICENSE) para consultar el texto completo de la licencia.
