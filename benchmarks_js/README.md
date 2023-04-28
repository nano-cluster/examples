# Simple Client-side Benchmark

the benchmark sends an array of 1,000 numbers `[0, 1, 2, ..]`
to `mycalc.sqsum` which returns the summation and the sum of squared values
the benchmark sends concurrent 2,000 requests
the benchmark took 1.5 seconds to run
it took ~0.039ms per request to call and 0.73ms to get the response
it took ~0.77ms (0.00077 seconds) to send the request and get the response


```
$ node index.mjs 
{ sum: 499500, sqsum: 332833500 }
time to send the 2k requests:  78 0.039
time to get responses:  1458 0.729
total time:  1536 0.768
```