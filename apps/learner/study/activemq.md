## Understand

ActiveMQ Classic and ActiveMQ Artemis are distinct broker implementations. Do not copy configuration element names, policies or client assumptions between them without checking the targeted product. These notes use Artemis's address model, which is also the focus of the Dummy Exam.

An Artemis address receives routed messages; queues store messages for consumers. ANYCAST routes to one matching anycast queue, while MULTICAST routes to each matching multicast queue. Consumers attached to the same queue compete. Topic-like fan-out normally involves multiple subscription queues, not multiple consumers of one shared queue.

Persistence requires appropriate message delivery and durable queue/storage configuration. A broker's acknowledgment protocol cannot make a nontransactional external payment exactly once. Use an application operation ID and a durable idempotency check.

## Apply

Conceptual Artemis broker configuration:

```xml
<addresses>
  <address name="orders">
    <anycast>
      <queue name="orders.work" />
    </anycast>
  </address>
</addresses>
```

Place this inside the appropriate broker configuration document for the selected Artemis release. Bind clients to the intended queue/address according to their protocol. Two consumers on `orders.work` divide work; they do not each receive an independent copy. For independent billing and shipping consumers that both need every event, design separate subscription queues and multicast routing.

## Cheatsheet

| Operation | Check |
| --- | --- |
| Repeated delivery | Transaction/ack boundary, delivery count, duplicate business effects |
| Poison messages | Redelivery delay/backoff, maximum attempts, dead-letter address and routing |
| Expired messages | TTL and expiry-address policy, not the same as failed processing |
| Growing backlog | Arrival rate vs processing rate, queue age, consumer errors and blocked resources |
| Paging | Broker memory pressure management; disk still has finite capacity |
| Flow control | Bound producer/consumer buffering; Classic prefetch and Artemis windows are not identical knobs |
| Failover | Test client reconnection and in-flight message ambiguity, not only broker restart |

## Check yourself

Both a billing consumer and a shipping consumer attach to one anycast queue. Why does each see only some events?

**Answer:** They compete on that queue. Independent subscribers need separate queues receiving the required routed copies. Adding more consumers to one queue increases competition rather than fan-out.

## Sources

[Artemis address model](https://artemis.apache.org/components/artemis/documentation/latest/address-model.html) · [Redelivery and undelivered messages](https://artemis.apache.org/components/artemis/documentation/latest/undelivered-messages.html) · [Paging](https://artemis.apache.org/components/artemis/documentation/latest/paging.html) · [Classic documentation](https://activemq.apache.org/components/classic/documentation/)
