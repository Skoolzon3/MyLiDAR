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
1. Download the plugin by clicking on `<Code> → Download ZIP`, at the top of the repository.

2. In QGIS, select `Plugins → Manage and Install Plugins → Install from ZIP`.

3. Drag and drop the ZIP file onto the menu's sole form field.

4. Install the required dependencies (see [dependencies](#dependencies)).

5. Restart QGIS.

6. Manually activate the plugin from ``Plugins → Manage and Install Plugins → Installed``.

<!-- Manual installation -->

<!-- 1.Copy the plugin repository into your own QGIS plugin directory (in this example, the `plugins` folder):
   - **Windows:** `%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\`
   - **Linux:** `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/`

   **Note:** The paths above correspond to the **default** QGIS profile. If you are using a custom profile, replace `default` with your profile name (e.g., `profiles/my_profile/python/plugins/`).

  2. Restart QGIS.

  3. Manually activate the plugin from ``Plugins → Manage and Install Plugins``.-->

### Dependencies
This plugin requires the following Python libraries:
- **laspy** for reading and writing LAS/LAZ files.
- **GDAL** and **OSR** for geospatial data manipulation.
- **numpy** for numerical calculations and statistical queries. ()
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
 1. Open the macOS terminal
 2. Navigate to the following path:
    ```bash
    /Applications/"Your_QGIS_Version".app/Contents/MacOS/bin/
    ```
 3. Paste and execute the following command:
    ```bash
    pip install laspy[lazrs,laszip] scipy GDAL OSR matplotlib reportlab scikit-learn shapely
    ```
 4. Update the sip and PyQt5-sip modules to ensure compatibility between PyQt and QGIS.
    ```bash
    pip install sip --upgrade
    ```	  
    ```bash
    pip install PyQt5-sip --upgrade
    ```

#### Linux (Ubuntu/Debian)
 1. Open the Linux terminal
 2. Paste and execute the following command:
    ```bash
    pip install laspy[lazrs,laszip] scipy GDAL OSR matplotlib reportlab scikit-learn shapely
    ```

### Availability
We recommend using the latest stable version of QGIS to take full advantage of its functionality. Not compatible with versions prior to QGIS 3.18.

### Acknowledgements
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
1. Descargue el complemento haciendo clic en ``<Código> → Descargar ZIP``, en la parte superior del repositorio.

2. En QGIS, seleccione ``Complementos → Administrar e instalar complementos → Instalar desde ZIP``.

3. Arrastre y suelte el archivo ZIP en el único campo del formulario del menú.

4. Instale las dependencias necesarias (consulta [dependencias](#dependencias)).

5. Reinicie QGIS.

6. Active manualmente el complemento desde ``Complementos → Administrar e instalar complementos → Instalados``.

<!-- Instalación manual -->

<!-- 1. Copie la carpeta del complemento en su directorio de complementos QGIS propio (en este ejemplo, la carpeta `plugins`):
   - **Windows:** `%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\`
   - **Linux:** `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/`

   **Nota:** Las rutas anteriores corresponden al perfil **predeterminado** de QGIS. Si utiliza un perfil personalizado, sustituya «predeterminado» por el nombre de su perfil (por ejemplo, «perfiles/mi_perfil/python/plugins/»).

2. Reinicie QGIS.
3. Active manualmente el complemento desde **Complementos > Administrar e instalar complementos**. -->

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
 1. Abra el terminal de macOS
 2. Desplácese a la siguiente ruta:
    ```bash
    /Applications/«Tu_versión_de_QGIS».app/Contents/MacOS/bin/
    ```
 3. Pegue y ejecute el siguiente comando:
    ```bash
    pip install laspy[lazrs,laszip] scipy GDAL OSR matplotlib reportlab scikit-learn shapely
    ```
 4. Actualice los módulos sip y PyQt5-sip para asegurar la compatibilidad entre PyQt y QGIS
    ```bash
    pip install sip --upgrade
    ```	  
    ```bash
    pip install PyQt5-sip --upgrade
    ```

#### Linux (Ubuntu/Debian)
 1. Abra el terminal de Linux
 2. Pegue y ejecute el siguiente comando:
    ```bash
    pip install laspy[lazrs,laszip] scipy GDAL OSR matplotlib reportlab scikit-learn shapely
    ```

### Disponibilidad
Se recomienda utilizar la última versión estable de QGIS para aprovechar su funcionalidad al máximo. No compatible con versiones anteriores a QGIS 3.18.

### Agradecimientos
Complemento desarrollado en colaboración con el Grupo de Ingeniería de Medios (GIM) de la Escuela Politécnica de Cáceres.
