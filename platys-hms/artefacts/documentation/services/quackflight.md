# QuackFlight

DuckDB API Server with Arrow Flight SQL Airport support and concurrent writes/reads (quackpipe).

**[Documentation](https://github.com/quackscience/quackflight)** | **[GitHub](https://github.com/quackscience/quackflight)**

## How to enable?

```
platys init --enable-services QUACKFLIGHT
platys gen
```

## How to use it?

Execute DuckDB queries using the HTTP POST/GET API (compatible with the ClickHouse HTTP API)

```bash
<<<<<<< Updated upstream
curl -X POST "http://192.168.1.112:28261" \
=======
curl -X POST "http://10.156.72.251:28261" \
>>>>>>> Stashed changes
   -H "Content-Type: application/json" \
   -d 'SELECT version()'  
```   