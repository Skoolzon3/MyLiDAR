# FAQ

[Español](#español) | [English](#english)

## English

### How do I fix the "LazBackend.Lazrs is not available" error?

Error message example:

```text
CRITICAL ERROR EXCEPTION: An error occurred during vegetation classification:
The 'LazBackend.Lazrs' is not available
FINAL STATUS: FAILED
Error: The 'LazBackend.Lazrs' is not available
```

This error occurs when the required LAZ file processing libraries (lazrs and laspy) are not installed in the same Python environment that QGIS uses. Even if you installed them via the OSGeo4W Shell, QGIS may not recognize those installations because it often runs in an isolated Python environment.

**Solution**: Install the missing libraries directly into QGIS’s Python environment. You can do this using the command below, adjusting the path if your QGIS version or installation path differs.

```bash
"C:\Program Files\QGIS 3.44.6\apps\Python312\python.exe" -m pip install lazrs laspy
```

Once the installation completes, restart QGIS and rerun the tool. The process should now run without errors.

## Español

### ¿Cómo puedo solucionar el error "LazBackend.Lazrs no está disponible"?

Ejemplo del mensaje de error:

```text
CRITICAL ERROR EXCEPTION: An error occurred during vegetation classification:
The 'LazBackend.Lazrs' is not available
FINAL STATUS: FAILED
Error: The 'LazBackend.Lazrs' is not available
```

Este error ocurre cuando las bibliotecas necesarias para procesar archivos LAZ (lazrs y laspy) no están instaladas en el mismo entorno de Python que utiliza QGIS. Aunque se hayan instalado mediante OSGeo4W Shell, es posible que QGIS no las reconozca porque suele usar un entorno de Python independiente.

**Solución**: Instala las bibliotecas que faltan directamente en el entorno de Python de QGIS. Puedes hacerlo con el siguiente comando, ajustando la ruta según tu versión o instalación de QGIS.

```bash
"C:\Program Files\QGIS 3.44.6\apps\Python312\python.exe" -m pip install lazrs laspy
```

Una vez completada la instalación, reinicia QGIS y vuelve a ejecutar la herramienta. El proceso debería funcionar sin errores.
