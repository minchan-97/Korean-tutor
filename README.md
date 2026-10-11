# Korean Magnet Tutor — Molang core integrated

Streamlit tutor for one Indonesian-speaking Korean learner.

## Run
```bash
pip install -r requirements.txt
streamlit run app.py
```
Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and configure `OPENAI_API_KEY`, `OPENAI_MODEL`, `APP_PASSWORD`. For Streamlit Cloud put these values in the cloud Secrets panel, never in Git.

## Actual Molang modules reused
- `molang_core/thought_structure.py`: unmodified original `ThoughtStructure`, `JudgmentNode`, `traverse`, `learn`, transition probabilities, path audit.
- `molang_core/markov_mass.py`: unmodified original directed word Markov and mass calculation.
- `molang_core/semantic_map.py`, `word_gravity.py`, `llm_bridge.py`: preserved as original modules for subsequent integration, **not yet invoked by the UI**.
- `molang_adapter.py`: education-specific routing, persistent SQLite NM probabilities and audit, approved-only corpus.

## Critical limitations
- Original Molang's `data/molang.pkl` is NOT included, loaded, or migrated. Avoid loading unknown pickle files.
- Original `thought_structure.py` uses a real decision tree, but here its `choose_fn` is a diagnosis gate + weighted random choice; LLM does not select NM branches.
- A strategy is learned only from explicit learner feedback after the teaching action, not the score of the preceding answer. This is a subjective proxy, not verified learning gains.
- Word Markov counts sequences and does not validate grammatical or semantic relations. Seed curated graph remains separate.
- AI-generated suggested words remain unapproved until manually entered into approved corpus.
- No voice or robust Korean morphological analyzer.
- Local SQLite may be ephemeral on Streamlit Community Cloud; use durable storage for real long-term learning.
- Single shared password is not per-user authentication. Keep the link private and use platform-level access controls where possible.

## Dynamic vocabulary network extension
- `dynamic_magnet.py` now calls original Molang `semantic_map.build`, `semantic_map.clusters`, `word_gravity.masses/pull/home_branch`, `markov_mass.count/masses/next_of/blend`.
- For <=20 approved documents, original `semantic_map`'s >25%-frequency suppression makes the graph empty. An explicitly isolated small-corpus co-occurrence fallback reuses its original tokenizer and cluster/gravity calculations.
- The graph is rebuilt from *approved example sentences only*, and the learner's submitted answers remain unapproved. LLM vocabulary suggestions go into a review queue, never directly into the approved corpus. Approving a vocabulary pair does not implicitly make it a corpus sentence.
- Word gravity scores are heuristic associations, not validated linguistic relations. For production, use Korean morphological analysis and an externally checked Korean–Indonesian lexicon.
- Click 'Bangun / segarkan peta' after adding approved examples. The graph state is session-scoped; approved source sentences persist in SQLite.
