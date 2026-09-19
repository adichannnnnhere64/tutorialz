# Third-party runtime notices

The optional Java pack is downloaded from the TeaVM playground, pinned by SHA-256 in `public/java-pack/manifest.json`. It is not included in Git or in the initial learner bundle.

- TeaVM and teavm-javac: copyright Alexey Andreev and contributors; Apache License 2.0. Source and build instructions: https://github.com/konsoletyper/teavm-javac and https://github.com/konsoletyper/teavm. License: https://www.apache.org/licenses/LICENSE-2.0
- The compiler includes OpenJDK components under GPL version 2 with the Classpath Exception. License and exception: https://openjdk.org/legal/gplv2+ce.html . OpenJDK sources: https://github.com/openjdk/jdk . The teavm-javac Gradle build describes the OpenJDK inputs used to produce the runtime.

Retain applicable notices and provide corresponding source as required when redistributing runtime binaries. `scripts/download-java-pack.mjs` refuses changed upstream artifacts; review provenance and licensing before repinning. The repository's own Java input adapter is separate from TeaVM's standard library.

Rust and JavaScript dependency versions are recorded in Cargo.lock and package-lock.json. Dependency licenses remain those of their respective authors.
