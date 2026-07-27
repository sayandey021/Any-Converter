# Contributing to Any Converter

Thank you for your interest in contributing to Any Converter! We welcome contributions of all sizes—whether it's fixing bugs, improving documentation, suggesting new features, or adding converters for entirely new file formats.

Please take a moment to review this document to ensure a smooth contribution process.

---

## 🛠️ Developer Environment Setup

1. **Fork and Clone the Repository**
   Fork the repository on GitHub, then clone your fork locally:
   ```bash
   git clone https://github.com/<your-username>/Any-Converter.git
   cd Any-Converter
   ```

2. **Set Up a Virtual Environment**
   ```bash
   python -m venv venv
   # Activate on Windows:
   venv\Scripts\activate
   # Activate on macOS/Linux:
   source venv/bin/activate
   ```

3. **Install Development Dependencies**
   Install standard packages and quality check tools:
   ```bash
   pip install -r requirements.txt
   pip install ruff black pytest
   ```

---

## 📐 Coding Standards

To maintain code readability and reliability across the project, we adhere to the following rules:

- **Style Guide:** We follow **PEP 8** guidelines.
- **Formatter & Linter:** We use **Ruff** for linting and **Black** for formatting. Run the following checks before committing:
  ```bash
  black .
  ruff check .
  ```
- **Type Hints:** Whenever writing python functions, please use type annotations (e.g., `def convert_image(source: str, target: str) -> bool:`).
- **Security:** Do not commit hardcoded credentials, API keys, or certificates (`.pfx` files). Ensure they are kept in local configurations or environment variables.

---

## 🧪 Testing Your Changes

We write utility test scripts to verify converters. 
- You can create scratch testing scripts to verify converters in the `scratch/` directory. Note that the entire `scratch/` directory is ignored by git to keep your local testing workspace clean.
- Ensure that any new converter you write is verified with sample test files before submitting your pull request.

---

## 🚀 Pull Request Process

1. **Create a Feature Branch:**
   Use descriptive branch names (e.g., `feature/add-webp-encoder` or `bugfix/fix-mobi-converter`).
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. **Commit Changes:**
   Write clear, concise commit messages. Reference issue numbers where applicable.
   ```bash
   git commit -m "feat(converter): add support for XYZ format"
   ```
3. **Push to Your Fork:**
   ```bash
   git push origin feature/your-feature-name
   ```
4. **Open a Pull Request (PR):**
   Open a PR against the `main` branch of the main repository. Fill out the pull request template completely, outlining:
   - What changes were made.
   - The motivation behind the changes.
   - Any manual or automated tests performed.
