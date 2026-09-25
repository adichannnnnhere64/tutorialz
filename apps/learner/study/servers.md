## Understand

### Compatibility is a versioned contract

Jakarta EE is a set of specifications and integration requirements implemented by compatible runtimes. A product name alone does not tell you its supported platform release, profile, Java version, or enabled features. Verify the exact product version and certification target. This chapter uses Jakarta EE 10 as a concrete baseline, not as a claim that it is the newest release.

The Full Platform, Web Profile, and Core Profile offer different required capabilities. Web Profile is not just a servlet container, and Core Profile is not every web or enterprise service in a smaller download. Core Profile emphasizes a smaller service-oriented set including CDI Lite and REST-related APIs. An application requiring MDBs, full Enterprise Beans behavior, or specific resource adapters must select a runtime with those capabilities rather than assume every Jakarta-branded distribution includes them.

A servlet container such as a matching Tomcat release implements its documented web specifications, not the entire Jakarta EE Full Platform by default. Adding API JARs makes types available for compilation but does not install a transaction manager, EJB container, or messaging provider. A framework can supply selected services in an embedded application, but that is a different assembly and ownership model from a full application server.

### Namespace and Java version are separate axes

Java EE 8 and Jakarta EE 8 use many javax enterprise packages. Jakarta EE 9 moved those APIs to jakarta packages, creating a binary/source compatibility boundary for affected APIs. Not every javax package changed: Java SE packages such as javax.sql remain. A global text replacement is therefore an unsafe migration strategy.

The platform minimum JDK and the application's chosen JDK are also separate. Jakarta EE 10 specifies Java SE 11 or higher, while an application stack such as Spring Boot 3.5 requires at least Java 17. A server distribution may support a particular tested set of JDKs. Compilation with a newer JDK does not prove that the deployment runtime accepts the resulting bytecode or dependencies.

### Packaging expresses ownership

A WAR typically contains web application classes under WEB-INF/classes and application libraries under WEB-INF/lib. An EAR can group enterprise modules and shared libraries according to platform rules. An executable JAR with an embedded server bundles a different startup and dependency arrangement. None is inherently more correct; choose based on deployment, operations, and compatibility needs.

Container-provided API dependencies should normally be compile-time provided dependencies in a server deployment. Shipping a conflicting implementation or duplicate API inside the application can create class identity and linkage problems. Conversely, marking a library provided in an embedded application does not make it appear at runtime unless the assembly supplies it. Understand who provides each API and implementation.

## Apply

### Example SRV1: Choose a runtime by requirements

An application uses Servlet, JSP, CDI, Persistence, and local business transactions. Another also requires MDB consumption through a resource adapter and full Enterprise Beans services. Build a capability list for each application, then compare it with the exact supported profile and enabled server features.

Do not select a servlet-only distribution because both applications produce HTML. Their server-side dependencies differ. Likewise, do not select a large Full Platform deployment solely because the word enterprise appears in the project name. The worked decision is a traceable mapping from required services to documented runtime support, JDK compatibility, operations, and team constraints.

### Example SRV2: Inject a logical datasource reference

Jakarta EE component fragment:

```java
@jakarta.annotation.Resource(lookup = "java:comp/DefaultDataSource")
javax.sql.DataSource dataSource;
```

The Java type remains javax.sql.DataSource because it is a Java SE API. The annotation is jakarta.annotation.Resource on this baseline. The lookup refers to the platform's default datasource where available and configured appropriately. A real application may use an explicitly named logical resource to avoid silently relying on a server default.

Injection does not prove the datasource points to the intended environment, has correct permissions, or participates in the desired transaction model. Verify the binding, driver, pool configuration, credentials, validation, and recovery settings. Keep environment-specific credentials out of application source.

### Example SRV3: Diagnose duplicate class identity

A deployment fails with an error that appears to say a class cannot be cast to another class with the same fully qualified name. Inspect which class-loader loaded each class and from which archive. Java type identity includes the defining loader, not only the textual class name.

A common cause is packaging one copy in a shared server library and another in WEB-INF/lib, then passing objects across the boundary. Remove or realign the duplicate according to the server's supported class-loading model; do not blindly change every dependency to parent-first or child-first. The correct fix depends on ownership and the loader boundary involved.

### Example SRV4: Trace a namespace mismatch

An old application references javax.servlet.http.HttpServlet, while the selected container supplies jakarta.servlet.http.HttpServlet. These are different types. Merely installing the latest servlet API beside the old application does not make the old class implement the new container contract.

Rebuild against compatible dependencies or use a supported migration tool and then test the transformed application thoroughly. Include deployment descriptors, tag libraries, reflective class names, service metadata, and transitive libraries in the audit. A successful package rename in application source is only one part of the migration.

## Advanced

### Class-loader delegation and provider conflicts

Application servers can isolate modules and applications through class-loader hierarchies. Delegation policies vary by product and by protected package categories. Tomcat's documented web-application loading behavior, for example, is not a universal rule for every full application server. Read the selected version's documentation before changing delegation settings.

ClassNotFoundException usually indicates a requested class could not be found through the attempted loading path. NoClassDefFoundError can also reflect a class that was present at compilation but unavailable at runtime, or a failed initialization dependency. NoSuchMethodError often points to incompatible runtime library versions. Diagnose the first causal failure and archive origin instead of adding random JARs until the top-level message changes.

Providers for JSON, persistence, logging, and validation can be selected through service metadata or container integration. Duplicate providers may change behavior even when no immediate linkage error appears. Shading can accidentally merge or discard service descriptors. Build an inventory of runtime artifacts and test the actual packaged archive, not only the IDE classpath.

### Resource binding and managed services

JNDI names separate a logical application reference from an environment binding. Portable namespaces such as java:comp, java:module, java:app, and java:global express different scopes, while vendor configuration controls many concrete resource definitions. Keep logical names stable and environment mappings explicit. A successful lookup establishes a reference, not the correctness of its permissions or destination.

Use managed executors, datasources, connection factories, and transaction services where the platform supplies them. Creating unmanaged threads or independent pools inside a container can bypass lifecycle, context, monitoring, and shutdown integration. That does not mean all application-created objects are forbidden; it means resources with container-managed responsibilities need deliberate ownership.

A resource adapter integrates an enterprise information system with container services, potentially including pooling, transactions, and message inflow. Verify supported transaction modes and recovery configuration. A connection factory JNDI binding alone does not prove XA coordination, high availability, or the right queue/topic routing.

### Profiles, optional features, and portability

Certification describes conformance to a specific specification target under documented conditions. It is valuable evidence, but does not guarantee every vendor extension or every historical optional feature. Applications relying on proprietary deployment descriptors, clustering APIs, or management endpoints have additional portability requirements beyond the standard API surface.

CDI Lite, Enterprise Beans Lite, and a server's marketing term lightweight are different concepts. Compare actual included specifications and versions. MicroProfile is another set of specifications often implemented alongside Jakarta capabilities; it is not interchangeable with the Jakarta EE Full Platform. Keep its version and required features explicit when using health, configuration, fault tolerance, or telemetry integrations.

### Deployment evolution and shared infrastructure

Rolling deployments run old and new code simultaneously. Shared database schema, serialized session data, message schemas, and remote contracts must tolerate that overlap. A compatible JDK upgrade does not guarantee compatible serialized application state. Consider draining sessions, externalizing stable state, or explicit migration strategies rather than assuming in-memory objects survive arbitrary redeployment.

Server-level shared libraries simplify central management but couple applications to coordinated upgrades. Application-bundled libraries isolate versions but can conflict with provided APIs and consume more resources. Choose based on the server's supported model and deployment governance. Document the decision so a future patch does not accidentally replace one application's private library for every tenant on the server.

## Production

### Build a deployment manifest

Record artifact digest, application version, JDK vendor/version, server distribution/version, enabled features, logical resource names, external configuration, and schema/message compatibility assumptions. Pin immutable artifacts rather than downloading an unspecified latest server during every deployment. Keep credentials and signing material outside the manifest while recording safe identifiers for their managed versions.

Validate startup with representative datasource and broker settings. A default in-memory database can make a deployment look healthy while production data remains disconnected. Health checks should distinguish process life from readiness to serve useful traffic. Verify management endpoints are bound and authorized deliberately, not exposed merely because the server enables them.

### Diagnosis: start from the earliest cause

Capture the first startup error with its nested cause, then classify it as bytecode compatibility, missing API, linkage conflict, discovery, binding, authentication, schema, or network failure. Later exceptions may be consequences. Compare the packaged dependency tree and effective server configuration with the last working deployment.

For runtime incidents, correlate request latency with thread pools, database waits, broker backlog, garbage collection, and class-loader retention after redeployments. Repeated deployment can reveal leaks where static registries or unmanaged threads retain old application loaders. Restarting may restore capacity temporarily, but the durable fix is correct lifecycle cleanup and ownership.

## Exam reasoning

### Match requirement to capability

First identify the platform release, profile, JDK, packaging, and services required. Do not infer Full Platform support from the presence of Servlet or a familiar server brand. A compile-time API dependency is not a runtime implementation.

For class-loading questions, consider both class name and defining loader, then examine archive placement and version compatibility. For resource questions, distinguish logical reference, concrete binding, and transaction mode. For migration questions, separate enterprise namespace changes from Java SE packages and bytecode requirements.

A strong answer includes operational consequences. An embedded server can simplify a self-contained artifact but moves configuration and dependency ownership into that artifact. A shared application server can centralize services but introduces shared upgrade coordination. Choose from constraints rather than treating one packaging style as universally modern or obsolete.

## Cheatsheet

| Concern | Verify |
| --- | --- |
| Platform compatibility | Exact product version, profile, and specification release |
| Servlet container | Documented web capabilities, not assumed Full Platform |
| API JAR | Compilation contract, not service implementation |
| javax to jakarta | Affected enterprise APIs only; Java SE packages remain |
| JDK | Application bytecode and server-supported runtime |
| WAR | Application classes and libraries under WEB-INF |
| EAR | Enterprise module assembly and sharing rules |
| Executable JAR | Embedded runtime and dependency ownership |
| Class identity | Fully qualified name plus defining class-loader |
| NoSuchMethodError | Often runtime binary-version mismatch |
| JNDI binding | Logical name versus configured resource |
| Managed executor | Container lifecycle and context integration |
| Rolling upgrade | Old/new schema, message, and session compatibility |
| Diagnosis | Earliest cause, artifact origin, effective configuration |

## Check yourself

### 1. API dependency

Does adding the EJB API to a servlet-only container install EJB services?

**Answer:** No. It supplies types, not the required container implementation and integration.

### 2. Namespace exception

Should javax.sql.DataSource become jakarta.sql.DataSource during migration?

**Answer:** No. DataSource is a Java SE API and remains in javax.sql. Only the affected enterprise namespaces migrate.

### 3. Profile choice

Can every Core Profile runtime be assumed to support MDBs?

**Answer:** No. Check required capabilities against the exact profile and implementation features. Core Profile is not the Full Platform.

### 4. Advanced: same-name cast

How can two identically named classes fail a cast?

**Answer:** Different defining class-loaders create distinct runtime types. Inspect archive origin and loader ownership to resolve duplicate or incompatible packaging.

### 5. Advanced: provided dependency

Why might an executable JAR fail after a needed implementation is marked provided?

**Answer:** Its runtime assembly may not supply that implementation. Provided is appropriate only when the deployment environment actually owns and supplies the dependency.

### 6. Advanced: rolling compatibility

Why can a valid new WAR still break a rolling deployment?

**Answer:** Old and new instances may disagree about shared schema, messages, remote contracts, or serialized sessions. Compilation does not establish cross-version runtime compatibility.

## Sources

Reviewed 2026-09-25. Baseline: Jakarta EE 10; product examples illustrate documented capability boundaries, not a current product recommendation.

- [Jakarta EE 10 Platform](https://jakarta.ee/specifications/platform/10/)
- [Jakarta EE 10 Web Profile](https://jakarta.ee/specifications/webprofile/10/)
- [Jakarta EE 10 Core Profile](https://jakarta.ee/specifications/coreprofile/10/)
- [Compatible product listings](https://jakarta.ee/compatibility/)
- [Tomcat namespace migration](https://tomcat.apache.org/migration-10.html)
- [Tomcat 10.1 class-loader behavior](https://tomcat.apache.org/tomcat-10.1-doc/class-loader-howto.html)
- [Jakarta Concurrency](https://jakarta.ee/specifications/concurrency/3.1/)
- [Jakarta Connectors](https://jakarta.ee/specifications/connectors/2.1/)
