# Tutorialz

A local-first learning and practice app, written in Rust with Dioxus 0.7.10. The learner targets web and Android. A separate web studio authors public GitHub JSON content. There is no application backend, account, or automatic sync.

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

For GitHub Pages use `SITE_BASE_PATH=your-repository python3 scripts/build-web.py` and publish `dist/`. User/org root sites need no base path. `DX` can override the CLI path. Set `TUTORIALZ_CATALOG_URL` and `TUTORIALZ_JAVA_PACK_URL` at build time for preset URLs, or use learner Settings. HTTPS or localhost is required for browser storage, workers, and offline service workers. Dioxus's development server does not provide the production service worker.

```sh
rustup target add aarch64-linux-android x86_64-linux-android
dx build --android --package tutorialz-learner --no-default-features --features mobile --target aarch64-linux-android --release
# For an x86_64 emulator, use --target x86_64-linux-android.
```

Android progress and course cache are JSON in app-private storage. Runtime binaries are stored in the WebView's IndexedDB. Progress export saves to Downloads/Tutorialz via MediaStore (Android 10+); import uses the system file chooser. Release signing/Play Store publication is not configured. Browser storage can be evicted or cleared, so export backups periodically.

## Content workflow

1. Open the studio and import its previously exported ZIP or JSON draft, or edit the included samples.
2. Create courses, ordered Markdown lessons, tests, and questions. Link lessons to their tests. Use the form fields or advanced JSON; all changes save locally.
3. Install the Java pack if your content includes Java. **Validate & export ZIP** validates the collection and runs every Java reference solution against its cases.
4. Unzip into a public GitHub repository and commit/push. Point the learner at the raw `catalog.json` URL. Refresh its catalog, then download courses. Use **Update downloaded courses** for new versions.

ZIP imports accept the uncompressed format produced by Tutorialz. Plain draft JSON also works. Authoring content is public, including answers and test cases; this is a personal practice tool rather than a secure examination service.

Catalogs have `schema_version: 1`, a stable `collection_id`, and course summaries with relative JSON paths and SHA-256 hashes. Course files contain metadata, ordered `lessons`, and `tests`. See `content/` for runnable examples. IDs use letters, digits, hyphens, and underscores and are unique across a collection. Each question belongs to one test. Changed question content receives a new revision during studio export; active sessions retain their original snapshots.

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
