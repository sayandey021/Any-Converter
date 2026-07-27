# 🗺️ Any Converter Roadmap

This document outlines the development direction and upcoming features planned for **Any Converter**. We prioritize offline speed, format coverage, and user interface elegance.

---

## 📅 Roadmap Overview

### 🚀 Phase 1: Core Enhancements & UI Polish (Short-term)
* **🔧 Native Thumbnail Previews:** Enhance image/video thumbnail loaders to reduce UI thread blocking on heavy folders.
* **📈 Real-time Progress Granularity:** Show percentages for video processing steps (e.g., encoding pass 1 vs. pass 2) in Flet progressbars.
* **🗂️ Default Conversion Presets:** Allow users to save preferred conversion profiles (e.g., "Web-Optimized Image: WebP, 80% quality").
* **🔄 Parallel Job Limit Settings:** Let users choose the number of concurrent conversion threads based on their CPU cores.

---

### 🎨 Phase 2: Expanded Formats & Custom Decoders (Medium-term)
* **📚 Refined E-Book Layouts:** Improve the PDF output formatting when converting from `.epub` and `.mobi`.
* **💬 Extended Subtitle Engines:** Support character encoding conversions (e.g., UTF-8 to ISO-8859-1) for subtitle files.
* **🧊 CAD/3D Expansion:** Integrate FBX/STEP file translations directly without requiring heavy external installation components.
* **🔒 Encrypted Archives:** Support password-protected ZIP and 7Z unpacks directly in the GUI.

---

### 🛠️ Phase 3: Productivity Utilities (Long-term)
* **🔤 Batch Renamer:** A tool to bulk rename files before or after conversion (e.g., lowercase names, prefixing dates).
* **📄 PDF Toolkit:**
  * Compress PDF files.
  * Merge multiple PDFs into a single document.
  * Extract specific pages or image assets from a PDF.
* **👁️ Offline OCR (Optical Character Recognition):** Extract text from scanned documents/images into `.txt` or searchable `.pdf` documents using lightweight on-device engines.

---

### 🌐 Phase 4: Integration & Cloud Sync (Optional)
* **☁️ Cloud Provider Storage:** Add optional connectors for Google Drive, OneDrive, and Dropbox to directly download source files, convert them locally, and upload results.
* **🤖 Command Line Interface (CLI):** Expose Any Converter’s core conversion engine as a standalone CLI tool for automated shell scripting.
