# Supported Formats

Any Converter supports a wide range of file formats across different media and document types. Below is a comprehensive list of all supported input extensions and what formats they can be converted into.

## 🖼️ Images
**Supported Inputs:**
- **Standard & Web:** `.png`, `.jpg`, `.jpeg`, `.webp`, `.bmp`, `.gif`, `.heic`, `.heif`, `.avif`, `.jxl`
- **Icons & UI:** `.ico`, `.icns`, `.cur`, `.xbm`, `.xpm`
- **Professional & Raw:** `.tiff`, `.tif`, `.psd`, `.raw`, `.cr2`, `.nef`, `.arw`, `.dng`, `.indd`, `.idml`, `.raf`, `.pef`, `.exr`, `.dpx`
- **Legacy & Specialized:** `.tga`, `.pcx`, `.ppm`, `.pgm`, `.pbm`, `.pnm`, `.sgi`, `.dds`, `.dib`

**Can be converted to:**
- **Standard & Web:** `.png`, `.jpg`, `.jpeg`, `.webp`, `.bmp`, `.gif`, `.heic`, `.heif`, `.avif`, `.jxl`
- **Icons & UI:** `.ico`, `.icns`, `.cur`, `.xbm`, `.xpm`
- **Professional & Specialized:** `.tiff`, `.tif`, `.tga`, `.pcx`, `.ppm`, `.pgm`, `.pbm`, `.pnm`, `.sgi`, `.dds`, `.dib`

*(Note: `.psd`, `.indd`, `.idml`, `.raw`, `.cr2`, `.nef`, `.arw`, `.dng`, `.raf`, `.pef` are supported as inputs for conversion by extracting their image data/previews, but cannot be exported to).*

## 🎥 Video
**Supported Inputs:**
- **Standard & Web:** `.mp4`, `.mkv`, `.avi`, `.mov`, `.webm`, `.wmv`, `.flv`, `.f4v`, `.3gp`, `.3g2`, `.m4v`, `.swf`
- **Broadcast & Professional:** `.mxf`, `.asf`, `.mts`, `.m2ts`, `.ts`, `.m2v`, `.m1v`, `.mpg`, `.mpeg`, `.vob`, `.vro`, `.wtv`, `.dvr-ms`
- **Streaming & Network:** `.m3u8`, `.m3u`, `.m4s`, `.mpd`, `.fmp4`, `.cmfv`, `.cmfa`, `.f4f`, `.ism`, `.ismc`, `.ismv`, `.isma`, `.sdp`
- **Raw Bitstreams:** `.h264`, `.h265`, `.hevc`, `.yuv`
- **Legacy & Specialized:** `.ogv`, `.rm`, `.rmvb`, `.dat`, `.divx`, `.xvid`, `.nut`, `.mvi`, `.roq`, `.svi`, `.ivf`, `.amv`, `.bik`, `.bk2`

**Can be converted to:**
- **Standard Video:** `.mp4`, `.mkv`, `.avi`, `.mov`, `.webm`, `.wmv`, `.flv`, `.f4v`, `.3gp`, `.3g2`, `.m4v`
- **Broadcast & Professional:** `.mxf`, `.asf`, `.mts`, `.m2ts`, `.ts`, `.m2v`, `.m1v`, `.mpg`, `.mpeg`, `.vob`
- **Streaming Segments:** `.m3u8`, `.m3u`, `.m4s`, `.mpd`, `.fmp4`, `.cmfv`, `.cmfa`, `.f4f`, `.ismv`, `.isma`
- **Raw Bitstreams:** `.h264`, `.h265`, `.hevc`, `.yuv`
- **Legacy & Specialized:** `.ogv`, `.rm`, `.rmvb`, `.nut`
- **Audio Extraction:** `.mp3`, `.wav`, `.flac`, `.m4a`, `.aac`, `.opus`, `.mka`, `.ogg`

*(Note: Supports native ingestion of playlists (`.m3u8`, `.mpd`, `.ism`) and segmentation mapping to standalone containers).*

## 🎵 Audio
**Supported Inputs:**
- **Standard & Web:** `.mp3`, `.wav`, `.flac`, `.m4a`, `.aac`, `.ogg`, `.opus`, `.mka`, `.m4b`, `.m4r`
- **Lossless & High-Res:** `.aiff`, `.alac`, `.ape`, `.wv`, `.tta`, `.tak`, `.dsd`, `.dff`, `.dsf`, `.mqa`
- **Broadcast & Telephony:** `.wma`, `.amr`, `.awb`, `.spx`, `.gsm`, `.qcp`, `.voc`
- **Surround & Cinema:** `.ac3`, `.eac3`, `.thd`, `.dts`, `.dtshd`
- **Legacy & Tracker:** `.mod`, `.s3m`, `.xm`, `.it`, `.ra`, `.bwf`, `.aob`, `.oga`, `.au`, `.snd`, `.mp2`, `.mp1`, `.caf`, `.mpc`, `.oma`, `.omg`

**Can be converted to:**
- **Standard & Web:** `.mp3`, `.wav`, `.flac`, `.m4a`, `.aac`, `.opus`, `.mka`, `.oga`
- **Lossless & High-Res:** `.aiff`, `.alac`, `.ape`, `.wv`, `.tta`
- **Broadcast & Telephony:** `.wma`, `.amr`, `.spx`, `.gsm`, `.voc`
- **Surround & Cinema:** `.ac3`, `.eac3`, `.thd`, `.dts`
- **Legacy & Other:** `.au`, `.snd`, `.mp2`, `.mp1`, `.caf`

*(Note: High-Res and Tracker formats like `.dsd`, `.mqa`, `.mod` are supported as inputs but naturally downmixed or PCM-converted during output due to architectural/encoder bounds).*

## 📄 Documents
**Supported Inputs:** `.doc`, `.docx`, `.docm`, `.dot`, `.dotx`, `.dotm`, `.rtf`, `.txt`, `.log`, `.odt`, `.mht`, `.html`, `.htm`, `.wpd`, `.wps`, `.xls`, `.xlsx`, `.xlsm`, `.xlsb`, `.ods`, `.sxc`, `.ppt`, `.pptx`, `.pptm`, `.pps`, `.odp`, `.key`, `.pages`, `.numbers`, `.xps`, `.oxps`, `.vsd`, `.vsdx`, `.pub`, `.mpp`
**Can be converted to:** `.pdf`

*(Note: Legacy word processing formats like `.wpd` (WordPerfect) and `.wps` (MS Works) are supported using an automatic multi-engine fallback chain across Microsoft Office, LibreOffice, and WPS Office).*

## 📊 Data, Config & Contacts
**Supported Inputs:** `.json`, `.yaml`, `.yml`, `.csv`, `.xml`, `.vcf`, `.ics`
**Can be converted to:** `.json`, `.yaml`, `.yml`, `.csv`, `.xml`, `.pdf`
*(Note: Supports bidirectional conversion between JSON, YAML, CSV, XML, and exports vCard Contacts (.vcf) and iCalendar events (.ics) into structured tabular data or PDF).*

## 📚 PDFs & E-Books
**Supported Inputs:** `.pdf`, `.epub`, `.mobi`, `.azw3`, `.azw`, `.iba`, `.djvu`, `.djv`, `.cbr`, `.cbz`, `.cb7`, `.cbt`, `.chm`
**Can be converted to:** `.pdf`, `.png`, `.jpg`, `.jpeg`, `.webp`
*Note: E-Book and Comic formats (`.epub`, `.mobi`, `.cbr`, `.cbz`, etc.) can be converted directly into `.pdf` documents or extracted page-by-page as images.*

## 🧊 3D Models & CAD
**Supported Inputs:** `.obj`, `.stl`, `.ply`, `.glb`, `.gltf`, `.off`, `.dae`, `.fbx`, `.step`, `.stp`, `.iges`, `.igs`, `.dxf`, `.dwg`, `.3mf`, `.scad`, `.dwf`, `.3ds`, `.blend`, `.x`, `.lwo`, `.lws`, `.md5mesh`, `.smd`, `.vta`, `.ogex`, `.3d`, `.b3d`, `.q3d`, `.q3s`, `.nff`, `.ter`, `.mdl`, `.xml`, `.ifc`, `.x3d`, `.x3db`, `.csm`, `.bvh`, `.ase`, `.cob`, `.scn`, `.ac`, `.ms3d`, `.mqo`, `.ndo`, `.irr`, `.irrmesh`, `.pmx`
**Can be converted to:** `.obj`, `.stl`, `.ply`, `.glb`, `.gltf`, `.off`, `.dae`, `.fbx`, `.x`, `.stp`
*(Note: Powered natively by the Assimp Library through a transparent ctypes wrapper, allowing full multi-format 3D conversion while preserving materials, textures, and binary FBX node structures. Legacy CAD and OpenSCAD formats are safely handled via specialized secondary parsers. If Assimp fails on a format, the app safely falls back to Trimesh).*


## 🗄️ Databases & SQL
**Supported Inputs:** `.sql`, `.db`, `.sqlite`, `.sqlite3`, `.mdb`, `.accdb`
**Can be converted to:** `.sql`, `.sqlite`, `.json`, `.csv`, `.xml`, `.yaml`
*(Note: Converts database schemas and tables between SQLite databases, SQL dump files, and structured data formats).*

## 🗺️ GIS & Geospatial
**Supported Inputs:** `.geojson`, `.kml`, `.kmz`, `.gpx`, `.shp`
**Can be converted to:** `.geojson`, `.kml`, `.gpx`, `.csv`, `.json`
*(Note: Converts spatial features, waypoints, tracks, and shapefiles bidirectionally).*

## 📦 Archives & Disk Images
**Supported Inputs:** `.zip`, `.rar`, `.7z`, `.tar`, `.gz`, `.tgz`, `.bz2`, `.tbz2`, `.xz`, `.txz`, `.iso`, `.img`, `.mds`, `.mdf`, `.cab`
**Supported Targets:** `zip`, `7z`, `tar`, `tar.gz`, `tar.bz2`, `tar.xz`, `iso`, `folder`
*(Note: Extracts compressed archives, ISO optical images, and MDF/MDS disk images directly into a folder or repacks into clean archives).*

## 💬 Subtitles
**Supported Inputs:** `.srt`, `.vtt`, `.ass`, `.ssa`, `.sub`, `.scc`
**Can be converted to:** `.srt`, `.vtt`, `.ass`, `.sub`, `.scc`, `.txt`
*(Note: Supports bidirectional conversion between all major subtitle and closed caption formats).*

## 🔤 Fonts
**Supported Inputs:** `.ttf`, `.otf`, `.woff`, `.woff2`, `.eot`, `.dfont`
**Can be converted to:** `.ttf`, `.otf`, `.woff`, `.woff2`, `.eot`
*(Note: Supports native bidirectional conversion between TrueType, OpenType, WOFF, WOFF2, and EOT web fonts, as well as extraction from Mac OS X Data Fork Fonts).*

## ✒️ Vector Graphics
**Supported Inputs:** `.svg`, `.ai`, `.eps`, `.ps`, `.cdr`, `.xps`, `.oxps`
**Can be converted to:** `.png`, `.jpg`, `.jpeg`, `.webp`, `.pdf`, `.svg`

---
*(Note: `.ai` vector files are supported via PDF compatibility layers, `.eps` and `.ps` files are rendered natively via PyMuPDF or embedded stream extraction, CorelDRAW (`.cdr`) files are converted via LibreOffice/Inkscape CLI or zip/RIFF embedded thumbnail extraction, and `.xps`/`.oxps` are processed directly as vector documents).*
