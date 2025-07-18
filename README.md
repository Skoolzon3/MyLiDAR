# MyLiDAR Plugin for QGIS 3.x

## English

### Description
**MyLiDAR Plugin** is a QGIS 3.x plugin that allows users to generate detailed reports from LAS/LAZ LiDAR files. The plugin supports TXT, Markdown, and PDF output formats and provides insight into file metadata, spatial properties, intensity, classifications, returns, and GPS time information.

### Features
- Load and analyze `.las` or `.laz` LiDAR files.
- View file metadata: file name, source ID, system ID, version, point format, and more.
- Extract spatial information: bounds, area, density, and axis ranges.
- Report GPS time ranges (if available).
- List point classifications and return numbers.
- Export reports in **TXT**, **Markdown**, or **PDF** formats.
- Simple and intuitive UI integrated with QGIS.
- Fast processing using `laspy`, `numpy`, and QGIS PyQt5 framework.

### Installation
1. Copy the plugin folder to your QGIS plugin directory:
   - Linux: `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/`
   - Windows: `%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\`
2. Restart QGIS.
3. Activate the plugin from **Plugins > Manage and Install Plugins**.

### Usage
1. Click **MyLiDAR > Generate LiDAR File Report** from the QGIS menu or toolbar.
2. Select a `.las` or `.laz` file.
3. Choose what data to include in the report.
4. Select output format (TXT, Markdown, or PDF).
5. Save the report to your desired location.

### Dependencies
- `laspy`
- `numpy`
- PyQt5 (bundled with QGIS)
- QGIS 3.x

### Credits
Developed by Skoolzon3.
This plugin uses `laspy` for LiDAR data parsing and `PyQt5` for GUI integration.

---

## Español

### Descripción
**MyLiDAR Plugin** es un complemento para QGIS 3.x que permite generar informes detallados a partir de archivos LiDAR en formato LAS/LAZ. El complemento admite exportación en formatos TXT, Markdown y PDF, y proporciona información sobre metadatos del archivo, propiedades espaciales, intensidad, clasificaciones, retornos y tiempo GPS.

### Funcionalidades
- Carga y análisis de archivos `.las` o `.laz`.
- Visualización de metadatos: nombre del archivo, ID de origen, ID del sistema, versión, formato de puntos, entre otros.
- Extracción de información espacial: límites, área, densidad y rangos de ejes.
- Reporte del tiempo GPS (si está disponible).
- Listado de clasificaciones de puntos y números de retorno.
- Exportación de informes en **TXT**, **Markdown** o **PDF**.
- Interfaz sencilla e intuitiva integrada en QGIS.
- Procesamiento rápido mediante `laspy`, `numpy` y PyQt5.

### Instalación
1. Copia la carpeta del complemento al directorio de plugins de QGIS:
   - Linux: `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/`
   - Windows: `%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\`
2. Reinicia QGIS.
3. Activa el complemento desde **Complementos > Administrar e instalar complementos**.

### Uso
1. Haz clic en **MyLiDAR > Generate LiDAR File Report** desde el menú o la barra de herramientas de QGIS.
2. Selecciona un archivo `.las` o `.laz`.
3. Elige los datos que deseas incluir en el informe.
4. Selecciona el formato de salida (TXT, Markdown o PDF).
5. Guarda el informe en la ubicación deseada.

### Dependencias
- `laspy`
- `numpy`
- PyQt5 (incluido con QGIS)
- QGIS 3.x

### Créditos
Desarrollado por Skoolzon3.
Este complemento utiliza `laspy` para analizar archivos LiDAR y `PyQt5` para la integración con la interfaz gráfica.

---
