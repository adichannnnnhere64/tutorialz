# Repository Guidelines

## Project Structure & Module Organization

Tutorialz is a Rust workspace using Dioxus. `crates/core/` holds content models, validation, grading, and progress logic; `crates/ui/` holds shared interface code. `apps/learner/` builds the web and Android learner, while `apps/author/` builds the web authoring studio. Public browser assets and the Java runner live in `public/`; example catalogs and courses live in `content/`. Build and integration helpers are in `scripts/`, JavaScript tests in `tests/`, and generated web output in `dist/`.

## Build, Test, and Development Commands

Use Rust with the `wasm32-unknown-unknown` target and Dioxus CLI 0.7.10. Run one app locally with `dx serve --web --package tutorialz-learner` or substitute `tutorialz-author`. Run `node scripts/download-java-pack.mjs` to fetch the optional pinned Java runtime. `python3 scripts/build-web.py` builds both release sites into `dist/`; serve that directory over HTTP to check production service workers. Set `SITE_BASE_PATH=tutorialz` to reproduce the GitHub Pages path.

## Coding Style & Naming Conventions

Use standard Rust formatting (`cargo fmt --all`) and Rust naming: `snake_case` for functions and modules, `PascalCase` for types. Keep shared domain logic in `crates/core/` and shared presentation code in `crates/ui/`. Match existing JSON schema fields and use stable, unique content IDs containing letters, digits, hyphens, or underscores. Name course files descriptively and update catalog hashes when content changes.

## Testing Guidelines

Run `cargo test -p tutorialz-core --locked` for core unit tests, `cargo run -p tutorialz-core --locked -- content/catalog.json` for catalog validation, `cargo check --workspace --target wasm32-unknown-unknown --locked` for web compilation, and `npm ci && npm test` for Node's `node:test` suite (`tests/*.test.mjs`). After a production build, browser integration scripts in `scripts/` exercise Java execution and learner storage; see `README.md` for their HTTP server setup. Add focused tests for grading, revisions, content integrity, or persistence changes. No numeric coverage target is defined.

## Commit & Pull Request Guidelines

Recent commits use short imperative subjects, such as `Use available Android SDK packages in CI`. Keep each commit focused. In pull requests, describe the user-visible change, list the checks run, and link a relevant issue when one exists. Include screenshots for interface changes and explain any catalog or schema migration. CI checks the web workspace, builds both sites and Android, and runs browser integration before deployment from `main`.
