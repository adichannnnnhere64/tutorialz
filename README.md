# Tutorialz

A local-first learning and practice app, written in Rust with Dioxus 0.7.10. The learner targets web and Android. A separate web studio authors public GitHub JSON content. There is no application backend or account. The bundled Java Enterprise / Jakarta EE collection is available offline and refreshes from its public GitHub catalog when online.

## Run and build

Install Rust, the `wasm32-unknown-unknown` target, and Dioxus CLI **0.7.10**. Android additionally needs the Android SDK/NDK, Java 17+, and a Rust Android target.

```sh
cargo install dioxus-cli --version 0.7.10 --locked
rustup target add wasm32-unknown-unknown
node scripts/download-java-pack.mjs
# Development (one app at a time)
dx serve --web --package tutorialz-learner
dx serve --web --package tutorialz-author
# Both production sites, service workers, samples and optional compiler pack
python3 scripts/build-web.py
python3 -m http.server 8080 --directory dist
```

Open `http://localhost:8080/` and `/author/`. To install Java practice in either app, set the pack URL to `http://localhost:8080/java-pack/`. The runtime files are deliberately excluded from Git; the download script checks committed SHA-256 hashes. Neither app downloads the pack until requested.

The Makefile wraps the common workflows:

If Dioxus reports a wasm-bindgen version mismatch, run `make setup-tools` to install the CLI version from `Cargo.lock` into the ignored `tools/bin/` directory. The Makefile and web build prefer this directory over system packages. On Nix, ensure `wasm-ld` is available (from LLVM's `lld` package), or set `CARGO_TARGET_WASM32_UNKNOWN_UNKNOWN_LINKER` to its path.

```sh
make serve                 # build and serve both apps at http://127.0.0.1:8080
make serve-existing        # serve the current dist/ without rebuilding
make author                # run only the authoring studio with Dioxus
make check                 # validate content and run required checks
make build                 # production build in dist/
```

GitHub Actions deploys the public learner to [Tutorialz on GitHub Pages](https://adichannnnnhere64.github.io/tutorialz/) after checks pass on `main`; the author studio is at `/author/`. Locally, use `SITE_BASE_PATH=tutorialz python3 scripts/build-web.py` to reproduce that build. `DX` can override the CLI path. Set `TUTORIALZ_CATALOG_URL` and `TUTORIALZ_JAVA_PACK_URL` at build time for preset URLs, or use learner Settings. HTTPS or localhost is required for browser storage, workers, and offline service workers. Dioxus's development server does not provide the production service worker.

```sh
rustup target add aarch64-linux-android x86_64-linux-android
dx build --android --package tutorialz-learner --no-default-features --features mobile --target aarch64-linux-android --release
# For an x86_64 emulator, use --target x86_64-linux-android.
python3 scripts/patch-android-ui.py release
cd target/dx/tutorialz-learner/release/android/app && ./gradlew --no-daemon assembleRelease
```

Android progress and course cache are JSON in app-private storage. Runtime binaries are stored in the WebView's IndexedDB. Progress export saves to Downloads/Tutorialz via MediaStore (Android 10+); import uses the system file chooser. Tagged `vX.Y.Z` commits publish a signed arm64 APK on [GitHub Releases](https://github.com/adichannnnnhere64/tutorialz/releases). The tag must match `apps/learner/Cargo.toml`'s version, and each release uses the same Android signing key. Play Store publication is not configured. Browser storage can be evicted or cleared, so export backups periodically.

Android includes a **Study** tab with 24 full chapters and 192 offline sections: Understand, Apply, Advanced, Production, Exam reasoning, Cheatsheet, Check yourself, and Sources. The chapters contain 95 worked examples and 144 self-checks, including advanced scenarios in every subject. Coverage includes Java foundations, OOP, Java 8/9, Spring, Hibernate, Servlets, JSP, CDI, EJB, JMS, ActiveMQ, REST, security, servers, deployment, architecture, and Java 17/21. Design patterns explicitly covers all 23 GoF patterns, with separate Factory Method, Abstract Factory, and Builder examples. Search results and chapter contents jump directly to named subtopics.

Save topics, mark them read, and resume the last section. Stable section IDs preserve reading positions when sections are inserted; v0.3.4 numeric cursors still restore their original section (for example, index 2 remains Cheatsheet). Backups retain bookmarks and reading status without changing exam scores or question banks. Lessons live in `apps/learner/study/` and are embedded only in the APK; reference links require internet. Each chapter identifies its version baseline and source-review date. This is independent learning material, not an official Accenture syllabus or a reproduction of its assessments.

The published web app—including its mobile-browser layout—does not include this reader or its lesson text. To test the Android UI locally in a browser, build an explicit debug harness with `dx build --web --package tutorialz-learner --features study-preview --base-path ''`, serve `target/dx/tutorialz-learner/debug/web/public` on port 8876, then run `node scripts/study-test.mjs`. Never enable `study-preview` in a production web build. With JDK 21 installed, `python3 -m unittest tests.study_content_test` checks chapter integrity and compiles/runs 35 complete programs with their declared Java 8/9/17/21 release targets. `python3 scripts/study-framework-test.py` compiles the framework fragments against pinned Spring 6.2.19 and Jakarta EE 10 APIs and executes two Spring-container examples; it does not claim database/broker runtime validation. `python3 scripts/study-audit.py --output target/study-audit.json` maps required concepts to chapter headings, example titles, version notes, and primary references. CI retains that review map and reader screenshots.

After committing ordinary work on `main`, `make release` increments the patch version, runs the content checks and production web build, commits the version change, creates an annotated tag, and pushes `main` and the tag. The tag triggers the signed Android GitHub release workflow. Use `make release VERSION=0.4.0` to choose an explicit newer version. The command requires a clean worktree so it cannot include unfinished files.

## Content workflow

1. Open the studio and import its previously exported ZIP or JSON draft, or edit the included samples.
2. Create courses, ordered Markdown lessons, tests, and questions. Link lessons to their tests. Use the form fields or advanced JSON; all changes save locally.
3. Install the Java pack if your content includes Java. **Validate & export ZIP** validates the collection and runs every Java reference solution against its cases.
4. Unzip into a public GitHub repository and commit/push. Point the learner at the raw `catalog.json` URL. **Sync questions now** in Settings downloads the collection. Later launches check for new or changed files automatically.

The authoring studio is already included here. Run `make author` for its development server, or run `make serve` and open `http://127.0.0.1:8080/author/`. Import the current collection ZIP or JSON, add and preview questions under **Tests**, then choose **Validate & export ZIP**. Install that export into this checkout with:

```sh
make import-author AUTHOR_EXPORT=/path/to/tutorialz-content.zip
```

The importer verifies safe paths, catalog hashes, and course IDs before replacing catalog-listed JSON. Documentation and attribution notices remain in place. Set `CONTENT_DIR=content/another-collection` to target another collection. Normal builds preserve imported questions. `make regenerate-content` explicitly replaces the bundled collection from the Python generator sources; use it only when those sources contain the changes you want to ship.

ZIP imports accept the uncompressed format produced by Tutorialz. Plain draft JSON also works. Authoring content is public, including answers and test cases; this is a personal practice tool rather than a secure examination service.

Catalogs have `schema_version: 1`, a stable `collection_id`, an optional monotonic `content_revision` (legacy catalogs default to 0), and course summaries with relative JSON paths and SHA-256 hashes. Course files contain metadata, ordered `lessons`, and `tests`. See `content/` for runnable examples. IDs use letters, digits, hyphens, and underscores and are unique across a collection. Each question belongs to one test. Changed question content receives a new revision during studio export; active sessions retain their original snapshots.

The learner starts with [the Java and enterprise question bank](content/enterprise/README.md): 650 questions: 164 easy, 344 medium, and 142 advanced, including 64 beginner Java, 66 OOP questions, the 100-question [Jakarta Competency Exam](content/enterprise/JAKARTA_COMPETENCY_EXAM.md), and the 200-question [Jakarta Dummy Exam](content/enterprise/JAKARTA_DUMMY_EXAM.md). Repeated narrative variants have been removed, and original topics remain covered. Questions are labeled AI or Scraped with source attribution; review shows your submitted answer beside the correct answer. Web and Android builds bundle the same JSON. Visitors can search cached questions and topics, then start a quiz from the results. On startup, the learner checks its selected public catalog in the background and downloads only new or changed course files after validating each file hash. It shows cached questions immediately, including when offline. Set `TUTORIALZ_CATALOG_URL` during the build to use a different public catalog. Switching collection IDs still requires confirmation in Settings.

Questions support `choice` (single or multiple select), `blanks` (one or more accepted answers per blank), and `java` (`program` or `snippet`). Choices require the exact correct set. Blanks trim outer whitespace and honor case sensitivity. Code must pass every case. All questions have equal weight. Skips are recorded but do not mark a question answered. Test completion means all current question revisions were submitted, not necessarily correctly answered.

Progress exports merge by attempt ID, combine lesson completion, reject other collections, and retain the receiving device's active session. Importing the same backup twice is safe. Switching content collections requires explicit confirmation and replaces the current library/history; export first.

## Offline Java subset

The pinned TeaVM playground pack includes a compiler and a limited Java class library. It is **not a full JVM**. Compile/run happens locally inside a dedicated worker, with no native app bridge, network, or persistent-storage API exposed to submitted code.

- Whole programs use `public class Main` and `public static void main(String[] args)`.
- Snippets fill exactly one `{{answer}}` placeholder in a `Main` template. Each case may supply harness statements, for example `System.out.print(Main.square(5));`.
- Console input is adapted to a per-case input stream. Basic `Scanner` construction, `hasNext`, `next`, `nextInt`, `nextLong`, `nextDouble`, `nextLine`, and `close` are supported by a small adapter. Advanced scanner/charset behavior is not supported. Standard input references and Scanner references outside strings/comments are adapted before compilation; packages and runtime interop are unsupported.
- Reflection, external dependencies, frameworks, native APIs and some Java SE I/O APIs are unavailable. Unsupported APIs produce diagnostics. This runner is intended for your own practice content, not adversarial code judging.
- Compile timeout: 30 seconds per case; execution timeout: 3 seconds; combined stdout/stderr limit: 64 KiB. Cancel terminates the worker. Console comparison normalizes line endings and one trailing newline, preserving other whitespace.
- Requires a modern browser/WebView with WebAssembly GC. A missing pack or worker failure is a runtime error, not an incorrect answer. No remote execution fallback is used.

See `THIRD_PARTY_NOTICES.md` for runtime provenance and licensing. The optional pack is about 6.4 MiB uncompressed; exact sizes and hashes are in `public/java-pack/manifest.json`.

## Checks

```sh
cargo test -p tutorialz-core
cargo run -p tutorialz-core -- content/catalog.json
cargo check --workspace --target wasm32-unknown-unknown
npm ci
npm test
# Question quality and Java 17 trace verification (requires JDK 17+):
npm run test:content
python3 scripts/question_bank.py
cargo run -p tutorialz-core --locked -- content/enterprise/catalog.json
# Runtime integration: serve the repository on port 8765 first
python3 -m http.server 8765
node scripts/browser-test.mjs
# App integration: serve dist on port 8766 first
python3 -m http.server 8766 --directory dist
node scripts/app-test.mjs
# With an Android emulator running
node scripts/android-browser-test.mjs
```

Set `CHROME_BIN` for your Chrome executable and `APP_URL` for another app test URL. Unit tests cover selection, grading, revisions, content integrity, and backup merging. Browser checks exercise the real compiler and learner persistence/offline flow. Production build output reports uncompressed and gzip file totals; these are artifact totals, not measured network transfers.
