import unittest
import subprocess
from update_sihn import downloadParseAndUpload 
from datetime import datetime

class TestRun(unittest.TestCase):

    def test_begin_date(self):
        result = downloadParseAndUpload(cod_mareografo="SFER", begin_date = datetime(2025,2,7))
        self.assertIsInstance(result, list)

    def test_run_begin_date(self):
        result = subprocess.run(["python","run.py","-b","2025-02-07","-e","2025-02-09","-o","/tmp/update_sihn_data.json"])
        
        # Check exit status
        self.assertEqual(result.returncode, 0)

    def test_run_relative_begin_date(self):
        result = subprocess.run(["python","run.py","-r","4","-o","/tmp/update_sihn_data.json"])
        
        # Check exit status
        self.assertEqual(result.returncode, 0)
