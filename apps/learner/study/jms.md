## Understand

JMS is the familiar name for Jakarta Messaging. A queue distributes each message among competing consumers; a topic delivers to subscriptions. A durable subscription can retain eligible messages while its consumer is absent. Durability, persistent delivery, acknowledgment and transactions solve different parts of the reliability problem.

The classic API uses Connection, Session, MessageProducer and MessageConsumer. JMSContext combines connection/session responsibilities in the simplified API. A session is a single-threaded context for application use; do not share it arbitrarily among worker threads. Container-managed injected contexts have additional restrictions.

In CLIENT_ACKNOWLEDGE mode, acknowledging one message acknowledges the session's delivered messages, not just that object. AUTO_ACKNOWLEDGE timing follows the receive/listener contract. A transacted session commits or rolls back its messaging work; it does not automatically include an unrelated JDBC connection.

## Apply

Standalone Messaging 3.1 sketch using a local transacted context:

```java
try (JMSContext context = factory.createContext(JMSContext.SESSION_TRANSACTED)) {
    context.createProducer().send(destination, "invoice-ready");
    context.commit();
}
```

`factory` and `destination` are configured provider resources. In a Jakarta EE component using JTA/container-managed messaging, use the container's transaction rules instead of manually committing an injected context. Processing must remain idempotent because failures and retries can produce duplicate business effects.

## Cheatsheet

| Mechanism | Distinction |
| --- | --- |
| Selector | Filters headers/properties using selector syntax, not arbitrary message-body text |
| Correlation ID / reply destination | Match an asynchronous response to its request |
| TemporaryQueue | Deleted with its creating connection; persistent messages cannot extend its lifetime |
| `BytesMessage.reset()` | Switch written bytes to read mode and rewind; `clearBody()` erases them |
| Delivery delay / TTL | Earliest eligibility / expiry; both measured from send time |
| QueueBrowser | Non-consuming observation, not a required fixed snapshot |
| CompletionListener | Send completion, not consumer acknowledgment; wait before reusing the Message |
| Poison message | Bound retries and route failures for inspection and controlled replay |

## Check yourself

A message has a 30-second delivery delay and a 20-second TTL. When can it be delivered?

**Answer:** It expires before becoming eligible. TTL does not restart after the delay. A delayed business process needs a lifetime long enough for its intended eligibility and processing window.

## Sources

[Jakarta Messaging specification](https://jakarta.ee/specifications/messaging/3.1/jakarta-messaging-spec-3.1.html) · [JMSContext API](https://jakarta.ee/specifications/messaging/3.1/apidocs/jakarta.messaging/jakarta/jms/JMSContext.html) · [MessageProducer API](https://jakarta.ee/specifications/messaging/3.1/apidocs/jakarta.messaging/jakarta/jms/MessageProducer.html)
