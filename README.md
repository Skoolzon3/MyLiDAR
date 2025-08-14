# MyLiDAR

## English

### Description
**MyLiDAR** is a QGIS 3.44 plugin that provides an expanding suite of tools to process and analyze LiDAR point clouds. 
In addition to generating detailed reports from LAS/LAZ files, the plugin offers point cloud cleaning, vegetation classification, building counting, and statistical analysis, all integrated directly into QGIS.

### Features
- **Generate LiDAR File Report** with metadata, spatial properties, intensity, classifications, returns, and GPS time.
- **Remove outlier points** to clean noise from datasets.
- **Remove overlapping** tiles or redundant points.
- **Count buildings** detected in the dataset.
- **Classify vegetation** based on height and other attributes.
- **View file statistics** including density, ranges, and classification counts.
- Supports `.las` and `.laz` LiDAR files.
- Export reports in **TXT**, **Markdown**, or **PDF** formats.
- Simple and intuitive UI integrated into QGIS’s menu and toolbar.
- Fast processing using `laspy`, `numpy`, and the QGIS PyQt5 framework.

### Installation
1. Copy the plugin repository into your QGIS plugin directory:
   - **Linux:** `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/`
   - **Windows:** `%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\`
2. Restart QGIS.
3. Manually activate the plugin from **Plugins > Manage and Install Plugins**.

### Usage
1. Access **MyLiDAR** tools from the QGIS menu or toolbar:
   - **Generate LiDAR File Report**
   - **Remove Outlier Points**
   - **Remove Overlapping**
   - **Count Buildings**
   - **Classify Vegetation**
   - **View File Statistics**
2. Select the input file to be processed and follow on-screen prompts to configure tool options.
   - During report generation, select desired data sections and output format.
3. Save results to your chosen location if allowed.

### Dependencies
- `laspy`
- `numpy`
- PyQt5 (bundled with QGIS)
- QGIS 3.44

### Credits
Developed by **Skoolzon3**.  
This plugin uses:
- `laspy` for LiDAR data parsing
- `PyQt5` for GUI integration
- QGIS API for spatial analysis

---

## Español

### Descripción

**MyLiDAR** es un complemento de QGIS 3.44 que proporciona un conjunto de herramientas en expansión para procesar y analizar nubes de puntos LiDAR.
Además de generar informes detallados a partir de archivos LAS/LAZ, el complemento ofrece limpieza de nubes de puntos, clasificación de vegetación, recuento de edificios y análisis estadístico, todo ello integrado directamente en QGIS.

### Características
- **Generar informe de archivo LiDAR** con metadatos, propiedades espaciales, intensidad, clasificaciones, retornos y hora GPS.
- **Elimina puntos atípicos** para limpiar el ruido de los conjuntos de datos.
- **Elimina mosaicos superpuestos** o puntos redundantes.
- **Cuenta los edificios** detectados en el conjunto de datos.
- **Clasifica la vegetación** en función de la altura y otros atributos.
- **Visualiza las estadísticas del archivo**, incluyendo la densidad, los rangos y los recuentos de clasificación.
- Compatible con archivos LiDAR `.las` y `.laz`.
- Exporta informes en formatos **TXT**, **Markdown** o **PDF**.
- Interfaz de usuario sencilla e intuitiva integrada en el menú y la barra de herramientas de QGIS.
- Procesamiento rápido mediante `laspy`, `numpy` y el marco QGIS PyQt5.

### Instalación
1. Copie la carpeta del complemento en el directorio de complementos de QGIS:
   - **Linux:** `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/`
   - **Windows:** `%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\`
2. Reinicie QGIS.
3. Active manualmente el complemento desde **Complementos > Administrar e instalar complementos**.

### Uso
1. Acceda a las herramientas **MyLiDAR** desde el menú o la barra de herramientas de QGIS:
   - **Generar informe de archivo LiDAR**
   - **Eliminar puntos atípicos**
   - **Eliminar superposiciones**
   - **Contar edificios**
   - **Clasificar vegetación**
   - **Ver estadísticas del archivo**
2. Seleccione el archivo de entrada a procesar y siga las instrucciones que aparecen en pantalla para configurar las opciones de la herramienta.
   - Durante la generación de informes, seleccione las secciones de datos deseadas y el formato de salida.
3. Guarde los resultados en la ubicación que desee, en su caso.

### Dependencias
- `laspy`
- `numpy`
- PyQt5 (incluido con QGIS)
- QGIS 3.44

### Créditos
Desarrollado por **Skoolzon3**.  
Este complemento utiliza:
- `laspy` para el análisis de datos LiDAR
- `PyQt5` para la integración de la interfaz gráfica de usuario
- API de QGIS para el análisis espacial
