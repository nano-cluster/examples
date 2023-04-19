# Simple example
```
$ nano-compose
running module [http_relay]: ...
running module [http_relay]: pid=335515
running module [db]: ...
running module [db]: pid=335516
running module [num]: ...
running module [num]: pid=335517
running module [book]: ...
running module [book]: pid=335518
running module [periodic]: ...
running module [periodic]: pid=335519
waiting: ...
======== Running on http://0.0.0.0:3000 ========
(Press CTRL+C to quit)
```

trying the http relay

```
curl -X POST -d '{"params":{"q":"foo"}}' localhost:3000/xrpc/book.book_search
```

