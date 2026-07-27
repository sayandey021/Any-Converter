# Supported Formats

Any Converter supports a wide range of file formats across different media and document types. Below is a comprehensive list of all supported input extensions and what formats they can be converted into.

## 🖼️ Images
**Supported Inputs:** `.png`, `.jpg`, `.jpeg`, `.webp`, `.bmp`, `.gif`, `.heic`, `.heif`, `.psd`, `.ico`, `.tiff`, `.tif`, `.raw`, `.cr2`, `.nef`, `.arw`, `.dng`, `.avif`, `.jxl`
**Can be converted to:** `.png`, `.jpg`, `.jpeg`, `.webp`, `.bmp`, `.gif`, `.ico`, `.tiff`, `.tif`, `.avif`, `.jxl`

*(Note: `.heic`, `.heif`, `.psd`, `.raw`, `.cr2`, `.nef`, `.arw`, `.dng` are supported as inputs for conversion, but cannot be exported to).*

## 🎥 Video
**Supported Inputs:** `.mp4`, `.mkv`, `.avi`, `.mov`, `.webm`, `.wmv`, `.flv`, `.f4v`, `.mxf`, `.asf`, `.mts`, `.m2ts`, `.vob`, `.ts`, `.3gp`, `.3g2`, `.ogv`, `.rm`, `.rmvb`, `.vro`, `.dat`, `.mpg`, `.mpeg`
**Can be converted to:**
- **Video:** `.mp4`, `.mkv`, `.avi`, `.mov`, `.webm`, `.wmv`, `.flv`, `.f4v`, `.mxf`, `.asf`, `.mts`, `.m2ts`, `.vob`, `.ts`, `.3gp`, `.3g2`, `.ogv`, `.rm`, `.rmvb`, `.mpg`, `.mpeg`
- **Audio Extraction:** `.mp3`, `.wav`, `.flac`, `.m4a`, `.aac`

## 🎵 Audio
**Supported Inputs:** `.mp3`, `.wav`, `.flac`, `.m4a`, `.aac`, `.ogg`, `.aiff`, `.alac`, `.dff`, `.dsf`, `.mqa`, `.mod`, `.s3m`, `.xm`, `.it`, `.wma`, `.ra`, `.bwf`, `.amr`, `.ac3`, `.eac3`, `.thd`, `.dts`, `.dtshd`, `.aob`
**Can be converted to:** `.mp3`, `.wav`, `.flac`, `.m4a`, `.aac`, `.aiff`, `.alac`, `.wma`, `.amr`, `.ac3`, `.eac3`, `.thd`, `.dts`

*(Note: `.dff`, `.dsf`, `.mqa`, `.mod`, `.s3m`, `.xm`, `.it`, `.ra`, `.bwf`, `.dtshd`, `.aob` are supported as inputs for conversion, but cannot be exported to directly due to encoder limitations or format nature).*

## 📄 Documents
**Supported Inputs:** `.doc`, `.docx`, `.docm`, `.dot`, `.dotx`, `.dotm`, `.rtf`, `.txt`, `.log`, `.odt`, `.mht`, `.html`, `.htm`, `.xls`, `.xlsx`, `.xlsm`, `.xlsb`, `.ods`, `.ppt`, `.pptx`, `.pptm`, `.pps`, `.odp`
**Can be converted to:** `.pdf`

*(Note: Requires Microsoft Office to be installed for legacy formats. Falls back to internal open-source converters for modern formats).*

## 📊 Data & Config
**Supported Inputs:** `.json`, `.yaml`, `.yml`, `.csv`, `.xml`
**Can be converted to:** `.json`, `.yaml`, `.yml`, `.csv`, `.xml`, `.pdf`
*(Note: Supports bidirectional conversion between JSON, YAML, CSV, and XML structured formats, as well as export to PDF).*

## 📚 PDFs & E-Books
**Supported Inputs:** `.pdf`, `.epub`, `.mobi`, `.azw3`, `.azw`, `.iba`, `.djvu`, `.djv`
**Can be converted to:** `.pdf`, `.png`, `.jpg`, `.jpeg`, `.webp`
*Note: E-Book formats (`.epub`, `.mobi`, `.azw3`, `.iba`, `.djvu`) can be converted directly into `.pdf` documents or extracted page-by-page as images.*

## 🧊 3D Models & CAD
**Supported Inputs:** `.obj`, `.stl`, `.ply`, `.glb`, `.gltf`, `.off`, `.dae`, `.fbx`, `.step`, `.stp`, `.iges`, `.igs`, `.dxf`, `.dwg`, `.3mf`
**Can be converted to:** `.obj`, `.stl`, `.ply`, `.glb`, `.gltf`, `.off`, `.dae`
*(Note: Supports 3D meshes and CAD formats. `.fbx` is supported as an input format via FBX2glTF).*

## 🗄️ Databases & SQL
**Supported Inputs:** `.sql`, `.db`, `.sqlite`, `.sqlite3`, `.mdb`, `.accdb`
**Can be converted to:** `.sql`, `.sqlite`, `.json`, `.csv`, `.xml`, `.yaml`
*(Note: Converts database schemas and tables between SQLite databases, SQL dump files, and structured data formats).*

## 🗺️ GIS & Geospatial
**Supported Inputs:** `.geojson`, `.kml`, `.kmz`, `.gpx`, `.shp`
**Can be converted to:** `.geojson`, `.kml`, `.gpx`, `.csv`, `.json`
*(Note: Converts spatial features, waypoints, tracks, and shapefiles bidirectionally).*

## 📦 Archives & Disk Images
**Supported Inputs:** `.zip`, `.rar`, `.7z`, `.tar`, `.gz`, `.tgz`, `.bz2`, `.tbz2`, `.xz`, `.txz`, `.iso`, `.img`, `.mds`, `.mdf`
**Supported Targets:** `zip`, `7z`, `tar`, `tar.gz`, `tar.bz2`, `tar.xz`, `iso`, `folder`
*(Note: Extracts compressed archives, ISO optical images, and MDF/MDS disk images directly into a folder or repacks into clean archives).*

## 💬 Subtitles
**Supported Inputs:** `.srt`, `.vtt`, `.ass`, `.ssa`, `.sub`, `.scc`
**Can be converted to:** `.srt`, `.vtt`, `.ass`, `.sub`, `.scc`, `.txt`
*(Note: Supports bidirectional conversion between all major subtitle and closed caption formats).*

## 🔤 Fonts
**Supported Inputs:** `.ttf`, `.otf`, `.woff`, `.woff2`
**Can be converted to:** `.ttf`, `.otf`, `.woff`, `.woff2`
*(Note: Supports native bidirectional conversion between TrueType, OpenType, WOFF, and WOFF2 web fonts).*

## ✒️ Vector Graphics
**Supported Inputs:** `.svg`
**Can be converted to:** `.png`, `.jpg`, `.jpeg`, `.pdf`, `.svg`

---
*Note: `.ai` and `.eps` vector formats have been removed from support because they do not natively support independent processing without heavy external dependencies.*
