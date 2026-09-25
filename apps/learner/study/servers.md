## Understand

Jakarta EE defines APIs and compatibility requirements; an application server supplies implementations and managed services. A profile is a defined subset. Check the exact product release and supported profile against the APIs your application needs: support for Servlet does not by itself imply full Enterprise Beans or Messaging support.

Tomcat and Jetty focus on web-container capabilities. Products such as GlassFish, WildFly, Payara, Open Liberty and TomEE offer different Jakarta EE implementations/configurations. Do not infer support from the product name alone or a historical server comparison. Consult the compatibility listing for the precise release/profile and the vendor's supported JDKs.

Java EE 8/Jakarta EE 8 APIs generally use `javax.*`; Jakarta EE 9 moved the enterprise APIs to `jakarta.*`. This is not a blanket rename of Java SE packages. Align source imports, dependencies, descriptors, libraries and runtime together.

## Apply

A WAR has a Servlet, JSP views, persistence and a messaging consumer. Before deployment, record:

1. Required specification versions and namespace.
2. Target server version, profile, JDK and enabled features.
3. Data source, connection factory and destination bindings.
4. Packaging and dependency scopes for container-provided APIs.
5. Security roles, database migration and recovery procedures.

A missing class may mean the chosen profile lacks the API, the library is packaged incorrectly, or conflicting copies are loaded. Adding every API JAR to the WAR can create more class-loader conflicts.

## Cheatsheet

| Artifact / service | Meaning |
| --- | --- |
| JAR | Java classes/resources; may be a library or an executable application |
| WAR | Web application; classes and libraries live under `WEB-INF` |
| EAR | Groups enterprise modules and deployment metadata |
| Provided API dependency | Compile against the API the runtime is expected to supply |
| JNDI | Naming for managed resources/components; verify target bindings |
| Container lifecycle | Injection, transactions and callbacks require managed instances |
| Jakarta EE 11 | Minimum Java SE 17; verify profile and implementation certification |

## Check yourself

An application using a full-platform service deploys locally but fails on a web-only runtime. What should change?

**Answer:** Choose a runtime/configuration that implements the required capability, or redesign the application to use supported services. A deployment descriptor cannot create an absent implementation.

## Sources

[Jakarta compatible products](https://jakarta.ee/compatibility/) · [Jakarta EE 11](https://jakarta.ee/specifications/platform/11/) · [Apache Tomcat](https://tomcat.apache.org/) · [Open Liberty features](https://openliberty.io/docs/latest/reference/feature/feature-overview.html)
