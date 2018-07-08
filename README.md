# prospects-viewer
A tool used to scrape stats of NHL players/prospects. Generates markdown to view data. Can also dump the data to JSON.

# Usage
This command will generate the data for the Habs, store the data as JSON and store the data in a pickle for further uses.
All the http requests are cached in the `.request-cache` directory, in order to avoid spamming the web server.
```
python -m prospects "https://www.eliteprospects.com/team/64/montreal-canadiens/depth-chart" --json habs.json --pickle habs.pickle > habs.md

```

To generate the document faster, use the `--use-pickle` switch in order to use pre-computer data.
