from __future__ import annotations

import os
import shutil
import io
import unittest
from typing import Dict, Any

from app import app
from database import init_database


def clean_environment() -> None:
    """Clean up test environment."""
    # remove upload, backup, trash directories and database file
    for folder in ['uploads', 'backups', 'trash']:
        shutil.rmtree(folder, ignore_errors=True)
        os.makedirs(folder, exist_ok=True)

    db_path: str = os.path.join('..', 'database', 'gallery.db')
    try:
        os.remove(db_path)
    except OSError:
        pass


class GalleryAPITest(unittest.TestCase):
    """Test cases for Gallery API."""
    
    def setUp(self) -> None:
        """Set up test fixtures."""
        clean_environment()
        init_database()
        self.client = app.test_client()

    def test_full_workflow(self) -> None:
        """Test complete workflow: upload, trash, restore, backup."""
        # Upload a dummy document file
        data: Dict[str, tuple[Any, str]] = {
            'files': (io.BytesIO(b"dummy content"), 'test.txt')
        }
        response = self.client.post('/api/upload', data=data, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 200)
        json_data: Dict[str, Any] = response.get_json()
        self.assertIn('files', json_data)
        self.assertEqual(len(json_data['files']), 1)
        file_id: int = json_data['files'][0]['id']

        # verify counts incremented
        resp = self.client.get('/api/counts')
        counts = resp.get_json()
        self.assertEqual(counts['documents'], 1)

        # Move file to trash
        resp = self.client.delete(f'/api/files/{file_id}')
        self.assertEqual(resp.status_code, 200)

        resp = self.client.get('/api/counts')
        counts = resp.get_json()
        self.assertEqual(counts['documents'], 0)

        resp = self.client.get('/api/trash')
        trash = resp.get_json()
        self.assertEqual(len(trash['documents']), 1)

        # restore from trash
        resp = self.client.post(f'/api/trash/{file_id}/restore')
        self.assertEqual(resp.status_code, 200)
        resp = self.client.get('/api/counts')
        counts = resp.get_json()
        self.assertEqual(counts['documents'], 1)

        # delete again and then permanently remove
        resp = self.client.delete(f'/api/files/{file_id}')
        self.assertEqual(resp.status_code, 200)
        resp = self.client.delete(f'/api/trash/{file_id}')
        self.assertEqual(resp.status_code, 200)
        resp = self.client.get('/api/trash')
        trash = resp.get_json()
        self.assertEqual(len(trash['documents']), 0)

        # upload again for backup test
        data = {
            'files': (io.BytesIO(b"backup content"), 'backup.txt')
        }
        resp = self.client.post('/api/upload', data=data, content_type='multipart/form-data')
        self.assertEqual(resp.status_code, 200)

        # create backup
        resp = self.client.post('/api/backup')
        self.assertEqual(resp.status_code, 200)
        backup_name = resp.get_json()['filename']
        self.assertTrue(os.path.exists(os.path.join('backups', backup_name)))

        # delete uploads folder to simulate loss
        shutil.rmtree('uploads')
        os.makedirs('uploads', exist_ok=True)

        # restore via API
        resp = self.client.post('/api/restore')
        self.assertEqual(resp.status_code, 200)

        # counts after restore: should be back to 1 document
        resp = self.client.get('/api/counts')
        counts = resp.get_json()
        self.assertEqual(counts['documents'], 1)


if __name__ == '__main__':
    unittest.main()
