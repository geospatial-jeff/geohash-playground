## Geohash-Playground
Utility for benchmarking spatial queries on geohashes from a JSON configuration file.
This package benchmarks against the following prefix search methods:
- Builtin
- Trie
- GTrie
- Lexpy (Trie)
- Lexpy (DAWG)
- Completion DAWG


#### Usage
Run a benchmark with `benchmark <fname>` where `<fname>` is a JSON of the following format:

```json
{
    "query_iterations": 30,
    "index_iterations": 1,
    "hash_precision": 3,
    "hash_count": 1000000,
    "geohash_extent": [-100, -120, 30, 60],
    "query_extent": [-111, -110, 42, 43],
    "outfolder": "/path/to/benchmark_output"
}
```

Upon completion, the benchmark will populate the outfolder with a box plot and summary statistics.