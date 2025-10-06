# MyLiDAR

[Español](#español) | [English](#english)

## English

### Description
**MyLiDAR** is a QGIS 3.44 plugin that provides an expanding suite of tools to process and analyze LiDAR point clouds.
In addition to generating detailed reports from LAS/LAZ files, the plugin offers point cloud cleaning, vegetation classification, building counting, and statistical analysis, all integrated directly into QGIS.

### Features
- **Generation of LiDAR file reports** with metadata, spatial properties, intensity, classifications, returns, and GPS time.
- **Deletion of outliers** to clean up noise in the datasets.
- **Deletion of overlapping** or redundant points.
- **Counting of buildings** detected in the dataset.
- **Classification of vegetation** based on its relative height.
- **Generation of digital elevation models (DEM) of bare terrain** from LiDAR files, as well as their corresponding relief shadow maps.
- **Visualisation of LAS/LAZ file statistics**, including density, ranges and classification counts.

These functions are compatible with LiDAR `.las` and `.laz` files, and their execution is aided by an intuitive user interface, integrated directly into the QGIS menu.

### Installation
1. Copy the plugin repository into your own QGIS plugin directory (in this example, the `plugins` folder):
   - **Windows:** `%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\`
   - **Linux:** `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/`

   **Note:** The paths above correspond to the **default** QGIS profile. If you are using a custom profile, replace `default` with your profile name (e.g., `profiles/my_profile/python/plugins/`).

2. Restart QGIS.
3. Manually activate the plugin from **Plugins > Manage and Install Plugins**.

### Usage
1. Access **MyLiDAR** tools from the QGIS menu or toolbar.
2. Select the input file to be processed and follow on-screen prompts to configure tool options.
3. Save results to your chosen location if allowed.

### Installation

#### Dependencies
This plugin requires the following Python libraries:
- **matplotlib** for generating graphs and visualisations.
- **laspy** for reading and writing LAS/LAZ files.
- **numpy** for numerical calculations and statistical queries.
- **scipy** for scientific data processing and analysis.
- **reportlab** for generating PDF reports.
- **GDAL** and **OSR** for geospatial data manipulation.
- **scikit-learn** for point clustering.

Note: during the installation of laspy, the numpy dependency used in the project is integrated alongside it, so there is no need to install it later on.

#### How to install dependencies
- **Windows (QGIS installed via OSGeo4W)**:
  Open OSGeo4W Shell and run:
  ```bash
  python -m pip install laspy[lazrs,laszip] scipy GDAL OSR matplotlib reportlab scikit-learn
- **Linux**:
  Open a terminal and run:
  ```bash
  pip install laspy scipy gdal matplotlib reportlab scikit-learn

### Credits
Plugin developed in collaboration with the Media Engineering Group (GIM) of the Polytechnic School of Cáceres.

---

## Español

### Descripción

**MyLiDAR** es un complemento de QGIS 3.44 que proporciona un conjunto de herramientas en expansión para procesar y analizar nubes de puntos LiDAR.
Además de generar informes detallados a partir de archivos LAS/LAZ, el complemento ofrece limpieza de nubes de puntos, clasificación de vegetación, recuento de edificios y análisis estadístico, todo ello integrado directamente en QGIS.

### Características
- **Generación de informes de archivos LiDAR** con metadatos, propiedades espaciales, intensidad, clasificaciones, retornos y hora GPS.
- **Borrado de puntos atípicos** para limpiar el ruido de los conjuntos de datos.
- **Borrado de puntos superpuestos** o redundantes.
- **Recuento de edificios** detectados en el conjunto de datos.
- **Clasificación de la vegetación** en función de su altura relativa.
- **Generación de modelos digitales de elevación (DEM) del terreno desnudo**, junto con sus correspondientes mapas de sombras del relieve.
- **Visualización de estadísticas de archivos LAS/LAZ**, incluyendo la densidad, los rangos y los recuentos de clasificación.

Estas funciones son compatibles con archivos LiDAR `.las` y `.laz`, y su ejecución se ayuda de una interfaz de usuario intuitiva, integrada directamente dentro del menú de QGIS.

### Instalación
1. Copie la carpeta del complemento en su directorio de complementos QGIS propio (en este ejemplo, la carpeta `plugins`):
   - **Windows:** `%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\`
   - **Linux:** `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/`

   **Nota:** Las rutas anteriores corresponden al perfil **predeterminado** de QGIS. Si utiliza un perfil personalizado, sustituya «predeterminado» por el nombre de su perfil (por ejemplo, «perfiles/mi_perfil/python/plugins/»).

2. Reinicie QGIS.
3. Active manualmente el complemento desde **Complementos > Administrar e instalar complementos**.

### Uso
1. Acceda a las herramientas **MyLiDAR** desde el menú o la barra de herramientas de QGIS.
2. Seleccione el archivo de entrada a procesar y siga las instrucciones que aparecen en pantalla para configurar las opciones de la herramienta.
3. Guarde los resultados en la ubicación que desee, en su caso.

#### Dependencias
Este complemento requiere las siguientes bibliotecas de Python:
- **matplotlib** para la generación de gráficos y visualizaciones.
- **laspy** para leer y escribir archivos LAS/LAZ.
- **numpy** para cálculos numéricos y consultas estadísticas.
- **scipy** para el procesamiento y análisis de datos científicos.
- **reportlab** para la generación de informes en PDF.
- **GDAL** y **OSR** para la manipulación de datos geoespaciales.
- **scikit-learn** para la clusterización de puntos.

Nota: durante la instalación de laspy, se integra junto a esta la dependencia de numpy utilizada en el proyecto, por lo que no es necesaria su instalación posterior.

#### Cómo instalar las dependencias
- **Windows (QGIS instalado a través de OSGeo4W)**:
  Abra el shell de OSGeo4W y ejecute:
  ```bash
  python -m pip install laspy[lazrs,laszip] scipy GDAL OSR matplotlib reportlab scikit-learn
- **Linux**:
  Abra un terminal y ejecute:
  ```bash
  pip install laspy scipy gdal matplotlib reportlab scikit-learn

### Créditos
Complemento desarrollado en colaboración con el Grupo de Ingeniería de Medios (GIM) de la Escuela Politécnica de Cáceres.
