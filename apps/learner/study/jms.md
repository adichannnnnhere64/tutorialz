## Understand

### Baseline, prerequisites and objectives

JMS is the familiar name for Jakarta Messaging. This chapter targets Messaging 3.1 with jakarta.jms imports and Java 17. Older JMS applications may use javax.jms; do not mix those API namespaces with incompatible provider libraries. You should understand exceptions, resource ownership, transactions and basic network failure before studying the advanced sections.

Messaging separates sending from processing. The producer can submit work without waiting for the eventual business operation, but this introduces explicit questions about storage, routing, ordering, acknowledgment, retries and recovery. A successful send does not mean a customer was charged or a shipment was booked. Name the particular boundary whose success has actually been observed.

### Queues, topics and subscription identity

A queue distributes messages among competing consumers. That describes distribution, not an exactly-once guarantee for arbitrary business effects. A topic distributes to subscriptions; multiple subscriptions can independently receive a publication. Consumers on one shared subscription compete for that subscription's work.

Durability belongs to the subscription's lifetime, while persistent delivery belongs to message delivery guarantees under the provider's configuration and contract. An unshared durable subscription has one active consumer. A shared durable subscription allows several consumers on the same subscription, distributing its messages among them. A consumer disconnecting is not necessarily the same event as deleting its durable subscription.

### Connections, sessions and context ownership

The classic API separates Connection, Session, MessageProducer and MessageConsumer. The simplified JMSContext combines connection/session responsibilities and creates JMSProducer/JMSConsumer collaborators. A session represents a single-threaded context for application use. Do not share one session across arbitrary worker threads merely because the connection is long-lived.

In a standalone client, explicitly created contexts can be closed with try-with-resources. In a Jakarta EE component, an injected context is container-managed and has different lifecycle and transaction restrictions. Closing or committing it as though it were a locally owned client resource can be incorrect. Establish whether the example is standalone or container-managed before interpreting its code.

## Apply

### Example J1: commit a local messaging transaction

Standalone Messaging 3.1 fragment; factory and destination are configured provider resources:

```java
try (JMSContext context =
         factory.createContext(JMSContext.SESSION_TRANSACTED)) {
    context.createProducer().send(destination, "invoice-ready");
    context.commit();
}
```

The local transaction controls the messaging work in this context. It does not automatically include an unrelated JDBC connection. Closing the context after an uncommitted transaction does not substitute for a successful commit. If the network fails during commit, the caller may need recovery logic because the observed exception does not always reveal the server's final outcome.

### Example J2: select using a typed message property

Messaging 3.1 fragments on a configured context:

```java
TextMessage message = context.createTextMessage("{\"orderId\":42}");
message.setStringProperty("region", "APAC");
message.setIntProperty("priorityLevel", 3);
context.createProducer().send(destination, message);
JMSConsumer consumer = context.createConsumer(
    destination, "region = 'APAC' AND priorityLevel >= 2");
```

The selector evaluates headers/properties using its defined syntax. It is not a JSONPath expression and does not inspect orderId inside the body. Treat property types as part of the message contract; a string that visually looks like a number is not interchangeable with every numeric property. Close or otherwise manage the consumer consistently with the context's ownership.

### Example J3: CLIENT_ACKNOWLEDGE is session-wide

Standalone nontransacted context fragment; both receives must return non-null messages for this demonstration:

```java
try (JMSContext context =
         factory.createContext(JMSContext.CLIENT_ACKNOWLEDGE)) {
    JMSConsumer consumer = context.createConsumer(destination);
    Message first = consumer.receive(1000);
    Message second = consumer.receive(1000);
    if (first != null && second != null) {
        second.acknowledge();
    }
}
```

Acknowledging second acknowledges the messages consumed by that session, not only the second Java object. Therefore process and acknowledgment boundaries must be designed together. This snippet demonstrates the contract; it is not a production processing loop because it intentionally omits business handling and the policy for receive timeouts.

### Example J4: delayed delivery does not restart TTL

Messaging 3.1 producer fragment:

```java
context.createProducer()
    .setDeliveryDelay(30_000)
    .setTimeToLive(20_000)
    .send(destination, "too-late");
```

The message expires before its earliest delivery eligibility. Both intervals relate to sending, not to the eventual consumer's first attempt. A real delayed workflow needs enough lifetime for the delay, queue waiting, and processing policy. Time-to-live zero means no expiration limit from this setting; it does not mean immediate expiration.

## Advanced

### Acknowledgment modes and transaction boundaries

AUTO_ACKNOWLEDGE behavior depends on whether consumption uses a synchronous receive or a message listener. Do not assume that the provider can observe business processing performed after a synchronous receive has returned. CLIENT_ACKNOWLEDGE gives the application an explicit acknowledgment point but retains its session-wide semantics. DUPS_OK_ACKNOWLEDGE permits more relaxed acknowledgment and possible duplicates.

A transacted session uses commit/rollback for its work rather than ordinary acknowledgment-mode behavior. In a container with JTA, the component transaction arrangement governs participation. If message consumption and database mutation must share a global transaction, both resources and the transaction manager must support the chosen arrangement. Otherwise use a recoverable design such as an inbox/deduplication record around the local database effect.

### Durable and shared subscription changes

Subscription identity involves the subscription name and relevant client identifier rules. Reusing an identity with a different selector or topic is not a harmless rename: permitted behavior depends on subscription type and whether consumers are active. Treat changes as a migration requiring a decision about retained messages.

A durable subscription can accumulate messages while consumers are absent, subject to expiration and configured storage limits. It is not an infinite archive. Monitor inactive subscriptions, define cleanup ownership, and avoid creating a fresh durable name for every application restart unless that behavior is intentional.

### Ordering and concurrent completion

Separate enqueue order, delivery order and business completion order. Multiple producers, consumers, sessions, priorities, redelivery and delivery delay complicate broad FIFO claims. Even if a particular stream is delivered in order, handing messages to independent workers can reorder the resulting database commits.

If a business entity requires serialized changes, define a grouping or partitioning strategy supported by the provider and enforce version/idempotency rules in the consumer. Ordering is not a substitute for duplicate handling. A replayed older event should not blindly overwrite newer state simply because it was delivered again.

### Selectors, missing properties and schema evolution

Selectors use a SQL-like expression language with defined types and null/unknown behavior. A property that is absent does not necessarily behave like an empty string or zero. Test selectors against missing and incorrectly typed properties, not only ideal examples.

Version message schemas deliberately. Optional additions can be easier to evolve than changing a property's type under the same name. Validate payload shape and allowed operations before processing. A selector can reduce which messages reach a consumer, but it does not establish authorization for the business effect.

### Asynchronous send and message reuse

A CompletionListener reports completion of an asynchronous send, not completion of downstream consumption. Do not mutate or reuse the Message until the send's completion contract permits it. Keep callbacks short and follow restrictions on operations performed from callback threads.

Send failure can be ambiguous across a network interruption. Generating a new business operation identifier on every retry defeats idempotency. Keep a stable operation ID in the application contract and distinguish it from the provider-assigned JMSMessageID, whose purpose and generation rules are different.

### Body state, browsing and temporary destinations

BytesMessage has read/write state: reset prepares written bytes for reading and rewinds; clearBody removes the body and makes it writable. ObjectMessage introduces serialization and compatibility/security concerns; prefer a deliberately versioned data representation when crossing trust or language boundaries.

QueueBrowser observes without consuming, but its enumeration is not required to be a fixed snapshot immune to concurrent queue changes. Temporary destinations have connection-related lifetime rules. Marking messages persistent does not extend a TemporaryQueue beyond the lifetime defined for its creating connection.

## Production

### Design an idempotent consumer

Suppose a consumer writes an invoice update and loses connectivity before acknowledgment. The provider can redeliver the message even though the database change succeeded. Record a stable operation ID atomically with the database effect so a repeat can be recognized. If the effect is external, use the external system's idempotency contract and persist enough recovery state to resolve ambiguity.

Do not acknowledge first and assume a later database write cannot fail. Conversely, writing first and acknowledging later still leaves a duplicate-delivery window without coordination. Draw the failure points explicitly and decide whether local deduplication, a global transaction or another workflow fits the business invariant.

### Bound poison-message retries

A malformed or incompatible message may never succeed by immediate retry. Track delivery attempts, classify transient versus permanent errors, and define dead-letter handling. Dead-letter queues need monitoring, retention and a replay process; moving a message there is not the same as resolving its business consequence.

Replay should preserve identity and audit context, not silently become a new charge or shipment. After fixing a consumer bug, replay a controlled sample and verify effects before releasing a large backlog. Avoid logging entire sensitive payloads merely to diagnose one failing field.

### Plan shutdown and capacity

Stopping a consumer while it has in-flight work creates a recovery boundary. Stop accepting new work, allow a bounded drain interval, then let uncompleted work follow the provider's transaction/acknowledgment rules. Do not swallow failures during shutdown and report success for uncommitted processing.

Measure queue age as well as depth. A queue of 1,000 tiny messages and one of 1,000 large, slow operations represent different capacity demands. Bound worker concurrency against database and external-service capacity. More consumers can worsen contention and increase retries rather than improve throughput.

## Exam reasoning

### Identify the session and consumption mode

For acknowledgment questions, identify which messages the same session has consumed and whether it is transacted. For AUTO_ACKNOWLEDGE, distinguish receive from listener delivery. For a shared subscription, distinguish multiple consumers of one subscription from multiple independent subscriptions.

### Separate four reliability concepts

Persistent delivery, durable subscription, acknowledgment and business idempotency are not interchangeable. A durable subscription addresses absence of a consumer; persistence addresses provider delivery reliability; acknowledgment marks consumption progress; idempotency protects a repeated business operation. A scenario may require all four, plus sufficient storage and a recovery policy.

### Read time and lifecycle assumptions literally

A delivery delay cannot postpone the start of TTL. A temporary queue is not made permanent by persistent messages. A send-completion callback does not mean a consumer finished. A browse operation does not remove messages. These distinctions matter more than memorizing a method name without its contract.

## Cheatsheet

| Mechanism | Key distinction |
| --- | --- |
| Queue | Competing consumers, not guaranteed exactly-once business effects |
| Topic | Delivers to subscriptions |
| Durable subscription | Retains eligible work while consumers are absent |
| Shared subscription | Several consumers divide one subscription's work |
| Session/JMSContext | Define ownership and single-threaded application use |
| AUTO_ACKNOWLEDGE | Timing follows receive/listener contract |
| CLIENT_ACKNOWLEDGE | Acknowledges session-consumed messages, not one object only |
| DUPS_OK_ACKNOWLEDGE | Relaxed acknowledgment can allow duplicates |
| Local transaction | Coordinates that messaging session, not arbitrary JDBC work |
| JTA | Requires correctly enlisted resources and managed boundaries |
| Ordering | Delivery order differs from concurrent business completion |
| Selector | Header/property expression, not body search |
| CompletionListener | Send completion, not processing completion |
| TTL / delay | Expiration / earliest eligibility measured from send |
| BytesMessage.reset | Read mode and rewind, not body deletion |
| TemporaryQueue | Lifetime follows its creating connection's rules |
| QueueBrowser | Non-consuming observation, not a required immutable snapshot |
| Redelivery | Use stable business identity and recoverable handling |

## Check yourself

### 1. One shared subscription

Three consumers use one shared durable subscription. Does each receive every message independently?

**Answer:** No. They divide that subscription's work. Three independent subscriptions are a different arrangement and can each receive a publication.

### 2. Delay exceeds lifetime

A message has a 30-second delay and a 20-second TTL. Does it get a new 20-second lifetime after the delay?

**Answer:** No. It expires before becoming eligible; the lifetime does not restart when delivery becomes possible.

### 3. Advanced: partial processing and acknowledgment

A CLIENT_ACKNOWLEDGE session consumes A and B. Processing B succeeds, processing A has not occurred, and B is acknowledged. What is the risk?

**Answer:** The acknowledgment covers session-consumed messages, including A. The application can acknowledge work it has not successfully processed if it treats acknowledgment as per-message.

### 4. Advanced: lost acknowledgment after commit

A consumer commits a database change but loses the connection before acknowledgment reaches the provider. What must a safe retry design tolerate?

**Answer:** Redelivery after an already-completed effect. Use atomic local deduplication or an appropriate coordinated transaction/recovery design, rather than assuming delivery is unique.

### 5. Advanced: asynchronous send callback

A producer's CompletionListener reports success. Can the UI claim the remote business operation finished?

**Answer:** No. The callback establishes send completion under the API contract. A separate application response or observable workflow state is needed to establish business completion.

### 6. Selector and body mismatch

The JSON body contains region=APAC, but no region message property exists. Must a selector using region = 'APAC' match?

**Answer:** No. The selector evaluates its defined headers/properties, not arbitrary JSON body fields. Publish the correctly typed property if the routing contract requires it.

## Sources

Reviewed 2026-09-25. Baseline: Jakarta Messaging 3.1, Java 17. Broker retry, dead-letter and grouping policies remain provider-specific.

- [Messaging 3.1 specification](https://jakarta.ee/specifications/messaging/3.1/jakarta-messaging-spec-3.1.html).
- [JMSContext](https://jakarta.ee/specifications/messaging/3.1/apidocs/jakarta.messaging/jakarta/jms/JMSContext.html).
- [Session](https://jakarta.ee/specifications/messaging/3.1/apidocs/jakarta.messaging/jakarta/jms/Session.html).
- [Message](https://jakarta.ee/specifications/messaging/3.1/apidocs/jakarta.messaging/jakarta/jms/Message.html).
- [MessageProducer](https://jakarta.ee/specifications/messaging/3.1/apidocs/jakarta.messaging/jakarta/jms/MessageProducer.html).
- [CompletionListener](https://jakarta.ee/specifications/messaging/3.1/apidocs/jakarta.messaging/jakarta/jms/CompletionListener.html).
- [BytesMessage](https://jakarta.ee/specifications/messaging/3.1/apidocs/jakarta.messaging/jakarta/jms/BytesMessage.html).
- [QueueBrowser](https://jakarta.ee/specifications/messaging/3.1/apidocs/jakarta.messaging/jakarta/jms/QueueBrowser.html).
