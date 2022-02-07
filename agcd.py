from concurrent.futures import ThreadPoolExecutor
import configparser
from dataclasses import dataclass, field
from datetime import datetime

import json
import logging
from os import listdir
from string import Template
import subprocess
import sys
from time import sleep

config = configparser.ConfigParser()
config.read('agcd.cfg')


@dataclass
class AGCDConfig:
    dry_run: bool
    thread_pool_runtime: dict
    thread_pool_worker_delay_ms: int 
    thread_pool_max_workers: int
    thread_name_prefix: str
    logging_level: str 
    resume_from_archive_id: str
    vault_name: str


agcd_config = AGCDConfig(
            dry_run=True if config['DEFAULT']['dry_run'].lower().strip() == 'true' else False,
            thread_pool_runtime={'futures': None, 'executor': None},
            thread_pool_worker_delay_ms=int(config['DEFAULT']['thread_pool_worker_delay_ms']),
            thread_pool_max_workers=int(config['DEFAULT']['thread_pool_max_workers']),
            thread_name_prefix=config['DEFAULT']['thread_name_prefix'],
            logging_level=config['DEFAULT']['logging_level'],
            resume_from_archive_id=config['DEFAULT']['resume_from_archive_id'],
            vault_name=config['DEFAULT']['vault_name']
            )
    
time_stamp = datetime.now()
logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    filename=time_stamp.strftime('agcd-%m-%d-%Y_%H:%M:%S.log'))
logging.getLogger().setLevel(agcd_config.logging_level)


def get_archive_list_from_file(f_name):
    with open(f_name) as archive_json:
        archives = json.load(archive_json)

    return archives['ArchiveList']


def get_archive_index(a_list, a_name):
    index_list = [{'index': i, 'archive': a}
                  for i, a in enumerate(a_list) if a_list[i]['ArchiveId'] == a_name]
    if len(index_list) == 1:
        return index_list[0]['index']
    else:
        logging.error(
            "Found more than one entry for this archive, verify source file")
        sys.exit(1)


DELETE_CMD = Template(
    'aws glacier delete-archive --vault-name $vault_name --account-id - --archive-id="$archive_id"')

DELETE_DRY_RUN_CMD = Template(
    'echoo aws glacier delete-archive --vault-name $vault_name --account-id - --archive-id="$archive_id"')


def delete_command(archive_id, index):
    logging.info(f'deleting archive {index}')
    run_cmd = DELETE_DRY_RUN_CMD if agcd_config.dry_run else DELETE_CMD
    sleep(agcd_config.thread_pool_worker_delay_ms * .001)
    completed_process = subprocess.run(run_cmd.safe_substitute(
        archive_id=archive_id, vault_name=agcd_config.vault_name), shell=True)
    if completed_process.returncode == 0:
        return completed_process
    else:
        logging.error(
            f'Error deleting archive {archive_id[0:20]}... {completed_process}')
        agcd_config.thread_pool_runtime['executor'].shutdown(wait=False, cancel_futures=True)


def parallel_archive_delete(archive_list):
    with ThreadPoolExecutor(max_workers=agcd_config.thread_pool_max_workers, thread_name_prefix=agcd_config.thread_name_prefix) as executor:
        agcd_config.thread_pool_runtime['executor'] = executor
        futures = [executor.submit(delete_command, archive_id['ArchiveId'], index+1)
                   for index, archive_id in enumerate(archive_list)]
        agcd_config.thread_pool_runtime['futures'] = futures

        for future in futures:
            logging.info(future.result())


def main():
    archive_list = get_archive_list_from_file('output.json')
    if agcd_config.resume_from_archive_id:
        resume_index = get_archive_index(
            archive_list, agcd_config.resume_from_archive_id)
        archive_sublist = archive_list[resume_index:len(archive_list)]
        logging.debug(
            f'first sublist record is {archive_sublist[0]}, sublist length is {len(archive_sublist)}, parent list length is {len(archive_list)}')
        parallel_archive_delete(archive_sublist)
    else:
      parallel_archive_delete(archive_list)


if __name__ == '__main__':
    main()
