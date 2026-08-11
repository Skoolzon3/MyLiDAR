# MyLiDAR

[Español](#español) | [English](#english)

## English

### NEWS
After a thorough review, this project's work has been featured in an indexed journal! Check it out for yourself at https://link.springer.com/article/10.1007/s12145-026-02126-6

### Description
**MyLiDAR** is a QGIS 3.44 plugin that provides an expanding suite of tools to process and analyze LiDAR point clouds.
In addition to generating detailed reports from LAS/LAZ files, the plugin offers point cloud cleaning, vegetation classification, feature counting, and statistical analysis, all integrated directly into QGIS.

### Features
- **Generation of LiDAR file reports** with metadata, spatial properties, intensity, classifications, returns, and GPS time.
- **Deletion of outliers** to clean up noise in the datasets.
- **Point filtering** of selected classification classes.
- **Counting of features** detected in the dataset (buildings, vegetation & bridges).
- **Classification of vegetation** based on its relative height.
- **Generation of digital elevation models (DEM) of bare terrain** from LiDAR files, as well as their corresponding relief shadow maps.
- **Visualisation of LAS/LAZ file statistics**, including density, ranges and classification counts.

These functions are compatible with LiDAR `.las` and `.laz` files, and their execution is aided by an intuitive user interface, integrated directly into the QGIS menu.

### Installation
1. Download the plugin by clicking on `<Code> → Download ZIP`, at the top of the repository.

2. In QGIS, select `Plugins → Manage and Install Plugins → Install from ZIP`.

3. Drag and drop the ZIP file onto the menu's sole form field.

4. Install the required dependencies (see [dependencies](#dependencies)).

5. Restart QGIS.

6. Manually activate the plugin from ``Plugins → Manage and Install Plugins → Installed``.

### Dependencies
This plugin requires the following Python libraries:
- **laspy** for reading and writing LAS/LAZ files.
- **GDAL** and **OSR** for geospatial data manipulation.
- **numpy** for numerical calculations and statistical queries.
- **scikit-learn** for point clustering.
- **scipy** for scientific data processing and analysis.
- **matplotlib** for generating graphs and visualisations.
- **reportlab** for generating PDF reports.

**Note**: The numpy dependency used in the project is integrated into laspy, so there is no need to install it later on once the latter is installed.

Currently, dependencies are installed automatically when importing the plugin as a ZIP file. However, in case of failure, it is possible to install them manually:

### Install dependencies

#### Windows - QGIS installed alongside OSGeo4W
  1. Open OSGeo4W Shell
  2. Paste and run the following command:
  ```bash
  python -m pip install laspy[lazrs,laszip] scipy GDAL OSR matplotlib reportlab scikit-learn shapely
  ```

**Note**: make sure the command is executed inside the QGIS path. It should look something like this:

```bash
C:\PROGRA~1\QGIS34~1.3>
```

#### macOS
No prior dependencies need to be installed. The necessary dependencies are installed alongside the plugin. Due to the way Python runs in QGIS, you can open multiple instances of QGIS. Simply close these until the installation is complete. This error occurs because Pip attempts to install package dependencies by calling a new Python interpreter, which is launched on another instance of QGIS.

#### Linux (Ubuntu/Debian)
 1. Open the Linux terminal
 2. Paste and execute the following command:
    ```bash
    pip install laspy[lazrs,laszip] scipy GDAL OSR matplotlib reportlab scikit-learn shapely
    ```

### Availability
We recommend using the latest stable version of QGIS to take full advantage of its functionality. Currently compatible with versions later than QGIS 3.18 and earlier than QGIS 4.0.

### Acknowledgements
Plugin developed in collaboration with the Media Engineering Group (GIM) of the Cáceres' School of Technology.

---

## Español

### NOTICIAS
Tras una revisión exhaustiva, ¡el trabajo de este proyecto ha sido publicado en una revista indexada! Échale un vistazo tú mismo en https://link.springer.com/article/10.1007/s12145-026-02126-6

### Descripción
**MyLiDAR** es un complemento de QGIS 3.44 que proporciona un conjunto de herramientas en expansión para procesar y analizar nubes de puntos LiDAR.
Además de generar informes detallados a partir de archivos LAS/LAZ, el complemento ofrece limpieza de nubes de puntos, clasificación de vegetación, recuento de elementos y análisis estadístico, todo ello integrado directamente en QGIS.

### Características
- **Generación de informes de archivos LiDAR** con metadatos, propiedades espaciales, intensidad, clasificaciones, retornos y hora GPS.
- **Borrado de puntos atípicos** para limpiar el ruido de los conjuntos de datos.
- **Filtrado por puntos** de clases de clasificación seleccionadas.
- **Recuento de elementos** detectados en el conjunto de datos (edificios, vegetación y puentes).
- **Clasificación de la vegetación** en función de su altura relativa.
- **Generación de modelos digitales de elevación (DEM) del terreno desnudo**, junto con sus correspondientes mapas de sombras del relieve.
- **Visualización de estadísticas de archivos LAS/LAZ**, incluyendo la densidad, los rangos y los recuentos de clasificación.

Estas funciones son compatibles con archivos LiDAR `.las` y `.laz`, y su ejecución se ayuda de una interfaz de usuario intuitiva, integrada directamente dentro del menú de QGIS.

### Instalación
1. Descargue el complemento haciendo clic en ``<Código> → Descargar ZIP``, en la parte superior del repositorio.

2. En QGIS, seleccione ``Complementos → Administrar e instalar complementos → Instalar desde ZIP``.

3. Arrastre y suelte el archivo ZIP en el único campo del formulario del menú.

4. Instale las dependencias necesarias (consulta [dependencias](#dependencias)).

5. Reinicie QGIS.

6. Active manualmente el complemento desde ``Complementos → Administrar e instalar complementos → Instalados``.

### Dependencias
Este complemento requiere las siguientes bibliotecas de Python:
- **laspy** para leer y escribir archivos LAS/LAZ.
- **GDAL** y **OSR** para la manipulación de datos geoespaciales.
- **numpy** para cálculos numéricos y consultas estadísticas.
- **scikit-learn** para la clusterización de puntos.
- **scipy** para el procesamiento y análisis de datos científicos.
- **matplotlib** para la generación de gráficos y visualizaciones.
- **reportlab** para la generación de informes en PDF.

**Nota**: la dependencia numpy utilizada en el proyecto está integrada en laspy, por lo que no es necesario instalarla posteriormente una vez instalada esta última.

Actualmente, las dependencias se instalan de manera automática en la importación del plugin como ZIP. En caso de fallo, sin embargo, es posible instalarlas manualmente:

### Instalar dependencias

#### Windows - QGIS instalado junto con OSGeo4W
  1. Abra OSGeo4W Shell.
  2. Pegue y ejecute el siguiente comando:
  ```bash
  python -m pip install laspy[lazrs,laszip] scipy GDAL OSR matplotlib reportlab scikit-learn shapely
  ```

**Nota**: asegúrese de que el comando se ejecuta dentro de la ruta de QGIS. Esta debería tener un aspecto similar al siguiente:

```bash
C:\PROGRA~1\QGIS34~1.3>
```

#### macOS
No es necesario instalar dependencias previas. Las dependencias necesarias son instaladas junto con el plugin. Derivado del entorno sobre el que se ejecuta Python en QGIS, puede abrir otras instancias de QGIS. Simplemente ciérrelas hasta finalizar la instalación. Este error deriva de que pip intenta instalar depedencias de los paquetes llamando a un nuevo intérprete de Python, que es iniciado sobre otra instancia de QGIS.

#### Linux (Ubuntu/Debian)
 1. Abra el terminal de Linux
 2. Pegue y ejecute el siguiente comando:
    ```bash
    pip install laspy[lazrs,laszip] scipy GDAL OSR matplotlib reportlab scikit-learn shapely
    ```

### Disponibilidad
Se recomienda utilizar la última versión estable de QGIS para aprovechar su funcionalidad al máximo. Actualmente compatible con versiones posteriores a QGIS 3.18 y anteriores a QGIS 4.0.

### Agradecimientos
Complemento desarrollado en colaboración con el Grupo de Ingeniería de Medios (GIM) de la Escuela Politécnica de Cáceres.
Tras una exhaustiva revisión, ¡el trabajo de este proyecto ha sido publicado en una revista indexada! Échale un vistazo tú mismo en https://link.springer.com/article/10.1007/s12145-026-02126-6
