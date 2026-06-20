#!/usr/bin/env python3
"""
Context inventory helper for review-driven-development.

Role:
- Inspect a project tree before planning.
- Detect source languages, Markdown docs, tests, build files, and data files.
- Save `.codex/review-driven-development/context-inventory.json`.
- Recommend critical-only subagent roles.

Extension notes:
- Scanning is bounded and skips common generated directories.
- Dependency graph extraction and deeper package-version analysis remain
  optional project-specific extensions.
- CSV schema sampling is delegated to `data_profile.py`.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping

STATE_DIR = Path(".codex") / "review-driven-development"
CONTEXT_INVENTORY_FILE = "context-inventory.json"
CONTEXT_CACHE_FILE = "context-cache.json"
CONTEXT_PACK_FILE = "context-pack.md"
CONTEXT_SEMANTIC_INDEX_FILE = "context-semantic-index.json"
BOOTSTRAP_BEGIN = "<!-- review-driven-development:context-bootstrap:begin -->"
BOOTSTRAP_END = "<!-- review-driven-development:context-bootstrap:end -->"
LANG_BY_EXT = {
    ".py": "python", ".js": "javascript", ".jsx": "javascript/react", ".ts": "typescript", ".tsx": "typescript/react",
    ".java": "java", ".kt": "kotlin", ".swift": "swift", ".go": "go", ".rs": "rust", ".rb": "ruby",
    ".php": "php", ".cs": "csharp", ".cpp": "cpp", ".cc": "cpp", ".cxx": "cpp", ".c": "c",
    ".h": "c/cpp header", ".hpp": "c/cpp header", ".sql": "sql", ".r": "r", ".ipynb": "notebook",
}
DOC_EXTS = {".md", ".mdx", ".rst", ".txt"}
DATA_EXTS = {".csv", ".tsv", ".jsonl", ".parquet", ".xlsx", ".xls", ".ndjson", ".log"}
INDEX_TEXT_EXTS = set(LANG_BY_EXT) | DOC_EXTS | {".toml", ".json", ".yaml", ".yml"}
TEST_HINTS = ("test", "spec", "__tests__", "tests")
BUILD_FILES = {
    "package.json", "pnpm-lock.yaml", "yarn.lock", "package-lock.json", "pyproject.toml", "requirements.txt",
    "Pipfile", "Cargo.toml", "go.mod", "pom.xml", "build.gradle", "Makefile", "Dockerfile",
    "docker-compose.yml", "compose.yml", "tsconfig.json", "vite.config.ts", "next.config.js",
}
SKIP_DIRS = {".git", ".codex", "node_modules", ".venv", "venv", "dist", "build", "target", ".next", ".cache", "coverage", ".pytest_cache", "__pycache__"}
PRIORITY_DOC_NAMES = {
    "AGENTS.MD", "README.MD", "README.KO.MD", "README.EN.MD", "SKILL.MD",
    "VALIDATION.MD", "REVIEW_NOTES.MD", "CHANGELOG.MD", "CONTRIBUTING.MD",
    "PYPROJECT.TOML", "PACKAGE.JSON",
}
STOPWORDS = {
    "about", "after", "again", "also", "and", "are", "because", "before", "build", "check", "class", "code", "could",
    "data", "default", "does", "file", "for", "from", "function", "have", "into", "only", "project", "return",
    "script", "should", "state", "test", "tests", "that", "the", "this", "todo", "true", "using", "when", "with",
    "work", "would", "그리고", "대한", "문서", "상태", "수행", "요구", "작업", "테스트", "파일",
}
DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
INVENTORY_MODES: Dict[str, Dict[str, int]] = {
    "fast": {
        "max_files": 600,
        "docs": 40,
        "data_files": 40,
        "tests": 80,
        "build_files": 40,
        "source_files_sample": 100,
        "doc_snippet_count": 0,
        "doc_snippet_chars": 0,
    },
    "standard": {
        "max_files": 1500,
        "docs": 80,
        "data_files": 80,
        "tests": 120,
        "build_files": 60,
        "source_files_sample": 180,
        "doc_snippet_count": 4,
        "doc_snippet_chars": 700,
    },
    "deep": {
        "max_files": 5000,
        "docs": 500,
        "data_files": 500,
        "tests": 500,
        "build_files": 100,
        "source_files_sample": 500,
        "doc_snippet_count": 20,
        "doc_snippet_chars": 2000,
    },
}
SECURITY_MARKERS = (
    ".env", "api_key", "access_token", "auth", "credential", "jwt", "login",
    "oauth", "password", "permission", "policy", "refresh_token", "secret",
    "security",
)
ROLE_PROFILES: List[Dict[str, Any]] = [
    {
        "role": "context-discovery",
        "purpose": "Inventory, cache reuse, context-pack generation, semantic lookup, and bootstrap guidance.",
        "patterns": ("context_inventory.py", "context-pack", "context-cache", "context-semantic-index", "AGENTS.md"),
        "queries": ("context cache semantic search file discovery", "bootstrap context pack stale inventory"),
    },
    {
        "role": "workflow-orchestration",
        "purpose": "High-level RDD phases, first-run routing, TODO execution flow, validation, docs, and command UX.",
        "patterns": ("workflow_runner.py", "workflow.md", "commands"),
        "queries": ("workflow phase validation documentation improvement", "run once preplan execution commands"),
    },
    {
        "role": "critic-briefs",
        "purpose": "Critical-only subagent role selection, depth caps, brief construction, and finding templates.",
        "patterns": ("subagent_brief_builder.py", "subagent-roles.md", "critic", "brief"),
        "queries": ("critic role depth brief context cap", "subagent findings validation critic"),
    },
    {
        "role": "todo-ledger",
        "purpose": "Append-only TODO lifecycle, evidence, review records, documentation gates, and completion checks.",
        "patterns": ("todo_manager.py", "todo-policy.md", "todos.jsonl", "TODO"),
        "queries": ("todo evidence review documentation completion gate", "in progress pending blocked completed"),
    },
    {
        "role": "quality-validation",
        "purpose": "Quality gate command selection, validation reports, smoke workflow, and regression tests.",
        "patterns": ("quality_gate.py", "self_test.py", "test_smoke_workflow.py", "tests/", "VALIDATION.md"),
        "queries": ("quality gate validation report pytest smoke workflow", "regression tests completion evidence"),
    },
    {
        "role": "state-defaults",
        "purpose": "Project defaults, first-run profile storage, requirement packet analysis, and persistent state.",
        "patterns": ("rdd_state.py", "requirement_analyzer.py", "first-run", "defaults.json", "profile.md"),
        "queries": ("first run defaults profile requirement packet", "project assumptions saved state"),
    },
    {
        "role": "external-skill-routing",
        "purpose": "Optional companion skill registry, external skill URLs, and source-grounded skill invocation policy.",
        "patterns": ("external_skill_registry.py", "external-skills", "external-skill-links", "internal-skill-map"),
        "queries": ("external skill registry companion skill source link", "agentic rag optional skills"),
    },
    {
        "role": "docs-contracts",
        "purpose": "User-facing README, script contracts, state schema, documentation policy, and contribution rules.",
        "patterns": ("README", "script-contracts.md", "function-scaffold.md", "state-schema.md", "documentation-policy.md", "CONTRIBUTING.md"),
        "queries": ("script contract state schema documentation policy", "readme install usage validation"),
    },
]


def now_iso() -> str:
    """Return a stable UTC timestamp."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def should_skip(path: Path) -> bool:
    """Return True if any path component should be skipped."""
    return any(part in SKIP_DIRS for part in path.parts)


def iter_files(root: Path, max_files: int) -> Iterable[Path]:
    """Yield files under root with a hard scan cap."""
    count = 0
    for path in root.rglob("*"):
        try:
            rel_for_skip = path.relative_to(root)
        except ValueError:
            rel_for_skip = path
        if should_skip(rel_for_skip):
            continue
        if path.is_file():
            yield path
            count += 1
            if count >= max_files:
                return


def classify_file(file_path: Path, root: Path) -> Dict[str, Any]:
    """Classify one file for planning and critic selection."""
    rel = str(file_path.relative_to(root)).replace("\\", "/")
    ext = file_path.suffix.lower()
    name = file_path.name
    lowered = rel.lower()
    return {
        "path": rel,
        "extension": ext,
        "language": LANG_BY_EXT.get(ext),
        "is_source": ext in LANG_BY_EXT,
        "is_doc": ext in DOC_EXTS or name.upper() == "AGENTS.MD" or name.upper().startswith("README"),
        "is_data": ext in DATA_EXTS,
        "is_test": any(hint in lowered for hint in TEST_HINTS),
        "is_build_file": name in BUILD_FILES,
    }


def collect_classified_files(root: Path, max_files: int) -> List[Dict[str, Any]]:
    """Return classified file metadata."""
    return [classify_file(path, root) for path in iter_files(root, max_files=max_files)]


def count_languages(classified: Iterable[Mapping[str, Any]]) -> Counter[str]:
    """Count detected source languages."""
    counts: Counter[str] = Counter()
    for item in classified:
        if item.get("language"):
            counts[str(item["language"])] += 1
    return counts


def group_paths(classified: Iterable[Mapping[str, Any]]) -> Dict[str, List[str]]:
    """Group paths into source/doc/data/test/build categories."""
    grouped: Dict[str, List[str]] = defaultdict(list)
    for item in classified:
        path = str(item["path"])
        if item.get("is_source"):
            grouped["source_files"].append(path)
        if item.get("is_doc"):
            grouped["docs"].append(path)
        if item.get("is_data"):
            grouped["data_files"].append(path)
        if item.get("is_test"):
            grouped["tests"].append(path)
        if item.get("is_build_file"):
            grouped["build_files"].append(path)
    return grouped


def read_text_snippet(path: Path, max_chars: int = 2000) -> str:
    """Read a small UTF-8 snippet, returning empty string for binary/failed reads."""
    try:
        return path.read_text(encoding="utf-8")[:max_chars]
    except (UnicodeDecodeError, OSError):
        return ""


def tokenize_for_index(text: str, *, max_terms: int = 24) -> List[str]:
    """Return stable high-signal terms for a semantic locator index."""

    counts: Counter[str] = Counter()
    for match in re.finditer(r"[A-Za-z_][A-Za-z0-9_]{2,}|[가-힣]{2,}", text):
        term = match.group(0).lower()
        if term in STOPWORDS or term.isdigit():
            continue
        counts[term] += 1
    return [term for term, _ in counts.most_common(max_terms)]


def extract_symbols(text: str, path: str) -> List[Dict[str, Any]]:
    """Extract shallow function/class/interface symbols from one text file."""

    ext = Path(path).suffix.lower()
    patterns: List[tuple[str, str]] = []
    if ext == ".py":
        patterns = [(r"^\s*def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", "function"), (r"^\s*class\s+([A-Za-z_][A-Za-z0-9_]*)\b", "class")]
    elif ext in {".js", ".jsx", ".ts", ".tsx"}:
        patterns = [
            (r"\bfunction\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*\(", "function"),
            (r"\bclass\s+([A-Za-z_$][A-Za-z0-9_$]*)\b", "class"),
            (r"\b(?:const|let|var)\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*=\s*(?:async\s*)?\(", "function"),
            (r"\binterface\s+([A-Za-z_$][A-Za-z0-9_$]*)\b", "interface"),
        ]
    elif ext == ".go":
        patterns = [(r"^\s*func\s+(?:\([^)]+\)\s*)?([A-Za-z_][A-Za-z0-9_]*)\s*\(", "function"), (r"^\s*type\s+([A-Za-z_][A-Za-z0-9_]*)\s+struct\b", "struct")]
    elif ext == ".rs":
        patterns = [(r"^\s*(?:pub\s+)?fn\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", "function"), (r"^\s*(?:pub\s+)?struct\s+([A-Za-z_][A-Za-z0-9_]*)\b", "struct")]
    elif ext in {".java", ".kt", ".swift", ".cs", ".cpp", ".cc", ".cxx", ".c", ".h", ".hpp"}:
        patterns = [(r"\bclass\s+([A-Za-z_][A-Za-z0-9_]*)\b", "class"), (r"\b(?:func|fun)\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", "function")]

    symbols: List[Dict[str, Any]] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        for pattern, kind in patterns:
            for match in re.finditer(pattern, line):
                symbols.append({"name": match.group(1), "kind": kind, "path": path, "line": line_number})
                if len(symbols) >= 40:
                    return symbols
    return symbols


def split_identifier_terms(value: str) -> str:
    """Expand snake/camel/path identifiers into searchable terms."""

    spaced = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", value)
    spaced = re.sub(r"[^A-Za-z0-9가-힣]+", " ", spaced)
    return spaced.lower()


def build_search_text(path: str, text: str, symbols: Iterable[Mapping[str, Any]], terms: Iterable[str], *, max_chars: int = 6000) -> str:
    """Build bounded text used by semantic ranking backends."""

    symbol_text = " ".join(str(symbol.get("name", "")) for symbol in symbols)
    weighted = " ".join([
        split_identifier_terms(path),
        split_identifier_terms(path),
        split_identifier_terms(symbol_text),
        split_identifier_terms(symbol_text),
        " ".join(terms),
        text[:max_chars],
    ])
    return " ".join(weighted.split())[:max_chars]


def sklearn_available() -> bool:
    """Return True when scikit-learn semantic ranking can be used."""

    try:
        import sklearn  # noqa: F401
    except ImportError:
        return False
    return True


def sentence_transformers_available() -> bool:
    """Return True when dense embedding ranking can be used."""

    try:
        import sentence_transformers  # noqa: F401
    except ImportError:
        return False
    return True


def encode_embedding_texts(texts: List[str], *, model_name: str = DEFAULT_EMBEDDING_MODEL) -> Dict[str, Any]:
    """Encode texts with SentenceTransformers, returning JSON-serializable vectors."""

    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(model_name)
    vectors = model.encode(texts, normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=False)
    return {
        "model": model_name,
        "dimension": int(vectors.shape[1]) if getattr(vectors, "ndim", 0) == 2 else 0,
        "vectors": [[round(float(value), 6) for value in row] for row in vectors],
    }


def dot_score(left: Iterable[float], right: Iterable[float]) -> float:
    """Return cosine score for normalized vectors, or dot-product fallback."""

    return sum(float(a) * float(b) for a, b in zip(left, right))


def collect_doc_snippets(root: Path, docs: Iterable[str], max_docs: int = 20, max_chars: int = 2000) -> Dict[str, str]:
    """Collect snippets from key Markdown/spec files."""
    snippets: Dict[str, str] = {}
    if max_docs <= 0 or max_chars <= 0:
        return snippets
    ordered = prioritize_paths(list(docs))
    for rel in ordered[:max_docs]:
        snippets[rel] = read_text_snippet(root / rel, max_chars=max_chars)
    return snippets


def prioritize_paths(paths: Iterable[str]) -> List[str]:
    """Return paths ordered for compact Codex context consumption."""

    def score(path: str) -> tuple[int, int, str]:
        name = Path(path).name.upper()
        parts = Path(path).parts
        priority = 0
        if name in PRIORITY_DOC_NAMES:
            priority -= 100
        if any(marker in path.lower() for marker in SECURITY_MARKERS):
            priority -= 30
        if "references" in parts or "docs" in parts:
            priority -= 20
        if "tests" in parts:
            priority -= 10
        return (priority, len(parts), path.lower())

    return sorted(paths, key=score)


def unique_ordered(paths: Iterable[str]) -> List[str]:
    """Return unique paths while preserving the incoming order."""

    seen: set[str] = set()
    unique: List[str] = []
    for path in paths:
        if path in seen:
            continue
        seen.add(path)
        unique.append(path)
    return unique


def inventory_limits(mode: str, max_files: int | None = None) -> Dict[str, int]:
    """Return scan/list/snippet limits for an inventory mode."""

    if mode not in INVENTORY_MODES:
        raise ValueError(f"Unknown inventory mode: {mode}. Expected one of {sorted(INVENTORY_MODES)}")
    limits = dict(INVENTORY_MODES[mode])
    if max_files is not None:
        limits["max_files"] = max_files
    return limits


def role_profile_for_path(path: str) -> Dict[str, Any] | None:
    """Return the first role profile matching a path or known task term."""

    lowered = path.lower()
    for profile in ROLE_PROFILES:
        if any(str(pattern).lower() in lowered for pattern in profile["patterns"]):
            return profile
    return None


def build_role_map(inventory: Mapping[str, Any], *, max_paths_per_role: int = 6) -> List[Dict[str, Any]]:
    """Build a compact file responsibility map for future targeted exploration."""

    candidates = unique_ordered(prioritize_paths([
        *list(inventory.get("source_files_sample", [])),
        *list(inventory.get("tests", [])),
        *list(inventory.get("docs", [])),
        *list(inventory.get("build_files", [])),
    ]))
    roles: Dict[str, Dict[str, Any]] = {}
    for path in candidates:
        profile = role_profile_for_path(path)
        if profile is None:
            continue
        role = str(profile["role"])
        item = roles.setdefault(
            role,
            {
                "role": role,
                "purpose": profile["purpose"],
                "paths": [],
                "queries": list(profile["queries"])[:2],
            },
        )
        if len(item["paths"]) < max_paths_per_role:
            item["paths"].append(path)
    return [roles[profile["role"]] for profile in ROLE_PROFILES if profile["role"] in roles]


def format_role_map(role_map: Iterable[Mapping[str, Any]], *, max_roles: int = 8, max_paths: int = 4) -> List[str]:
    """Return compact Markdown lines for a role map."""

    lines: List[str] = []
    for item in list(role_map)[:max_roles]:
        paths = ", ".join(f"`{path}`" for path in list(item.get("paths", []))[:max_paths])
        queries = "; ".join(str(query) for query in list(item.get("queries", []))[:2])
        lines.append(f"- **{item.get('role')}**: {item.get('purpose')} Paths: {paths or 'none'}. Query hints: `{queries}`")
    return lines or ["- none detected"]


def build_file_fingerprint(root: Path, max_files: int = 5000) -> Dict[str, Any]:
    """Build a cheap project fingerprint without reading file contents."""

    digest = hashlib.sha256()
    newest_mtime = 0.0
    newest_path = ""
    file_count = 0
    for file_path in iter_files(root, max_files=max_files):
        try:
            rel = str(file_path.relative_to(root)).replace("\\", "/")
            stat = file_path.stat()
        except OSError:
            continue
        file_count += 1
        digest.update(rel.encode("utf-8", errors="replace"))
        digest.update(str(stat.st_size).encode("ascii"))
        digest.update(str(stat.st_mtime_ns).encode("ascii"))
        if stat.st_mtime > newest_mtime:
            newest_mtime = stat.st_mtime
            newest_path = rel
    return {
        "algorithm": "sha256:path-size-mtime",
        "digest": digest.hexdigest(),
        "file_count": file_count,
        "newest_mtime": newest_mtime,
        "newest_path": newest_path,
        "max_files": max_files,
    }


def build_semantic_index(
    root: Path,
    inventory: Mapping[str, Any],
    *,
    max_files: int = 400,
    max_chars_per_file: int = 12000,
    max_terms_per_file: int = 16,
    max_paths_per_term: int = 12,
    enable_embeddings: bool = False,
    embedding_model: str = DEFAULT_EMBEDDING_MODEL,
) -> Dict[str, Any]:
    """Build a bounded lexical/symbol index for quick file location."""

    candidate_paths = unique_ordered(prioritize_paths([
        *list(inventory.get("source_files_sample", [])),
        *list(inventory.get("tests", [])),
        *list(inventory.get("docs", [])),
        *list(inventory.get("build_files", [])),
    ]))
    files: List[Dict[str, Any]] = []
    symbols: List[Dict[str, Any]] = []
    inverted: Dict[str, List[str]] = defaultdict(list)
    for rel in candidate_paths[:max_files]:
        if Path(rel).suffix.lower() not in INDEX_TEXT_EXTS:
            continue
        text = read_text_snippet(root / rel, max_chars=max_chars_per_file)
        if not text:
            continue
        file_symbols = extract_symbols(text, rel)
        terms = tokenize_for_index(text, max_terms=max_terms_per_file)
        search_text = build_search_text(rel, text, file_symbols, terms)
        for term in terms:
            paths = inverted[term]
            if rel not in paths and len(paths) < max_paths_per_term:
                paths.append(rel)
        symbols.extend(file_symbols)
        files.append({"path": rel, "terms": terms, "symbols": file_symbols[:20], "search_text": search_text})
    top_terms = sorted(inverted, key=lambda term: (-len(inverted[term]), term))[:80]
    ranking_backend = "sklearn-tfidf" if sklearn_available() else "lexical-overlap"
    embedding_info: Dict[str, Any] = {
        "enabled": bool(enable_embeddings),
        "available": sentence_transformers_available() if enable_embeddings else False,
        "model": embedding_model,
        "dimension": 0,
        "vectors": [],
        "error": None,
    }
    if enable_embeddings and files and sentence_transformers_available():
        try:
            encoded = encode_embedding_texts([str(item.get("search_text", "")) for item in files], model_name=embedding_model)
            embedding_info.update(encoded)
            embedding_info["available"] = True
            ranking_backend = "embedding-cosine"
        except Exception as exc:
            embedding_info["error"] = f"{type(exc).__name__}: {exc}"
    return {
        "schema_version": 1,
        "created_at": now_iso(),
        "strategy": "bounded-embedding-symbol-index" if ranking_backend == "embedding-cosine" else "bounded-tfidf-symbol-index" if ranking_backend == "sklearn-tfidf" else "bounded-lexical-symbol-index",
        "ranking_backend": ranking_backend,
        "embedding": embedding_info,
        "file_count": len(files),
        "symbol_count": len(symbols),
        "files": files,
        "symbols": symbols[:1000],
        "terms": {term: inverted[term] for term in top_terms},
    }


def summarize_semantic_index(index: Mapping[str, Any]) -> Dict[str, Any]:
    """Return compact semantic index metadata for context packs and cache."""

    terms = index.get("terms", {})
    top_terms = list(terms.keys())[:20] if isinstance(terms, Mapping) else []
    embedding = index.get("embedding", {}) if isinstance(index.get("embedding"), Mapping) else {}
    return {
        "strategy": index.get("strategy"),
        "ranking_backend": index.get("ranking_backend", "lexical-overlap"),
        "embedding_model": embedding.get("model"),
        "embedding_dimension": embedding.get("dimension", 0),
        "embedding_available": embedding.get("available", False),
        "embedding_error": embedding.get("error"),
        "file_count": index.get("file_count", 0),
        "symbol_count": index.get("symbol_count", 0),
        "top_terms": top_terms,
    }


def _lexical_score(query_terms: List[str], file_item: Mapping[str, Any]) -> float:
    terms = {str(term).lower() for term in file_item.get("terms", [])}
    path_terms = set(split_identifier_terms(str(file_item.get("path", ""))).split())
    symbol_terms = set()
    for symbol in file_item.get("symbols", []):
        if isinstance(symbol, Mapping):
            symbol_terms.update(split_identifier_terms(str(symbol.get("name", ""))).split())
    haystack = terms | path_terms | symbol_terms
    if not query_terms:
        return 0.0
    return sum(2.0 if term in symbol_terms else 1.5 if term in path_terms else 1.0 for term in query_terms if term in haystack) / len(query_terms)


def search_semantic_index(query: str, index: Mapping[str, Any], *, top_k: int = 8, force_fallback: bool = False, force_tfidf: bool = False, force_lexical: bool = False, embedding_model: str | None = None) -> Dict[str, Any]:
    """Rank semantic index files for a query using embeddings or TF-IDF when available."""

    files = [item for item in index.get("files", []) if isinstance(item, Mapping)]
    query_terms = tokenize_for_index(query, max_terms=32)
    backend = "lexical-overlap"
    scores: List[float] = []
    embedding = index.get("embedding", {}) if isinstance(index.get("embedding"), Mapping) else {}
    vectors = embedding.get("vectors", []) if isinstance(embedding.get("vectors", []), list) else []
    if files and vectors and not force_fallback and not force_tfidf and not force_lexical and sentence_transformers_available():
        try:
            encoded = encode_embedding_texts([query], model_name=embedding_model or str(embedding.get("model") or DEFAULT_EMBEDDING_MODEL))
            query_vector = encoded["vectors"][0]
            scores = [dot_score(query_vector, vector) for vector in vectors[:len(files)]]
            backend = "embedding-cosine"
        except Exception:
            scores = []
            backend = "lexical-overlap"
    if files and not scores and not force_fallback and not force_lexical and sklearn_available():
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity

            corpus = [str(item.get("search_text") or " ".join(item.get("terms", [])) or item.get("path", "")) for item in files]
            vectorizer = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, min_df=1)
            matrix = vectorizer.fit_transform([*corpus, query])
            query_vector = matrix[-1]
            doc_matrix = matrix[:-1]
            scores = [float(value) for value in cosine_similarity(query_vector, doc_matrix).ravel()]
            backend = "sklearn-tfidf"
        except Exception:
            scores = []
            backend = "lexical-overlap"
    if not scores:
        scores = [_lexical_score(query_terms, item) for item in files]
        backend = "lexical-overlap"
    ranked = sorted(zip(files, scores), key=lambda pair: (-pair[1], str(pair[0].get("path", ""))))[:top_k]
    return {
        "query": query,
        "ranking_backend": backend,
        "top_k": top_k,
        "results": [
            {
                "path": item.get("path"),
                "score": round(score, 6),
                "terms": list(item.get("terms", []))[:12],
                "symbols": list(item.get("symbols", []))[:10],
            }
            for item, score in ranked
            if score > 0
        ],
    }


def infer_frameworks(root: Path, grouped: Mapping[str, List[str]]) -> List[str]:
    """Infer likely frameworks from manifests and build files.

    Manifest parsing is intentionally shallow and bounded. It checks exact
    manifest files wherever they appear in the scanned tree.
    """
    frameworks: List[str] = []
    build_files = list(grouped.get("build_files", []))
    for rel in build_files:
        name = Path(rel).name
        if name == "package.json":
            package_text = read_text_snippet(root / rel, max_chars=12000).lower()
            for marker, framework in [("next", "nextjs"), ("react", "react"), ("vite", "vite"), ("vue", "vue"), ("svelte", "svelte"), ("express", "express")]:
                if marker in package_text:
                    frameworks.append(framework)
        elif name == "pyproject.toml":
            pyproject = read_text_snippet(root / rel, max_chars=12000).lower()
            for marker, framework in [("fastapi", "fastapi"), ("django", "django"), ("flask", "flask"), ("pandas", "pandas"), ("pytest", "pytest")]:
                if marker in pyproject:
                    frameworks.append(framework)
        elif name == "requirements.txt":
            requirements = read_text_snippet(root / rel, max_chars=12000).lower()
            for marker, framework in [("fastapi", "fastapi"), ("django", "django"), ("flask", "flask"), ("pandas", "pandas"), ("pytest", "pytest")]:
                if marker in requirements:
                    frameworks.append(framework)
    build_names = {Path(rel).name for rel in build_files}
    if "go.mod" in build_names:
        frameworks.append("go-module")
    if "Cargo.toml" in build_names:
        frameworks.append("rust-cargo")
    return sorted(set(frameworks))


def detect_security_surface(grouped: Mapping[str, List[str]]) -> bool:
    """Return True when filenames imply security/privacy-sensitive work."""

    candidates: List[str] = []
    for key in ("source_files", "data_files", "build_files"):
        candidates.extend(grouped.get(key, []))
    return any(any(marker in rel.lower() for marker in SECURITY_MARKERS) for rel in candidates)


def choose_recommended_critics(inventory: Mapping[str, Any]) -> List[str]:
    """Choose critic roles from inventory signals instead of exhaustive defaults."""
    critics = [
        "requirements-critic",
        "test-tdd-critic",
        "existing-code-reuse-refactor-critic" if inventory.get("has_existing_code") else "greenfield-scope-critic",
    ]
    if inventory.get("requires_data_critic"):
        critics.append("data-csv-critic")
    if inventory.get("needs_security_critic"):
        critics.append("security-risk-critic")
    if inventory.get("frameworks"):
        critics.append("source-driven-framework-critic")
    if inventory.get("has_existing_code"):
        critics.append("architecture-critic")
    return list(dict.fromkeys(critics))


def build_inventory(
    root: Path,
    max_files: int | None = None,
    include_snippets: bool = False,
    mode: str = "standard",
) -> Dict[str, Any]:
    """Build a bounded project context inventory.

    Standard mode intentionally omits snippets and caps ranked lists. Use
    mode="deep" or --include-snippets when a broader prompt context is worth
    the token cost.
    """

    limits = inventory_limits(mode, max_files=max_files)
    classified = collect_classified_files(root, max_files=limits["max_files"])
    language_counts = count_languages(classified)
    grouped = group_paths(classified)
    docs = prioritize_paths(grouped.get("docs", []))
    data_files = prioritize_paths(grouped.get("data_files", []))
    tests = prioritize_paths(grouped.get("tests", []))
    build_files = prioritize_paths(grouped.get("build_files", []))
    source_files = prioritize_paths(grouped.get("source_files", []))
    data: Dict[str, Any] = {
        "schema_version": 1,
        "created_at": now_iso(),
        "root": str(root),
        "cache_strategy": "bounded-file-metadata-fingerprint-plus-compact-context-pack",
        "inventory_mode": mode,
        "limits": limits,
        "scanned_file_count": len(classified),
        "scan_truncated": len(classified) >= limits["max_files"],
        "fingerprint": build_file_fingerprint(root, max_files=limits["max_files"]),
        "language_counts": dict(language_counts),
        "primary_languages": [lang for lang, _ in language_counts.most_common(5)],
        "frameworks": infer_frameworks(root, grouped),
        "docs": docs[: limits["docs"]],
        "data_files": data_files[: limits["data_files"]],
        "tests": tests[: limits["tests"]],
        "build_files": build_files[: limits["build_files"]],
        "source_files_sample": source_files[: limits["source_files_sample"]],
        "total_docs": len(docs),
        "total_data_files": len(data_files),
        "total_tests": len(tests),
        "total_build_files": len(build_files),
        "total_source_files": len(source_files),
        "requires_data_critic": bool(data_files),
        "has_existing_code": bool(source_files),
        "has_tests": bool(tests),
        "needs_security_critic": detect_security_surface(grouped),
    }
    if include_snippets:
        data["doc_snippets"] = collect_doc_snippets(
            root,
            data["docs"],
            max_docs=limits["doc_snippet_count"],
            max_chars=limits["doc_snippet_chars"],
        )
    data["recommended_critics"] = choose_recommended_critics(data)
    data["role_map"] = build_role_map(data)
    return data


def _markdown_list(values: Iterable[str], limit: int) -> List[str]:
    items = list(values)[:limit]
    return [f"- `{item}`" for item in items] or ["- none detected"]


def build_context_pack(data: Mapping[str, Any], *, max_chars: int = 12000) -> str:
    """Build a compact Markdown pack optimized for quick Codex reference."""

    fingerprint = data.get("fingerprint") if isinstance(data.get("fingerprint"), Mapping) else {}
    sections: List[str] = [
        "# review-driven-development context pack",
        "",
        "Use this file as the first fast reference before opening larger source files.",
        "",
        "## Snapshot",
        f"- Created: `{data.get('created_at')}`",
        f"- Root: `{data.get('root')}`",
        f"- Files scanned: `{data.get('scanned_file_count')}`",
        f"- Inventory mode: `{data.get('inventory_mode', 'standard')}`",
        f"- Fingerprint: `{fingerprint.get('digest', '')}`",
        f"- Newest file: `{fingerprint.get('newest_path', '')}`",
        "",
        "## Project shape",
        f"- Primary languages: `{', '.join(data.get('primary_languages', [])) or 'none detected'}`",
        f"- Frameworks: `{', '.join(data.get('frameworks', [])) or 'none detected'}`",
        f"- Existing code: `{data.get('has_existing_code')}`",
        f"- Tests detected: `{data.get('has_tests')}`",
        f"- Data critic required: `{data.get('requires_data_critic')}`",
        f"- Security critic signal: `{data.get('needs_security_critic')}`",
        f"- Recommended critics: `{', '.join(data.get('recommended_critics', []))}`",
    ]
    semantic = data.get("semantic_index_summary")
    if isinstance(semantic, Mapping):
        sections.extend([
            f"- Semantic index files: `{semantic.get('file_count', 0)}`",
            f"- Semantic index symbols: `{semantic.get('symbol_count', 0)}`",
            f"- Top semantic terms: `{', '.join(list(semantic.get('top_terms', []))[:12])}`",
        ])
    sections.extend([
        "",
        "## Role map",
        "Use this map before opening source trees; jump to the matching role path or run one query hint with `--semantic-search`.",
        *format_role_map(data.get("role_map", [])),
        "",
        "## Build files",
        *_markdown_list(data.get("build_files", []), 25),
        "",
        "## Priority docs",
        *_markdown_list(data.get("docs", []), 40),
        "",
        "## Tests",
        *_markdown_list(data.get("tests", []), 40),
        "",
        "## Source sample",
        *_markdown_list(data.get("source_files_sample", []), 80),
    ])
    snippets = data.get("doc_snippets", {})
    if isinstance(snippets, Mapping) and snippets:
        sections.extend(["", "## Doc snippets"])
        for path, snippet in list(snippets.items())[:8]:
            compact = " ".join(str(snippet).split())
            if len(compact) > 700:
                compact = compact[:700].rstrip() + "..."
            sections.extend(["", f"### `{path}`", compact or "(empty)"])
    text = "\n".join(sections).rstrip() + "\n"
    if len(text) <= max_chars:
        return text
    return text[: max(0, max_chars - 80)].rstrip() + "\n\n[truncated: increase --max-pack-chars for more]\n"


def summarize_inventory(data: Mapping[str, Any]) -> str:
    """Return a human-readable summary for prompts and briefs."""
    return "\n".join([
        f"Root: {data.get('root')}",
        f"Inventory mode: {data.get('inventory_mode', 'standard')}",
        f"Scanned files: {data.get('scanned_file_count')}{' (truncated)' if data.get('scan_truncated') else ''}",
        f"Primary languages: {', '.join(data.get('primary_languages', [])) or 'none detected'}",
        f"Frameworks: {', '.join(data.get('frameworks', [])) or 'none detected'}",
        f"Existing code: {data.get('has_existing_code')}",
        f"Tests detected: {data.get('has_tests')}",
        f"Data critic required: {data.get('requires_data_critic')}",
        f"Security critic signal: {data.get('needs_security_critic')}",
        f"Docs: {len(data.get('docs', []))} of {data.get('total_docs', len(data.get('docs', [])))}",
        f"Source sample: {len(data.get('source_files_sample', []))} of {data.get('total_source_files', len(data.get('source_files_sample', [])))}",
        f"Build files: {', '.join(data.get('build_files', [])[:10])}",
    ])


def save_inventory(root: Path, data: Mapping[str, Any]) -> Path:
    """Save context inventory under project state."""
    directory = root / STATE_DIR
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / CONTEXT_INVENTORY_FILE
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def save_context_pack(root: Path, data: Mapping[str, Any], *, max_chars: int = 12000) -> Path:
    """Save a compact Markdown context pack for fast Codex loading."""

    directory = root / STATE_DIR
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / CONTEXT_PACK_FILE
    path.write_text(build_context_pack(data, max_chars=max_chars), encoding="utf-8")
    return path


def save_context_cache(root: Path, data: Mapping[str, Any], *, inventory_path: Path, pack_path: Path | None = None) -> Path:
    """Save cache metadata used to reuse inventory and context packs safely."""

    directory = root / STATE_DIR
    directory.mkdir(parents=True, exist_ok=True)
    cache = {
        "schema_version": 1,
        "created_at": now_iso(),
        "strategy": data.get("cache_strategy"),
        "fingerprint": data.get("fingerprint", {}),
        "inventory_path": str(inventory_path),
        "context_pack_path": str(pack_path) if pack_path else None,
        "semantic_index_path": str(root / STATE_DIR / CONTEXT_SEMANTIC_INDEX_FILE),
        "semantic_index_summary": data.get("semantic_index_summary", {}),
        "scanned_file_count": data.get("scanned_file_count"),
        "primary_languages": data.get("primary_languages", []),
        "frameworks": data.get("frameworks", []),
    }
    path = directory / CONTEXT_CACHE_FILE
    path.write_text(json.dumps(cache, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def save_semantic_index(root: Path, index: Mapping[str, Any]) -> Path:
    """Save the semantic locator index under project state."""

    directory = root / STATE_DIR
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / CONTEXT_SEMANTIC_INDEX_FILE
    path.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def load_inventory(root: Path) -> Dict[str, Any] | None:
    """Load saved context inventory if it exists.

    Returns None when the saved schema is incompatible or when a scanned
    project file is newer than the inventory file.
    """
    path = root / STATE_DIR / CONTEXT_INVENTORY_FILE
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if data.get("schema_version") != 1:
        return None
    inventory_mtime = path.stat().st_mtime
    max_files = int(data.get("scanned_file_count") or 5000)
    for file_path in iter_files(root, max_files=max(max_files, 1)):
        try:
            if file_path.stat().st_mtime > inventory_mtime:
                return None
        except OSError:
            return None
    return data


def load_context_pack(root: Path) -> str | None:
    """Load the compact context pack if present."""

    path = root / STATE_DIR / CONTEXT_PACK_FILE
    if not path.exists():
        return None
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def load_context_cache(root: Path) -> Dict[str, Any] | None:
    """Load context cache metadata if present and parseable."""

    path = root / STATE_DIR / CONTEXT_CACHE_FILE
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    if data.get("schema_version") != 1:
        return None
    return data


def load_semantic_index(root: Path) -> Dict[str, Any] | None:
    """Load the semantic locator index if present and parseable."""

    path = root / STATE_DIR / CONTEXT_SEMANTIC_INDEX_FILE
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    if data.get("schema_version") != 1:
        return None
    return data


def detect_context_script(root: Path) -> str:
    """Return the best repo-local context inventory command path."""

    candidates = [
        "skills/review-driven-development/scripts/context_inventory.py",
        ".agents/skills/review-driven-development/scripts/context_inventory.py",
        ".codex/skills/review-driven-development/scripts/context_inventory.py",
    ]
    for candidate in candidates:
        if (root / candidate).exists():
            return candidate
    return candidates[0]


def build_bootstrap_block(root: Path, *, context_script: str | None = None) -> str:
    """Build an AGENTS.md block that injects fast context instructions."""

    script = context_script or detect_context_script(root)
    return "\n".join([
        BOOTSTRAP_BEGIN,
        "## review-driven-development fast context",
        "",
        "Before planning or editing in this repository:",
        f"- Run `python {script} --root . --sync --summary` when `.codex/review-driven-development/context-pack.md` is missing or stale.",
        "- Read `.codex/review-driven-development/context-pack.md` before opening broad source trees.",
        f"- Run `python {script} --root . --sync --semantic-search \"<query>\"` to rank likely files before broad search.",
        "- Use `.codex/review-driven-development/context-semantic-index.json` for file, symbol, term, and optional dense-vector lookup.",
        "- Use the `Role map` section in `context-pack.md` before opening source trees; it lists responsibility boundaries and query hints.",
        "- Default ranking uses scikit-learn TF-IDF when installed, then lexical overlap; dense sentence-transformers ranking is opt-in with `--embeddings`.",
        "- Open the full source files referenced by the active TODO before editing; the semantic index is a locator, not proof.",
        "- Keep validation evidence, independent review, and documentation status in the TODO ledger before completion.",
        BOOTSTRAP_END,
        "",
    ])


def write_bootstrap(root: Path, *, target: str = "AGENTS.md") -> Path:
    """Insert or replace the RDD fast-context bootstrap block in a repo file."""

    path = root / target
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    block = build_bootstrap_block(root)
    pattern = re.compile(re.escape(BOOTSTRAP_BEGIN) + r".*?" + re.escape(BOOTSTRAP_END) + r"\n?", re.DOTALL)
    if pattern.search(existing):
        updated = pattern.sub(block, existing)
    else:
        prefix = existing.rstrip() + "\n\n" if existing.strip() else ""
        updated = prefix + block
    if updated != existing:
        path.write_text(updated, encoding="utf-8")
    return path


def sync_context(
    root: Path,
    *,
    max_files: int | None = None,
    include_snippets: bool = False,
    mode: str = "standard",
    force: bool = False,
    write_pack: bool = True,
    write_semantic_index: bool = True,
    enable_embeddings: bool = False,
    embedding_model: str = DEFAULT_EMBEDDING_MODEL,
    max_pack_chars: int = 12000,
) -> Dict[str, Any]:
    """Reuse valid context cache or rebuild inventory and compact context pack."""

    cached = None if force else load_inventory(root)
    if cached is not None:
        cached = dict(cached)
        semantic_path = root / STATE_DIR / CONTEXT_SEMANTIC_INDEX_FILE
        semantic_index = load_semantic_index(root) if write_semantic_index else None
        needs_embedding_refresh = False
        if isinstance(semantic_index, Mapping):
            embedding = semantic_index.get("embedding", {}) if isinstance(semantic_index.get("embedding"), Mapping) else {}
            needs_embedding_refresh = bool(
                (
                    enable_embeddings
                    and sentence_transformers_available()
                    and (not embedding.get("vectors") or embedding.get("model") != embedding_model)
                )
                or (not enable_embeddings and bool(embedding.get("vectors")))
            )
        if write_semantic_index and (semantic_index is None or needs_embedding_refresh):
            semantic_index = build_semantic_index(root, cached, enable_embeddings=enable_embeddings, embedding_model=embedding_model)
            semantic_path = save_semantic_index(root, semantic_index)
        if semantic_index is not None:
            cached["semantic_index_summary"] = summarize_semantic_index(semantic_index)
            save_inventory(root, cached)
        pack_path = root / STATE_DIR / CONTEXT_PACK_FILE
        if write_pack:
            pack_path = save_context_pack(root, cached, max_chars=max_pack_chars)
        save_context_cache(root, cached, inventory_path=root / STATE_DIR / CONTEXT_INVENTORY_FILE, pack_path=pack_path if write_pack else None)
        return {
            "cache_hit": True,
            "context_inventory": cached,
            "inventory_path": str(root / STATE_DIR / CONTEXT_INVENTORY_FILE),
            "context_pack_path": str(pack_path) if write_pack else None,
            "cache_path": str(root / STATE_DIR / CONTEXT_CACHE_FILE),
            "semantic_index_path": str(semantic_path) if write_semantic_index else None,
        }

    data = build_inventory(root, max_files=max_files, include_snippets=include_snippets, mode=mode)
    semantic_path = None
    if write_semantic_index:
        semantic_index = build_semantic_index(root, data, enable_embeddings=enable_embeddings, embedding_model=embedding_model)
        data["semantic_index_summary"] = summarize_semantic_index(semantic_index)
        semantic_path = save_semantic_index(root, semantic_index)
    inventory_path = save_inventory(root, data)
    pack_path = save_context_pack(root, data, max_chars=max_pack_chars) if write_pack else None
    cache_path = save_context_cache(root, data, inventory_path=inventory_path, pack_path=pack_path)
    return {
        "cache_hit": False,
        "context_inventory": data,
        "inventory_path": str(inventory_path),
        "context_pack_path": str(pack_path) if pack_path else None,
        "cache_path": str(cache_path),
        "semantic_index_path": str(semantic_path) if semantic_path else None,
    }


def main() -> None:
    """CLI entrypoint for context inventory generation."""

    parser = argparse.ArgumentParser(description="Build project context inventory for review-driven-development.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--max-files", type=int)
    parser.add_argument("--inventory-mode", choices=sorted(INVENTORY_MODES), default="standard")
    parser.add_argument("--include-snippets", action="store_true")
    parser.add_argument("--no-snippets", action="store_true")
    parser.add_argument("--summary", action="store_true")
    parser.add_argument("--save", action="store_true")
    parser.add_argument("--sync", action="store_true", help="Reuse valid cache or rebuild inventory/cache/pack")
    parser.add_argument("--force", action="store_true", help="Force rebuild when used with --sync")
    parser.add_argument("--pack", action="store_true", help="Save a compact context-pack.md with the inventory")
    parser.add_argument("--overview", action="store_true", help="Print the compact context pack when available")
    parser.add_argument("--no-semantic-index", action="store_true", help="Skip semantic locator index generation")
    parser.add_argument("--semantic-index", action="store_true", help="Print the semantic locator index")
    parser.add_argument("--semantic-summary", action="store_true", help="Print compact semantic locator index metadata")
    parser.add_argument("--semantic-search", help="Rank likely files for this query using the semantic index")
    parser.add_argument("--role-map", action="store_true", help="Print compact file responsibility map")
    parser.add_argument("--top-k", type=int, default=8)
    parser.add_argument("--force-lexical", action="store_true", help="Force lexical fallback ranking for semantic search")
    parser.add_argument("--force-tfidf", action="store_true", help="Skip embedding ranking and force TF-IDF when available")
    parser.add_argument("--embeddings", action="store_true", help="Build/use dense embedding vectors; slower and optional")
    parser.add_argument("--no-embeddings", action="store_true", help="Compatibility flag; embeddings are off by default")
    parser.add_argument("--embedding-model", default=DEFAULT_EMBEDDING_MODEL)
    parser.add_argument("--bootstrap", action="store_true", help="Write repo-local AGENTS.md fast-context bootstrap block")
    parser.add_argument("--bootstrap-target", default="AGENTS.md")
    parser.add_argument("--max-pack-chars", type=int, default=12000)
    args = parser.parse_args()
    root = Path(args.root).resolve()
    include_snippets = args.include_snippets and not args.no_snippets
    enable_embeddings = args.embeddings and not args.no_embeddings
    if args.sync:
        result = sync_context(root, max_files=args.max_files, include_snippets=include_snippets, mode=args.inventory_mode, force=args.force, write_pack=True, write_semantic_index=not args.no_semantic_index, enable_embeddings=enable_embeddings, embedding_model=args.embedding_model, max_pack_chars=args.max_pack_chars)
        if args.bootstrap:
            bootstrap_path = write_bootstrap(root, target=args.bootstrap_target)
            result = sync_context(root, max_files=args.max_files, include_snippets=include_snippets, mode=args.inventory_mode, force=True, write_pack=True, write_semantic_index=not args.no_semantic_index, enable_embeddings=enable_embeddings, embedding_model=args.embedding_model, max_pack_chars=args.max_pack_chars)
            result["bootstrap_path"] = str(bootstrap_path)
        if args.semantic_index:
            print(json.dumps(load_semantic_index(root) or {}, ensure_ascii=False, indent=2))
        elif args.semantic_summary:
            print(json.dumps(summarize_semantic_index(load_semantic_index(root) or {}), ensure_ascii=False, indent=2))
        elif args.semantic_search:
            print(json.dumps(search_semantic_index(args.semantic_search, load_semantic_index(root) or {}, top_k=args.top_k, force_fallback=args.force_lexical, force_tfidf=args.force_tfidf, force_lexical=args.force_lexical, embedding_model=args.embedding_model), ensure_ascii=False, indent=2))
        elif args.role_map:
            print(json.dumps(result["context_inventory"].get("role_map", []), ensure_ascii=False, indent=2))
        elif args.overview:
            print(load_context_pack(root) or summarize_inventory(result["context_inventory"]))
        elif args.summary:
            print(summarize_inventory(result["context_inventory"]))
        else:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    if args.bootstrap:
        bootstrap_path = write_bootstrap(root, target=args.bootstrap_target)
        sync_context(root, max_files=args.max_files, include_snippets=include_snippets, mode=args.inventory_mode, force=True, write_pack=True, write_semantic_index=not args.no_semantic_index, enable_embeddings=enable_embeddings, embedding_model=args.embedding_model, max_pack_chars=args.max_pack_chars)
        print(json.dumps({"bootstrap_path": str(bootstrap_path)}, ensure_ascii=False, indent=2))
        return

    data = build_inventory(root, max_files=args.max_files, include_snippets=include_snippets, mode=args.inventory_mode)
    if args.save or args.pack:
        data = dict(data)
        inventory_path = save_inventory(root, data) if args.save else root / STATE_DIR / CONTEXT_INVENTORY_FILE
        data["saved_to"] = str(inventory_path)
        if args.pack:
            data["context_pack_path"] = str(save_context_pack(root, data, max_chars=args.max_pack_chars))
            data["cache_path"] = str(save_context_cache(root, data, inventory_path=inventory_path, pack_path=Path(data["context_pack_path"])))
    if args.overview:
        print(build_context_pack(data, max_chars=args.max_pack_chars))
    elif args.role_map:
        print(json.dumps(data.get("role_map", []), ensure_ascii=False, indent=2))
    else:
        print(summarize_inventory(data) if args.summary else json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
