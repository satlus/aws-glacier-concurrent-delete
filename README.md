# AWS Glacier Concurrent Deleter (AGCD)
This utility will delete AWS archive files from a glacier vault. It is concurrent by design, and can be customized to maximize throughput on your hardware.

## Requirements
  * A practical understanding of AWS Glacier
  * python3 (tested on 3.9.9)
  * [aws cli configured with the correct access key and secret for your vault](https://docs.aws.amazon.com/cli/latest/reference/configure/index.html)
  * An archive inventory json file

## Features
  * Deletes glacier archives in parallel via configurable ThreadPoolExecutor
  * Ability to resume delete operations from a specific ArchiveID (recover from failure)

## Limitations
  * Does not run the inventory retrieval job (you must do that first)

## Usage
### First Run
1. Ensure your aws cli is properly configured to connect to your vault
1. [Run the archive inventory job via the aws cli to produce a list of archives in a json file](https://docs.aws.amazon.com/amazonglacier/latest/dev/deleting-vaults-cli.html) (this can take up to 5hrs)
1. Edit [agcd.cfg](./agcd.cfg)

```
[DEFAULT]
dry_run = false
thread_pool_worker_delay_ms = 500
thread_pool_max_workers = 5
thread_name_prefix = agcd
logging_level = INFO
resume_from_archive_id = 
vault_name = <yourvaultname>
...
```

2. Ensure you replace `<yourvaultname>` with the actual name of your vault
3. Run the program
4. Inspect stdout or tail the log that was created in the ./logs directory

### Resume from a specific archive
If for some reason you have a failure during processing you can start where you left off.

1. Grep the log file for the first line that contains `Error`, e.g.:
```
2022-02-06 19:29:07 ERROR    Error deleting archive jA3EDhIk0H33Aelwu53l... CompletedProcess(args='aws glacier delete-archive --vault-name jcnas_0011321CEF38_2 --account-id - --archive-id="jA3EDhIk0H33Aelwu53lZheKATMK9HnHHPWJ9QIS3fOThtmod0nTntSuo7FUVexRsKAkrR4P53wcYueekv3ULN3z-qn_3dtXeGZrpT8Fu5XBHpTnNthEphNwmXedMhish6UoQgGlVg"', returncode=254)
```
2. copy the value from `---archive-id` above, without the quotes
3. set this value in the `resume_from_archive_id` in agcd.cfg
```
resume_from_archive_id=jA3EDhIk0H33Aelwu53lZheKATMK9HnHHPWJ9QIS3fOThtmod0nTntSuo7FUVexRsKAkrR4P53wcYueekv3ULN3z-qn_3dtXeGZrpT8Fu5XBHpTnNthEphNwmXedMhish6UoQgGlVg
```
4. Run the program, it will resume from the location of this archive id

### DryRun
Setting `dry_run = true` will echo the aws cli commands in the shell - useful for debugging.

## Roadmap