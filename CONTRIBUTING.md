# Contributing to AegisClinical

Thank you for your interest in contributing to **AegisClinical**! We welcome contributions from software engineers, healthcare practitioners, informaticians, and medical AI researchers.

---

## Code of Conduct

All contributors and participants must adhere to our [Code of Conduct](CODE_OF_CONDUCT.md). Please treat all members of the community with respect and empathy.

---

## Getting Started

### 1. Fork & Clone
```bash
git clone https://github.com/YOUR_USERNAME/Multi-Agent-Clinical-Support.git
cd Multi-Agent-Clinical-Support
git checkout -b feature/your-feature-name
```

### 2. Environment Setup
You can use the one-click initialization script:
```bash
./start.sh
```
Or set up manually:
```bash
# Python Virtual Environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Frontend Development
cd frontend
npm install
npm run dev
```

### 3. Verify the Test Suite
Before making any changes, confirm that all 17 tests pass:
```bash
pytest tests/ -v
```

---

## Development Guidelines

### 1. The Neuro-Symbolic Principle
* **Clinical Math & Contraindications MUST be deterministic**: Never delegate arithmetic, KDIGO staging cutoffs, or drug contraindications to statistical LLM prompts. All clinical boundary rules belong in [`src/rules.py`](src/rules.py).
* **LLMs are strictly for synthesis**: Local SLMs (Ollama `llama3.2:3b`) are used strictly to translate deterministic findings into readable, actionable physician narratives.

### 2. Adding a New Clinical Rule
When proposing a new clinical rule (e.g. QT-prolongation drug interactions or hypernatremia panic thresholds):
1. **Cite the Medical Source**: Include the clinical guideline (e.g. KDIGO, AHA/ACC, FDA label) in docstrings.
2. **Write Unit Tests First**: Add test cases in [`tests/test_rules.py`](tests/test_rules.py) covering normal, borderline, and critical values.
3. **Implement Rule**: Add the evaluation function in [`src/rules.py`](src/rules.py).
4. **Update `CONTEXT.md`**: As mandated by our living documentation guidelines, keep [`CONTEXT.md`](CONTEXT.md) synchronized with any rule changes.

### 3. Coding Standards
* **Python**: Follow PEP 8 style guidelines. Ensure type annotations are clean.
* **Frontend**: React 19 functional components with hooks. Use CSS custom properties from [`frontend/src/index.css`](frontend/src/index.css) for colors and spacing. Never use arbitrary inline styling or layout-shifting loaders.

---

## Submitting a Pull Request (PR)

1. Ensure all tests pass: `pytest tests/ -v`.
2. Ensure frontend compiles cleanly: `npm --prefix frontend run build`.
3. Commit with concise, descriptive commit messages (e.g. `feat(rules): add QT prolongation DDI checks`).
4. Push to your fork and open a Pull Request against the `main` branch.
5. Fill out the [Pull Request Template](.github/PULL_REQUEST_TEMPLATE.md).

---

## Need Help?
Feel free to open an Issue on GitHub for questions, architectural discussions, or clinical feedback!
