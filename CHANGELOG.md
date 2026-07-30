# Changelog

All notable changes to **Any Converter** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [1.2.1] - 2026-07-31

### 🚀 Added
- **Multi-Engine Document Fallback Pipeline**:
  - Implemented WordPerfect (`.wpd`) and Microsoft Works (`.wps`) document conversion to PDF.
  - Built an automated multi-suite document conversion fallback cascade across **Microsoft Office (Win32COM)** -> **LibreOffice (Headless CLI)** -> **WPS Office (Win32COM)** -> **`office2pdf`**.
  - Fully mapped Visio (`.vsd`, `.vsdx`), Publisher (`.pub`), and MS Project (`.mpp`) to the Document format group with dedicated UI icons and target options.
- **CorelDRAW (`.cdr`) Vector Support**:
  - Added support for CorelDRAW (`.cdr`) files via an automated multi-tier rendering pipeline (LibreOffice CLI `libcdr` -> Inkscape CLI -> ZIP/RIFF embedded preview stream extraction).

### 🎨 Improved
- **Vector Graphics Separation**:
  - Isolated and cleanly separated **Vector Graphics** (`.svg`, `.ai`, `.eps`, `.ps`, `.cdr`, `.xps`, `.oxps`) into a dedicated `'vector'` format group in `conversion_card.py`, `about_view.py`, and `SUPPORTED_FORMATS.md`, distinct from raster images.
- **About View Layout**:
  - Reordered category cards in `about_view.py` to place 3D & CAD Models directly after Audio.

---

## [1.2.0] - 2026-07-30

### 🚀 Added
- **Streaming & Video Format Expansion**:
  - Added **DASH (`.mpd`), CMAF (`.cmfv`, `.cmfa`), Smooth Streaming (`.ism`, `.ismv`), and SDP (`.sdp`)** support to transcode local or network streams into MP4, MKV, AVI, and other supported formats.
  - Mapped **19 new raw and legacy video extensions** (`.m4v`, `.yuv`, `.divx`, `.xvid`, `.nut`, `.wtv`, `.dvr-ms`, `.mvi`, `.roq`, `.svi`, `.m1v`, `.m2v`, `.ivf`, `.h264`, `.h265`, `.hevc`, `.amv`, `.bik`, `.bk2`) to the UI for native conversion via FFmpeg.
- **Audio Format Expansion**:
  - Mapped **21 new audio formats** (`.opus`, `.oga`, `.voc`, `.au`, `.snd`, `.mp2`, `.mp1`, `.caf`, `.qcp`, `.spx`, `.gsm`, `.tta`, `.ape`, `.tak`, `.mpc`, `.wv`, `.awb`, `.dsd`, `.oma`, `.omg`, `.mka`) allowing native audio extraction and transcoding.
- **Image Format Expansion**:
  - Enabled **HEIC & HEIF Output Support**. You can now export directly to High-Efficiency Image formats natively.
  - Mapped **13 new image formats** (`.tga`, `.pcx`, `.ppm`, `.pgm`, `.pbm`, `.pnm`, `.icns`, `.sgi`, `.dds`, `.dib`, `.xbm`, `.xpm`, `.cur`) for native bidirectional conversion via the Pillow backend engine.
- **E-Book & Comic Expansion**:
  - Built a custom **Comic Book Archive Parser** to support converting `.cbr`, `.cbz`, `.cb7`, and `.cbt` files natively into compiled PDFs or extracting them page-by-page.
- **Font Format Expansion**:
  - Added support for Mac OS X Data Fork Fonts (`.dfont`) via FontTools native indexing.
  - Added support for Embedded OpenType (`.eot`) web fonts for legacy browser support (requires `ttf2eot` and `eot2ttf` tools).
- **3D & CAD Expansion**:
  - Implemented **OpenSCAD (`.scad`)** native script parsing to automatically compile programmatic meshes into `STL` or `OBJ` (requires the OpenSCAD executable).
  - Added Design Web Format (`.dwf`) to the 3D schema as a fallback-supported extension.

### 🎨 Improved
- **UI & About View Sync**: Updated `about_view.py` and `conversion_card.py` format groups to dynamically list all newly added formats in the UI.
- **Documentation**: Updated `SUPPORTED_FORMATS.md` with restructured Video and Image sections.

---

## [1.1.0] - 2026-07-29

### 🚀 Added
- **Vector Graphics Expansion**:
  - Added **Adobe Illustrator (`.ai`)** vector conversion support using PDF compatibility layer parsing via PyMuPDF (`fitz`).
- **Legacy Documents & Presentations Expansion**:
  - Added legacy **OpenOffice Spreadsheet (`.sxc`)** support via Excel COM automation.
  - Implemented **Apple iWork (`.key`, `.pages`, `.numbers`)** to `.pdf` conversion via native `QuickLook` archive extraction, completely bypassing the need for MacOS or heavy dependencies.
  - Added COM automation support for **MS Visio (`.vsd`, `.vsdx`)**, **MS Publisher (`.pub`)**, and **MS Project (`.mpp`)** conversions to PDF.
  - Ensured `.ods`, `.odp`, and `.pps` formats are correctly exposed and handled by the document pipeline.
- **Data & Contacts Expansion**:
  - Wrote a custom native parser for **vCard (`.vcf`)** and **iCalendar (`.ics`)** files. You can now effortlessly drag and drop `.vcf` or `.ics` files and convert them into beautifully structured `.csv`, `.json`, or even formatted `.pdf` tables!
  - Added **Encapsulated PostScript (`.eps` & `.ps`)** conversion support using a multi-stage standalone fallback loader (Pillow -> PyMuPDF -> DOS EPS binary header parser -> Raw TIFF/JPEG stream extractor).
- **Adobe InDesign Preview Support**:
  - Added **InDesign Document (`.indd`)** support via binary scanning for embedded JPEG document previews.
  - Added **InDesign Markup Language (`.idml`)** container extraction for high-resolution embedded thumbnail assets.
- **Native 3D FBX Exporter**:
  - Built a pure-Python, zero-dependency **ASCII FBX 7.4.0 Exporter** (`export_mesh_to_ascii_fbx`).
  - Enabled **OBJ / STL / PLY / GLB / CAD -> FBX** exporting natively without requiring 300 MB `bpy`/Blender dependencies or proprietary Autodesk SDKs.
- **Streaming & Video Format Expansion**:
  - Added **HLS Playlists (`.m3u8`, `.m3u`)** support to transcode local or network streams into MP4, MKV, AVI, etc.
  - Added **MPEG-DASH Segments (`.m4s`)** support.
  - Added **AVCHD & Blu-ray Transport Streams (`.m2ts`, `.mts`)** across the backend pipeline, thumbnail generator, and UI card format selectors.

### 🎨 Improved
- **Documentation**: Updated `SUPPORTED_FORMATS.md` with restructured Vector Graphics and 3D CAD sections.

---

## [1.0.0] - Initial Release

### ✨ Features
- **Cross-Platform Application**: Developed with Python and Flet UI framework featuring an Apple-inspired dark/light responsive theme.
- **Asynchronous Batch Conversion**: Multithreaded job queue (`ConversionJob`, `BatchJobManager`) supporting drag-and-drop batch processing.
- **Comprehensive Format Support**:
  - **Images**: `.png`, `.jpg`, `.jpeg`, `.webp`, `.bmp`, `.gif`, `.heic`, `.heif`, `.psd`, `.ico`, `.tiff`, `.tif`, `.raw`, `.cr2`, `.nef`, `.arw`, `.dng`, `.avif`, `.jxl`.
  - **Video**: `.mp4`, `.mkv`, `.avi`, `.mov`, `.webm`, `.wmv`, `.flv`, `.f4v`, `.mxf`, `.asf`, `.mts`, `.m2ts`, `.vob`, `.ts`, `.3gp`, `.3g2`, `.ogv`, `.rm`, `.rmvb`, `.vro`, `.dat`, `.mpg`, `.mpeg` + Audio Extraction (`.mp3`, `.wav`, `.flac`, `.m4a`, `.aac`).
  - **Audio**: `.mp3`, `.wav`, `.flac`, `.m4a`, `.aac`, `.ogg`, `.aiff`, `.alac`, `.dff`, `.dsf`, `.mqa`, `.mod`, `.s3m`, `.xm`, `.it`, `.wma`, `.ra`, `.bwf`, `.amr`, `.ac3`, `.eac3`, `.thd`, `.dts`, `.dtshd`, `.aob`.
  - **Documents**: `.doc`, `.docx`, `.docm`, `.dot`, `.dotx`, `.dotm`, `.rtf`, `.txt`, `.log`, `.odt`, `.mht`, `.html`, `.htm`, `.xls`, `.xlsx`, `.xlsm`, `.xlsb`, `.ods`, `.ppt`, `.pptx`, `.pptm`, `.pps`, `.odp` -> `.pdf` conversion via MS Office / open-source fallbacks.
  - **Data & Config**: Bidirectional conversion between `.json`, `.yaml`, `.yml`, `.csv`, `.xml`, and export to `.pdf`.
  - **PDFs & E-Books**: `.pdf`, `.epub`, `.mobi`, `.azw3`, `.azw`, `.iba`, `.djvu`, `.djv` -> `.pdf` or page-by-page images.
  - **3D Models & CAD**: `.obj`, `.stl`, `.ply`, `.glb`, `.gltf`, `.off`, `.dae`, `.fbx`, `.step`, `.stp`, `.iges`, `.igs`, `.dxf`, `.dwg`, `.3mf` -> `.obj`, `.stl`, `.ply`, `.glb`, `.gltf`, `.off`, `.dae`.
  - **Databases & SQL**: `.sql`, `.db`, `.sqlite`, `.sqlite3`, `.mdb`, `.accdb` -> `.sql`, `.sqlite`, `.json`, `.csv`, `.xml`, `.yaml`.
  - **GIS & Geospatial**: `.geojson`, `.kml`, `.kmz`, `.gpx`, `.shp` -> `.geojson`, `.kml`, `.gpx`, `.csv`, `.json`.
  - **Archives & Disk Images**: `.zip`, `.rar`, `.7z`, `.tar`, `.gz`, `.tgz`, `.bz2`, `.xz`, `.iso`, `.img`, `.mds`, `.mdf` -> `.zip`, `.7z`, `.tar`, `.tar.gz`, `.tar.bz2`, `.tar.xz`, `.iso`, or extracted folder.
  - **Subtitles**: `.srt`, `.vtt`, `.ass`, `.ssa`, `.sub`, `.scc` -> `.srt`, `.vtt`, `.ass`, `.sub`, `.scc`, `.txt`.
  - **Web Fonts**: `.ttf`, `.otf`, `.woff`, `.woff2`.
  - **Vector Graphics**: `.svg` -> `.png`, `.jpg`, `.jpeg`, `.pdf`, `.svg`.
- **System Utilities**: Live progress indicators, thumbnail caching engine, history manager, and user settings panel.
