## Understand

### Baseline and learning objectives

ActiveMQ Classic and ActiveMQ Artemis are distinct broker implementations. These notes concentrate on the Artemis 2.x address model; operational details were checked against the 2.57 manual. A configuration name from Classic must not be assumed to configure the corresponding Artemis behavior. Clients also have protocol and API-version requirements, including the distinction between javax.jms and jakarta.jms libraries.

Read the JMS chapter first. Your objectives here are to connect messaging contracts to concrete broker routing, explain storage and flow-control behavior, and plan recovery from ambiguous failures. A broker's features support a reliable application, but do not by themselves make every downstream database or payment effect exactly once.

### Addresses, queues and routing types

An address is a routing destination. A queue stores messages for consumers. ANYCAST routes to one matching anycast queue; MULTICAST routes to matching multicast queues. Consumers on one queue compete for that queue's messages regardless of whether several consumers represent different business departments.

To let billing and shipping independently process every order event, give them separate subscription queues receiving the relevant routed copies. Adding more consumers to one work queue scales competition, not fan-out. Naming conventions should make address, queue and subscription ownership clear so operations staff can distinguish intended topology from accidental duplicate resources.

### Durability, persistence and storage

A durable queue and a persistent message solve related but different lifecycle questions. Check delivery mode, queue durability, journal configuration and transaction boundaries together. A message can also expire or be deliberately removed by policy. “Persistent” is not a promise of indefinite retention.

Storage must be sized for outages and recovery, not only average throughput. Backlogs consume journal/page storage, and multicast fan-out can leave copies pending for a slow subscription after faster subscriptions have progressed. Set capacity and retention policies from business recovery requirements rather than treating disk as unlimited.

## Apply

### Example A1: competing workers

Artemis broker configuration fragment, placed inside the appropriate core configuration document:

```xml
<addresses>
  <address name="orders">
    <anycast>
      <queue name="orders.work" />
    </anycast>
  </address>
</addresses>
```

Two consumers attached to orders.work divide its work. The fragment does not configure authentication, transport connectors, persistence storage or every production setting. Bind each client to the intended resource according to its protocol and naming rules. A producer successfully sending to an address does not prove that the desired queue and route existed.

### Example A2: independent subscribers

Artemis routing fragment for two independent queues:

```xml
<addresses>
  <address name="order.events">
    <multicast>
      <queue name="billing.events" />
      <queue name="shipping.events" />
    </multicast>
  </address>
</addresses>
```

Matching events can be routed to both queues, allowing independent acknowledgment and backlog. If billing is offline, shipping can continue while billing's queue retains eligible work under its configured policy. This independence consumes capacity: a forgotten subscription can keep accumulating work and needs a deliberate owner, alert and cleanup policy.

### Example A3: application-supplied duplicate identity

Artemis-specific JMS fragment on a configured Jakarta Messaging-compatible client:

```java
TextMessage message = context.createTextMessage(payload);
message.setStringProperty("_AMQ_DUPL_ID", operationId);
context.createProducer().send(destination, message);
```

Reuse the same operationId when retrying the same intended send. A fresh random value for every retry describes different identities and cannot suppress the duplicate as intended. The broker's duplicate cache has scope, size and persistence settings; do not mistake it for an infinite ledger of completed business operations. The consumer still needs an appropriate idempotency boundary for its own effects.

### Example A4: preserve affinity for an entity

JMS message-property fragment:

```java
message.setStringProperty("JMSXGroupID", "account-" + accountId);
```

With the corresponding Artemis grouping behavior, messages in a group are associated with a consumer to preserve affinity. This can help serialize an entity's stream, but a single hot group can limit parallelism. Client-side dispatch to arbitrary workers can undo the intended sequential processing. Define behavior for consumer failure, group ownership changes and replay.

## Advanced

### Message grouping and ordering boundaries

Grouping is an allocation mechanism, not an automatic transaction around every operation for an account. A consumer may fail after changing state but before acknowledgment, so the next consumer must tolerate repeated work. Include an operation identifier or sequence/version rule in the business contract where required.

Choose group cardinality deliberately. Grouping every message under one constant ID can force otherwise independent work through one consumer. Grouping each message under a fresh ID gives little useful entity affinity. Measure skew: a few very active accounts can dominate throughput even when the total number of groups is large.

### Duplicate detection limits

Artemis tracks duplicate IDs in a bounded per-address cache. Retention depends on cache size and configuration; older IDs can be displaced. Persistence of that cache is a separate setting. Duplicate detection is particularly useful when a sender cannot determine whether its previous send or commit reached the broker.

The guarantee is bounded by the mechanism's actual scope. An application retrying after a long outage should not assume the broker remembers every historical operation. Nor does filtering a duplicate send prove that a consumer's external HTTP operation was unique. Keep broker-level duplicate suppression and durable business deduplication conceptually separate.

### Redelivery, dead letters and expiry

Redelivery follows unsuccessful consumption or rollback according to the client and broker configuration. Use delays and a bounded attempt policy so a poison message does not monopolize consumers. Dead-letter routing requires a usable destination and appropriate address/queue configuration; merely naming a dead-letter address does not establish an operational replay workflow.

Expiry means the allowed lifetime elapsed, which is different from repeated processing failure. Diagnose expired messages by comparing send time, delivery delay, queue age and consumer capacity. A request that becomes invalid after five minutes may need an explicit business timeout response rather than an unnoticed move to an expiry destination.

### Paging, memory bounds and slow subscriptions

Paging allows the broker to move message storage out of memory under configured pressure. It does not eliminate disk usage or guarantee unchanged latency. Monitor page activity, disk headroom, journal latency and the slowest relevant consumers. Backlog growth can indicate a capacity imbalance even when process memory appears stable.

Address-full policies choose different outcomes such as paging, blocking, failing or dropping under defined conditions. These are business-visible behaviors. A producer timeout while blocked needs a retry policy that respects possible ambiguity. Silent dropping is unacceptable for some workflows but may be intentional for replaceable telemetry.

### Flow control, buffering and fairness

Producer and consumer flow-control settings bound buffering and influence throughput, latency and distribution. Classic prefetch and Artemis consumer windows are not interchangeable configuration names. Large buffers can improve bulk throughput while leaving more in-flight work with one consumer and complicating graceful shutdown.

Tune from measured workload rather than a generic “larger is faster” rule. Include message size, processing duration, acknowledgment batching, network latency and downstream database capacity. A consumer that accepts many messages but blocks on a small connection pool may make queue metrics look improved while merely relocating the backlog into application memory.

### High availability, clusters and failover

Clustering distributes routing/work across brokers; high availability addresses continuation after failures. Do not assume that enabling one establishes the other's guarantees. Shared-store and replication arrangements have different storage and coordination requirements. Network partitions can create competing views of which broker should be active if the failover design is incomplete.

A client can lose the response to a send or commit after the broker has applied it. Reconnecting does not remove this ambiguity. Test failure before submission, during commit, after broker acceptance and during acknowledgment. Coordinate duplicate detection, transaction recovery and business idempotency instead of treating reconnection as proof that all in-flight work has a known outcome.

## Production

### Diagnose a growing backlog

Compare arrival rate, successful completion rate, oldest-message age and retry volume. If consumers are active but progress is low, inspect thread dumps, dependency timeouts, database waits and poison-message loops. If messages are produced but the intended queue remains empty, inspect routing type, bindings, filters, permissions and protocol-specific destination configuration.

Do not add consumers before understanding the bottleneck. A saturated database can become less efficient under greater concurrent contention. Estimate the required throughput from business latency targets, then bound concurrency and apply backpressure at a controlled boundary.

### Run a controlled dead-letter replay

First identify the failure class and fix its cause. Preserve operation IDs, payload schema version and relevant audit metadata. Replay a small batch, verify business effects and monitor retries. A replay tool must not bypass authorization or reset identity in a way that makes a repeated payment appear new.

Define ownership of unresolved messages. A dead-letter queue without alerts and a response process is only another place to hide failed work. Retain enough diagnostic context while respecting sensitive-data retention and access restrictions.

### Test recovery instead of only startup

A broker restart test is useful but insufficient. Disconnect the producer during a transaction, stop a consumer after its database commit, exhaust a destination's capacity, and make one subscriber substantially slower than the others. Verify what users see and what operators must repair.

Record recovery-time and data-loss expectations for each topology. Backups and replication are not the same thing: replication can propagate an accidental deletion, while a backup without a tested restore process may not meet recovery needs. Include configuration, credentials, schemas and client compatibility in restore exercises, not only journal files.

## Exam reasoning

### Draw address, queue and consumer relationships

For routing questions, draw producers pointing to an address, the matching queues below it, and consumers below each queue. This prevents confusing multicast copies with competing consumption. Different consumer names do not create independent subscriptions automatically.

### Identify which product owns a setting

A question about Artemis paging cannot be answered by quoting a Classic prefetch property. Likewise, JMS API acknowledgment rules and broker-specific redelivery delays operate at different layers. Read the targeted product, protocol, client library and version before making a configuration claim.

### Avoid unbounded reliability claims

Duplicate detection is not an unlimited deduplication history. Grouping is not an external transaction. A durable queue is not infinite storage. Reconnection is not proof that an ambiguous commit failed. A cluster is not automatically a correctly configured high-availability pair.

## Cheatsheet

| Concept | Question to ask |
| --- | --- |
| Classic versus Artemis | Does this setting belong to the selected broker and client? |
| Address | Where are messages routed? |
| Queue | Where does one consumer group's work accumulate? |
| ANYCAST | Which one matching queue receives the routed message? |
| MULTICAST | Which matching queues receive independent copies? |
| Grouping | What entity needs affinity, and can hot groups bottleneck? |
| Duplicate detection | Is the ID stable, and what are cache scope/retention limits? |
| Redelivery | Is retry bounded, delayed and appropriate for this error? |
| Dead-letter handling | Is routing configured and is there an owner/replay procedure? |
| Expiry | Did business lifetime elapse before processing? |
| Paging | What happens to disk use and latency under pressure? |
| Address-full policy | Page, block, fail or drop: which business outcome is intended? |
| Flow control | Where is buffering bounded, including inside consumers? |
| Slow multicast queue | Which subscription retains backlog and storage? |
| Failover | Which in-flight outcomes become ambiguous? |
| Clustering versus HA | Distribution and failure continuity are different concerns |
| Recovery | Are topology, backups, credentials and business effects tested together? |

## Check yourself

### 1. Two departments, one queue

Billing and shipping consume from the same anycast queue but each needs every event. Why do they receive different subsets?

**Answer:** They compete on one queue. Use independent queues receiving the required multicast/topic copies when each business process needs its own consumption history.

### 2. Broker memory looks stable

Paging is active and process memory is stable while the backlog grows. Is capacity now unlimited?

**Answer:** No. Disk capacity, I/O performance and recovery time remain finite. Monitor storage and queue age, and correct the arrival/processing imbalance.

### 3. Advanced: fresh retry IDs

A producer retries an ambiguous send but generates a new duplicate-detection ID each time. Will the broker recognize the same operation through that mechanism?

**Answer:** No. Different IDs identify different sends to that cache. Preserve stable identity for the intended retry and still handle consumer-side business idempotency.

### 4. Advanced: one group for all accounts

Every account event uses JMSXGroupID equal to accounting. Why might additional consumers provide little throughput gain?

**Answer:** One group concentrates affinity. Select grouping keys around independent entities and measure skew, while preserving each entity's required sequencing.

### 5. Advanced: successful reconnect

A producer reconnects after losing the response to commit. Does reconnection prove the old transaction was rolled back?

**Answer:** No. The broker may have committed before the response was lost. Use the documented recovery behavior, duplicate suppression and stable business identity to handle ambiguity.

### 6. Expiry versus dead letters

A message expires while waiting behind a backlog. Is its expiry evidence that the consumer repeatedly failed to process it?

**Answer:** No. Lifetime elapsed, potentially before any attempt. Investigate delay, queue age and capacity separately from poison-message redelivery.

## Sources

Reviewed 2026-09-25. Artemis 2.x concepts; operational references checked against the 2.57 manual. Recheck exact configuration names when deploying another release.

- [Address model](https://artemis.apache.org/components/artemis/documentation/latest/address-model.html).
- [Message grouping](https://artemis.apache.org/components/artemis/documentation/latest/message-grouping.html).
- [Duplicate detection](https://artemis.apache.org/components/artemis/documentation/latest/duplicate-detection.html).
- [Redelivery and undelivered messages](https://artemis.apache.org/components/artemis/documentation/latest/undelivered-messages.html).
- [Message expiry](https://artemis.apache.org/components/artemis/documentation/latest/message-expiry.html).
- [Paging](https://artemis.apache.org/components/artemis/documentation/latest/paging.html).
- [Flow control](https://artemis.apache.org/components/artemis/documentation/latest/flow-control.html).
- [Client failover](https://artemis.apache.org/components/artemis/documentation/latest/client-failover.html).
- [High availability](https://artemis.apache.org/components/artemis/documentation/latest/ha.html).
- [Network isolation](https://artemis.apache.org/components/artemis/documentation/latest/network-isolation.html).
- [ActiveMQ Classic documentation](https://activemq.apache.org/components/classic/documentation/).
