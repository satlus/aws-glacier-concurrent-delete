from concurrent.futures import ThreadPoolExecutor
import unittest

import agcd


class TestAGCD(unittest.TestCase):
    def setUp(self) -> None:
        self.default_configparser = agcd.config['DEFAULT']
        self.agcd_config = agcd.agcd_config
        self.agcd_config.thread_pool_runtime['executor'] = ThreadPoolExecutor(max_workers=5)

    def test_load_config_file(self):
        self.assertEqual(
            self.default_configparser['thread_pool_worker_delay_ms'], '600')

    def test_config_dataclass(self):
        self.assertEqual(True, self.agcd_config.dry_run)
        self.assertIsInstance(self.agcd_config.thread_pool_runtime['executor'], ThreadPoolExecutor)
        self.assertEqual(600, self.agcd_config.thread_pool_worker_delay_ms)
        self.assertEqual(10, self.agcd_config.thread_pool_max_workers)
        self.assertEqual('agcd', self.agcd_config.thread_name_prefix)
        self.assertEqual('INFO' , self.agcd_config.logging_level)
        #self.assertEqual('', self.agcd_config.resume_from_archive_id)
        self.assertEqual('jcnas_0011321CEF38_2', self.agcd_config.vault_name)
    
if __name__ == '__main__':
    unittest.main()
