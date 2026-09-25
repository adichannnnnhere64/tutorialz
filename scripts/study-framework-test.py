#!/usr/bin/env python3
"""Compile the actual framework snippets with explicit, minimal application stubs.

This checks API/type compatibility, not provider runtime or database guarantees.
Two Spring examples also execute against a real application context.
"""
import pathlib
import re
import subprocess
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
STUDY = ROOT / "apps/learner/study"


def snippet(topic, example):
    body = (STUDY / f"{topic}.md").read_text()
    part = body.split(f"### Example {example}:", 1)[1].split("\n### ", 1)[0].split("\n## ", 1)[0]
    return re.search(r"```java\n(.*?)\n```", part, re.S).group(1)


with tempfile.TemporaryDirectory(prefix="tutorialz-study-framework-") as directory:
    directory = pathlib.Path(directory)
    classpath_file = directory / "classpath.txt"
    subprocess.run(["mvn", "-B", "-q", "-f", str(ROOT / "tests/study-framework/pom.xml"),
                    "org.apache.maven.plugins:maven-dependency-plugin:3.8.1:build-classpath",
                    f"-Dmdep.outputFile={classpath_file}"], check=True)
    classpath = classpath_file.read_text().strip()
    context_imports = "import org.springframework.context.annotation.*;"
    fixtures = [
        ("spring", "S1", context_imports, "", """
class Repository {}
class Service { final Repository repository; Service(Repository r) { repository = r; } }
class Main { public static void main(String[] args) {
  try (var context = new org.springframework.context.annotation.AnnotationConfigApplicationContext(Services.class)) {
    if (context.getBean(Service.class).repository != context.getBean(Repository.class)) throw new AssertionError("Managed dependency was not injected");
  }
}}
""", True),
        ("spring", "S2", context_imports + "import org.springframework.beans.factory.ObjectProvider; import org.springframework.stereotype.*;", "", """
class Main { public static void main(String[] args) {
  try (var context = new org.springframework.context.annotation.AnnotationConfigApplicationContext(Job.class, Dispatcher.class)) {
    Dispatcher dispatcher = context.getBean(Dispatcher.class);
    if (dispatcher.next() == dispatcher.next()) throw new AssertionError("Prototype lookup reused an instance");
  }
}}
""", True),
        ("spring", "S3", "import org.springframework.transaction.annotation.*; import java.io.*;", "class Importer {", "void loadAndPersistOrders() throws IOException {} }", False),
        ("spring", "S4", "import org.springframework.cache.annotation.*;", "class Finder { Repository repository = new Repository();", "} class Invoice {} class Repository { Invoice findAuthorized(String t, long i) { return null; } }", False),
        ("hibernate", "H1", "import jakarta.persistence.*; import java.math.*;", "", "", False),
        ("hibernate", "H2", "import jakarta.persistence.*; import java.math.*;", "class MergeExample { void run(EntityManager em, Invoice detachedInvoice) {", "}} class Invoice { BigDecimal total; }", False),
        ("hibernate", "H4", "import jakarta.persistence.*; import java.util.*;", "class BatchExample { void run(EntityManager em, List<Object> invoices) {", "}}", False),
        ("jms", "J1", "import jakarta.jms.*;", "class SendExample { void run(ConnectionFactory factory, Destination destination) {", "}}", False),
        ("jms", "J2", "import jakarta.jms.*;", "class SelectorExample { void run(JMSContext context, Destination destination) throws JMSException {", "}}", False),
        ("jms", "J3", "import jakarta.jms.*;", "class AckExample { void run(ConnectionFactory factory, Destination destination) throws JMSException {", "}}", False),
        ("jms", "J4", "import jakarta.jms.*;", "class DelayExample { void run(JMSContext context, Destination destination) {", "}}", False),
        ("activemq", "A3", "import jakarta.jms.*;", "class DuplicateExample { void run(JMSContext context, Destination destination, String payload, String operationId) throws JMSException {", "}}", False),
        ("activemq", "A4", "import jakarta.jms.*;", "class GroupExample { void run(Message message, long accountId) throws JMSException {", "}}", False),
        ("spring-web", "W1", "import org.springframework.web.bind.annotation.*;", "", "class OrderView {} class OrderService { OrderView findVisibleOrder(long id) { return null; } }", False),
        ("spring-web", "W2", "import org.springframework.web.bind.annotation.*;", "", "", False),
        ("spring-web", "W4", "import org.springframework.web.bind.annotation.*;", "", "class OrderMissing extends RuntimeException {}", False),
        ("transactions", "D2", "", "class Query { void run(java.sql.Connection connection, String tenant, long id) throws java.sql.SQLException {", "} void consume(java.math.BigDecimal value) {} }", False),
        ("transactions", "D3", "", "class SavepointExample { void run(java.sql.Connection connection) throws java.sql.SQLException {", "} void insertOptionalAuditDetail(java.sql.Connection c) throws java.sql.SQLException {} }", False),
        ("servlets", "V1", "", "", "", False),
        ("servlets", "V2", "", "class ForwardExample { void run(jakarta.servlet.http.HttpServletRequest request, jakarta.servlet.http.HttpServletResponse response, Object orderView) throws Exception {", "}}", False),
        ("servlets", "V3", "", "class AsyncExample extends jakarta.servlet.http.HttpServlet { void run(jakarta.servlet.http.HttpServletRequest request) {", "}}", False),
        ("cdi", "C1", "", "", "interface PaymentGateway {}", False),
        ("cdi", "C2", "", "", "", False),
        ("cdi", "C3", "", "", "class OrderPlaced {}", False),
        ("cdi", "C4", "", "class Resources {", "} class ReportClient implements AutoCloseable { public void close() {} }", False),
        ("ejb", "B1", "", "", "interface Inventory { void reserve(long id, int quantity); }", False),
        ("ejb", "B2", "", "", "", False),
        ("ejb", "B3", "", "", "", False),
        ("ejb", "B4", "", "", "", False),
        ("rest", "R1", "", "", "class OrderView {} class OrderService { OrderView findVisibleOrder(long id) { return null; } }", False),
        ("security", "SEC3", "", "class SafeQuery { void run(java.sql.Connection connection, String tenant, String displayName) throws java.sql.SQLException {", "} void consume(long value) {} }", False),
        ("servers", "SRV2", "", "class Bindings {", "}", False),
    ]
    for topic, example, imports, prefix, suffix, execute in fixtures:
        dest = directory / f"{topic}-{example}"
        dest.mkdir()
        code = snippet(topic, example)
        if (topic, example) == ("cdi", "C3"):
            # Inherit only the explicitly named application helper, not CDI behavior.
            code = code.replace("class OrderObservers {", "class OrderObservers extends Metrics {")
            suffix += " class Metrics { void recordMetric(OrderPlaced event) {} }"
        public_class = re.search(r"public class (\w+)", code)
        source = dest / ((public_class.group(1) if public_class else "Example") + ".java")
        source.write_text(imports + "\n" + prefix + "\n" + code + "\n" + suffix)
        subprocess.run(["javac", "--release", "17", "-cp", classpath, str(source)], check=True)
        if execute:
            subprocess.run(["java", "-cp", str(dest) + ":" + classpath, "Main"], check=True)
        print(f"PASS {topic}/{example}: {'compiled and executed' if execute else 'API compilation'}")
