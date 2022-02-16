# -*- coding: utf-8 -*-
"""Client tests for the IQB-RIMS addon."""
import json
import mock
from nose.tools import *  # noqa (PEP8 asserts)
import pytest

from addons.iqbrims.client import (
    IQBRIMSClient,
    SpreadsheetClient,
    IQBRIMSFlowableClient,
    IQBRIMSWorkflowUserSettings,
    _user_settings_cache
)
from addons.iqbrims.tests.utils import MockResponse
from addons.iqbrims import settings

from tests.base import OsfTestCase

pytestmark = pytest.mark.django_db

class TestIQBRIMSClient(OsfTestCase):

    def test_create_content(self):
        client = IQBRIMSClient('0001')
        with mock.patch.object(client, '_make_request',
                               return_value=MockResponse('{"test": true}',
                                                         200)) as mkreq:
            client.create_content('folderid456', 'files.txt', 'text/plain', 'TEST')
            assert_equal(len(mkreq.mock_calls), 1)
            name, args, kwargs = mkreq.mock_calls[0]
            assert_equal(args, ('POST', 'https://www.googleapis.com/upload/drive/v2/files?uploadType=multipart'))
            assert_equal(kwargs['files']['data'][0], 'metadata')
            assert_equal(json.loads(kwargs['files']['data'][1]),
                         {'parents': [{'id': 'folderid456'}], 'title': 'files.txt'})
            assert_equal(kwargs['files']['data'][2], 'application/json; charset=UTF-8')
            assert_equal(kwargs['files']['file'],
                         ('files.txt',
                          'TEST',
                          'text/plain'))

    def test_update_content(self):
        client = IQBRIMSClient('0001')
        with mock.patch.object(client, '_make_request',
                               return_value=MockResponse('{"test": true}',
                                                         200)) as mkreq:
            client.update_content('fileid456', 'text/plain', 'TEST')
            assert_equal(len(mkreq.mock_calls), 1)
            name, args, kwargs = mkreq.mock_calls[0]
            assert_equal(args, ('POST', 'https://www.googleapis.com/upload/drive/v2/files/fileid456?uploadType=media'))
            assert_equal(kwargs['data'], 'TEST')

    def test_grant_access_from_anyone_first(self):
        client = IQBRIMSClient('0001')
        dummyresp = {'permissions': []}
        with mock.patch.object(client, '_make_request',
                               return_value=MockResponse(json.dumps(dummyresp),
                                                         200)) as mkreq:
            client.grant_access_from_anyone('fileid123')
            assert_equal(len(mkreq.mock_calls), 2)
            name, args, kwargs = mkreq.mock_calls[1]
            assert_equal(args, ('POST', 'https://www.googleapis.com/drive/v3/files/fileid123/permissions'))
            assert_equal(json.loads(kwargs['data']),
                         {'type': 'anyone', 'role': 'writer', 'allowFileDiscovery': False})

    def test_grant_access_from_anyone_second(self):
        client = IQBRIMSClient('0001')
        dummyresp = {'permissions': [{
          'id': 'permid456',
          'type': 'anyone',
          'role': 'reader',
        }]}
        with mock.patch.object(client, '_make_request',
                               return_value=MockResponse(json.dumps(dummyresp),
                                                         200)) as mkreq:
            client.grant_access_from_anyone('fileid123')
            assert_equal(len(mkreq.mock_calls), 2)
            name, args, kwargs = mkreq.mock_calls[1]
            assert_equal(args, ('PATCH', 'https://www.googleapis.com/drive/v3/files/fileid123/permissions/permid456'))
            assert_equal(kwargs['headers'], {'Content-Type': 'application/json'})
            assert_equal(kwargs['data'], '{"role": "writer"}')

    def test_revoke_access_from_anyone_no_access(self):
        client = IQBRIMSClient('0001')
        dummyresp = {'permissions': [{
          'id': 'permid456',
          'type': 'anyone',
          'role': 'writer',
        }]}
        with mock.patch.object(client, '_make_request',
                               return_value=MockResponse(json.dumps(dummyresp),
                                                         200)) as mkreq:
            client.revoke_access_from_anyone('fileid123', drop_all=True)
            assert_equal(len(mkreq.mock_calls), 2)
            name, args, kwargs = mkreq.mock_calls[1]
            assert_equal(args, ('DELETE', 'https://www.googleapis.com/drive/v3/files/fileid123/permissions/permid456'))

    def test_revoke_access_from_anyone_read(self):
        client = IQBRIMSClient('0001')
        dummyresp = {'permissions': [{
          'id': 'permid456',
          'type': 'anyone',
          'role': 'writer',
        }]}
        with mock.patch.object(client, '_make_request',
                               return_value=MockResponse(json.dumps(dummyresp),
                                                         200)) as mkreq:
            client.revoke_access_from_anyone('fileid123', drop_all=False)
            assert_equal(len(mkreq.mock_calls), 2)
            name, args, kwargs = mkreq.mock_calls[1]
            assert_equal(args, ('PATCH', 'https://www.googleapis.com/drive/v3/files/fileid123/permissions/permid456'))
            assert_equal(kwargs['headers'], {'Content-Type': 'application/json'})
            assert_equal(kwargs['data'], '{"role": "reader"}')


class TestIQBRIMSSpreadsheetClient(OsfTestCase):

    def test_add_files_no_dirs(self):
        client = SpreadsheetClient('0001')
        with mock.patch.object(client, 'ensure_columns',
                               side_effect=lambda sid, cols, row: cols):
            with mock.patch.object(client, '_make_request',
                                   return_value=MockResponse('{"test": true}',
                                                             200)) as mkreq:
                client.add_files('sheet01', 1, 'sheet02', 2,
                                 ['file1.txt', 'file2.txt'])
                assert_equal(len(mkreq.mock_calls), 3)
                name, args, kwargs = mkreq.mock_calls[0]
                assert_equal(json.loads(kwargs['data']), {
                  'range': 'sheet02!A2:C2',
                  'values': [['FALSE']],
                  'majorDimension': 'ROWS'
                })
                name, args, kwargs = mkreq.mock_calls[1]
                assert_equal(json.loads(kwargs['data']), {
                  'range': 'sheet01!A4:I4',
                  'values': [['file1.txt', '', '.txt', '', '', '.txt', '', ''],
                             ['file2.txt', '', '.txt', '', '', '', '', '']],
                  'majorDimension': 'ROWS'
                })
                name, args, kwargs = mkreq.mock_calls[2]
                requests = json.loads(kwargs['data'])['requests']
                assert_equal(len(requests), 5);
                assert_equal(requests[0], {
                  'addProtectedRange': {
                    'protectedRange': {
                      'range': {
                        'endRowIndex': 1,
                        'endColumnIndex': 8,
                        'sheetId': 1,
                        'startColumnIndex': 0,
                        'startRowIndex': 0
                      },
                      'warningOnly': True
                    }
                  }
                })
                assert_equal(requests[1], {
                  'addProtectedRange': {
                    'protectedRange': {
                      'range': {
                        'endRowIndex': 1 + 3,
                        'endColumnIndex': 8,
                        'sheetId': 1,
                        'startColumnIndex': 0,
                        'startRowIndex': 0 + 3
                      },
                      'warningOnly': True
                    }
                  }
                })
                assert_equal(requests[2], {
                  'addProtectedRange': {
                    'protectedRange': {
                      'range': {
                        'endRowIndex': 3 + 3,
                        'endColumnIndex': 3,
                        'sheetId': 1,
                        'startColumnIndex': 0,
                        'startRowIndex': 1 + 3
                      },
                      'warningOnly': True
                    }
                  }
                })
                assert_equal(requests[3], {
                  'addProtectedRange': {
                    'protectedRange': {
                      'range': {
                        'endRowIndex': 3 + 3,
                        'endColumnIndex': 6,
                        'sheetId': 1,
                        'startColumnIndex': 5,
                        'startRowIndex': 1 + 3
                      },
                      'warningOnly': True
                    }
                  }
                })
                assert_equal(requests[4], {
                  'autoResizeDimensions': {
                    'dimensions': {
                      'sheetId': 1,
                      'dimension': 'COLUMNS',
                      'startIndex': 1,
                      'endIndex': 2,
                    }
                  }
                })

    def test_add_files_with_dir(self):
        client = SpreadsheetClient('0001')
        with mock.patch.object(client, 'ensure_columns',
                               side_effect=lambda sid, cols, row: cols):
            with mock.patch.object(client, '_make_request',
                                   return_value=MockResponse('{"test": true}',
                                                             200)) as mkreq:
                client.add_files('sheet01', 1, 'sheet02', 2,
                                 ['file1.txt', 'file2.txt', 'test/file3.txt'])
                assert_equal(len(mkreq.mock_calls), 3)
                name, args, kwargs = mkreq.mock_calls[0]
                assert_equal(json.loads(kwargs['data']), {
                  'range': 'sheet02!A2:C2',
                  'values': [['FALSE']],
                  'majorDimension': 'ROWS'
                })
                name, args, kwargs = mkreq.mock_calls[1]
                assert_equal(json.loads(kwargs['data'])['range'], 'sheet01!A4:J4')
                assert_equal(len(json.loads(kwargs['data'])['values']), 4)
                assert_equal(json.loads(kwargs['data'])['values'][0],
                             ['file1.txt', '', '', '.txt', '', '', '.txt', '', ''])
                assert_equal(json.loads(kwargs['data'])['values'][1],
                             ['file2.txt', '', '', '.txt', '', '', '', '', ''])
                assert_equal(json.loads(kwargs['data'])['values'][2],
                             ['test', '', '', '-', '', '', '', '', ''])
                assert_equal(json.loads(kwargs['data'])['values'][3],
                             [u'\u2514\u2212\u2212', 'file3.txt', '', '.txt', '', '', '', '', ''])
                assert_equal(json.loads(kwargs['data'])['majorDimension'], 'ROWS')
                name, args, kwargs = mkreq.mock_calls[2]
                requests = json.loads(kwargs['data'])['requests']
                assert_equal(len(requests), 6);
                assert_equal(requests[0], {
                    'addProtectedRange': {
                      'protectedRange': {
                        'range': {
                          'endRowIndex': 1,
                          'endColumnIndex': 9,
                          'sheetId': 1,
                          'startColumnIndex': 0,
                          'startRowIndex': 0
                        },
                        'warningOnly': True
                      }
                    }
                })
                assert_equal(requests[1], {
                    'addProtectedRange': {
                      'protectedRange': {
                        'range': {
                          'endRowIndex': 1 + 3,
                          'endColumnIndex': 9,
                          'sheetId': 1,
                          'startColumnIndex': 0,
                          'startRowIndex': 0 + 3
                        },
                        'warningOnly': True
                      }
                    }
                })
                assert_equal(requests[2], {
                    'addProtectedRange': {
                      'protectedRange': {
                        'range': {
                          'endRowIndex': 5 + 3,
                          'endColumnIndex': 4,
                          'sheetId': 1,
                          'startColumnIndex': 0,
                          'startRowIndex': 1 + 3
                        },
                        'warningOnly': True
                      }
                    }
                })
                assert_equal(requests[3], {
                    'addProtectedRange': {
                      'protectedRange': {
                        'range': {
                          'endRowIndex': 5 + 3,
                          'endColumnIndex': 7,
                          'sheetId': 1,
                          'startColumnIndex': 6,
                          'startRowIndex': 1 + 3
                        },
                        'warningOnly': True
                      }
                    }
                })
                assert_equal(requests[4], {
                  'autoResizeDimensions': {
                    'dimensions': {
                      'sheetId': 1,
                      'dimension': 'COLUMNS',
                      'startIndex': 1,
                      'endIndex': 3,
                    }
                  }
                })
                assert_equal(requests[5], {
                  'repeatCell': {
                    'range': {
                      'endRowIndex': 3 + 3 + 1,
                      'endColumnIndex': 1,
                      'sheetId': 1,
                      'startColumnIndex': 0,
                      'startRowIndex': 3 + 3,
                    },
                    'cell': {
                      'userEnteredFormat': {
                        'textFormat': {
                          'bold': True,
                          'italic': True,
                        },
                      },
                    },
                    'fields': 'userEnteredFormat.textFormat',
                  }
                })

    def test_add_files_with_dirs(self):
        client = SpreadsheetClient('0001')
        with mock.patch.object(client, 'ensure_columns',
                               side_effect=lambda sid, cols, row: cols):
            with mock.patch.object(client, '_make_request',
                                   return_value=MockResponse('{"test": true}',
                                                             200)) as mkreq:
                client.add_files('sheet01', 1, 'sheet02', 2,
                                 ['file1.txt', 'file2.txt', 'test2/file4.txt', 'test1/file3.txt'])
                assert_equal(len(mkreq.mock_calls), 3)
                name, args, kwargs = mkreq.mock_calls[0]
                assert_equal(json.loads(kwargs['data']), {
                  'range': 'sheet02!A2:C2',
                  'values': [['FALSE']],
                  'majorDimension': 'ROWS'
                })
                name, args, kwargs = mkreq.mock_calls[1]
                assert_equal(json.loads(kwargs['data'])['range'], 'sheet01!A4:J4')
                assert_equal(len(json.loads(kwargs['data'])['values']), 6)
                assert_equal(json.loads(kwargs['data'])['values'][0],
                             ['file1.txt', '', '', '.txt', '', '', '.txt', '', ''])
                assert_equal(json.loads(kwargs['data'])['values'][1],
                             ['file2.txt', '', '', '.txt', '', '', '', '', ''])
                assert_equal(json.loads(kwargs['data'])['values'][2],
                             ['test1', '', '', '-', '', '', '', '', ''])
                assert_equal(json.loads(kwargs['data'])['values'][3],
                             [u'\u2514\u2212\u2212', 'file3.txt', '', '.txt', '', '', '', '', ''])
                assert_equal(json.loads(kwargs['data'])['values'][4],
                             ['test2', '', '', '-', '', '', '', '', ''])
                assert_equal(json.loads(kwargs['data'])['values'][5],
                             [u'\u2514\u2212\u2212', 'file4.txt', '', '.txt', '', '', '', '', ''])
                assert_equal(json.loads(kwargs['data'])['majorDimension'], 'ROWS')
                name, args, kwargs = mkreq.mock_calls[2]
                requests = json.loads(kwargs['data'])['requests']
                assert_equal(len(requests), 7);
                assert_equal(requests[0], {
                    'addProtectedRange': {
                      'protectedRange': {
                        'range': {
                          'endRowIndex': 1,
                          'endColumnIndex': 9,
                          'sheetId': 1,
                          'startColumnIndex': 0,
                          'startRowIndex': 0
                        },
                        'warningOnly': True
                      }
                    }
                })
                assert_equal(requests[1], {
                    'addProtectedRange': {
                      'protectedRange': {
                        'range': {
                          'endRowIndex': 1 + 3,
                          'endColumnIndex': 9,
                          'sheetId': 1,
                          'startColumnIndex': 0,
                          'startRowIndex': 0 + 3
                        },
                        'warningOnly': True
                      }
                    }
                })
                assert_equal(requests[2], {
                    'addProtectedRange': {
                      'protectedRange': {
                        'range': {
                          'endRowIndex': 7 + 3,
                          'endColumnIndex': 4,
                          'sheetId': 1,
                          'startColumnIndex': 0,
                          'startRowIndex': 1 + 3
                        },
                        'warningOnly': True
                      }
                    }
                })
                assert_equal(requests[3], {
                    'addProtectedRange': {
                      'protectedRange': {
                        'range': {
                          'endRowIndex': 7 + 3,
                          'endColumnIndex': 7,
                          'sheetId': 1,
                          'startColumnIndex': 6,
                          'startRowIndex': 1 + 3
                        },
                        'warningOnly': True
                      }
                    }
                })
                assert_equal(requests[4], {
                  'autoResizeDimensions': {
                    'dimensions': {
                      'sheetId': 1,
                      'dimension': 'COLUMNS',
                      'startIndex': 1,
                      'endIndex': 3,
                    }
                  }
                })
                assert_equal(requests[5], {
                  'repeatCell': {
                    'range': {
                      'endRowIndex': 3 + 3 + 1,
                      'endColumnIndex': 1,
                      'sheetId': 1,
                      'startColumnIndex': 0,
                      'startRowIndex': 3 + 3,
                    },
                    'cell': {
                      'userEnteredFormat': {
                        'textFormat': {
                          'bold': True,
                          'italic': True,
                        },
                      },
                    },
                    'fields': 'userEnteredFormat.textFormat',
                  }
                })
                assert_equal(requests[6], {
                  'repeatCell': {
                    'range': {
                      'endRowIndex': 5 + 3 + 1,
                      'endColumnIndex': 1,
                      'sheetId': 1,
                      'startColumnIndex': 0,
                      'startRowIndex': 5 + 3,
                    },
                    'cell': {
                      'userEnteredFormat': {
                        'textFormat': {
                          'bold': True,
                          'italic': True,
                        },
                      },
                    },
                    'fields': 'userEnteredFormat.textFormat',
                  }
                })

    def test_add_files_with_multibytes_dir(self):
        client = SpreadsheetClient('0001')
        with mock.patch.object(client, 'ensure_columns',
                               side_effect=lambda sid, cols, row: cols):
            with mock.patch.object(client, '_make_request',
                                   return_value=MockResponse('{"test": true}',
                                                             200)) as mkreq:
                client.add_files('sheet01', 1, 'sheet02', 2,
                                 [u'ファイル1.txt', u'ファイル2.txt',
                                  u'テスト/ファイル3.txt'])
                assert_equal(len(mkreq.mock_calls), 3)
                name, args, kwargs = mkreq.mock_calls[0]
                assert_equal(json.loads(kwargs['data']), {
                  'range': 'sheet02!A2:C2',
                  'values': [['FALSE']],
                  'majorDimension': 'ROWS'
                })
                name, args, kwargs = mkreq.mock_calls[1]
                assert_equal(json.loads(kwargs['data']), {
                  'range': 'sheet01!A4:J4',
                  'values': [[u'ファイル1.txt', '', '', '.txt', '', '', '.txt', '', ''],
                             [u'ファイル2.txt', '', '', '.txt', '', '', '', '', ''],
                             [u'テスト', '', '', '-', '', '', '', '', ''],
                             [u'\u2514\u2212\u2212', u'ファイル3.txt', '', '.txt', '', '', '', '', '']],
                  'majorDimension': 'ROWS'
                })
                name, args, kwargs = mkreq.mock_calls[2]
                requests = json.loads(kwargs['data'])['requests']
                assert_equal(len(requests), 6);
                assert_equal(requests[0], {
                    'addProtectedRange': {
                      'protectedRange': {
                        'range': {
                          'endRowIndex': 1,
                          'endColumnIndex': 9,
                          'sheetId': 1,
                          'startColumnIndex': 0,
                          'startRowIndex': 0
                        },
                        'warningOnly': True
                      }
                    }
                })
                assert_equal(requests[1], {
                    'addProtectedRange': {
                      'protectedRange': {
                        'range': {
                          'endRowIndex': 1 + 3,
                          'endColumnIndex': 9,
                          'sheetId': 1,
                          'startColumnIndex': 0,
                          'startRowIndex': 0 + 3
                        },
                        'warningOnly': True
                      }
                    }
                })
                assert_equal(requests[2], {
                    'addProtectedRange': {
                      'protectedRange': {
                        'range': {
                          'endRowIndex': 5 + 3,
                          'endColumnIndex': 4,
                          'sheetId': 1,
                          'startColumnIndex': 0,
                          'startRowIndex': 1 + 3
                        },
                        'warningOnly': True
                      }
                    }
                })
                assert_equal(requests[3], {
                    'addProtectedRange': {
                      'protectedRange': {
                        'range': {
                          'endRowIndex': 5 + 3,
                          'endColumnIndex': 7,
                          'sheetId': 1,
                          'startColumnIndex': 6,
                          'startRowIndex': 1 + 3
                        },
                        'warningOnly': True
                      }
                    }
                })
                assert_equal(requests[4], {
                  'autoResizeDimensions': {
                    'dimensions': {
                      'sheetId': 1,
                      'dimension': 'COLUMNS',
                      'startIndex': 1,
                      'endIndex': 3,
                    }
                  }
                })
                assert_equal(requests[5], {
                  'repeatCell': {
                    'range': {
                      'endRowIndex': 3 + 3 + 1,
                      'endColumnIndex': 1,
                      'sheetId': 1,
                      'startColumnIndex': 0,
                      'startRowIndex': 3 + 3,
                    },
                    'cell': {
                      'userEnteredFormat': {
                        'textFormat': {
                          'bold': True,
                          'italic': True,
                        },
                      },
                    },
                    'fields': 'userEnteredFormat.textFormat',
                  }
                })

    def test_add_files_with_preset_cols(self):
        client = SpreadsheetClient('0001')
        with mock.patch.object(client, 'ensure_columns',
                               side_effect=lambda sid, cols, row: cols + ['L9', 'L10']):
            with mock.patch.object(client, '_make_request',
                                   return_value=MockResponse('{"test": true}',
                                                             200)) as mkreq:
                client.add_files('sheet01', 1, 'sheet02', 2,
                                 ['file1.txt', 'file2.txt'])
                assert_equal(len(mkreq.mock_calls), 3)
                name, args, kwargs = mkreq.mock_calls[0]
                assert_equal(json.loads(kwargs['data']), {
                  'range': 'sheet02!A2:E2',
                  'values': [['FALSE', '', '']],
                  'majorDimension': 'ROWS'
                })
                name, args, kwargs = mkreq.mock_calls[1]
                assert_equal(json.loads(kwargs['data']), {
                  'range': 'sheet01!A4:K4',
                  'values': [['file1.txt', '', '.txt', '', '', '.txt', '', '', '', ''],
                             ['file2.txt', '', '.txt', '', '', '', '', '', '', '']],
                  'majorDimension': 'ROWS'
                })
                name, args, kwargs = mkreq.mock_calls[2]
                reqs = json.loads(kwargs['data'])['requests']
                assert_equal(len(reqs), 7)
                assert_equal(reqs[0], {
                    'addProtectedRange': {
                      'protectedRange': {
                        'range': {
                          'endRowIndex': 1,
                          'endColumnIndex': 8,
                          'sheetId': 1,
                          'startColumnIndex': 0,
                          'startRowIndex': 0
                        },
                        'warningOnly': True
                      }
                    }
                })
                assert_equal(reqs[1], {
                    'addProtectedRange': {
                      'protectedRange': {
                        'range': {
                          'endRowIndex': 1 + 3,
                          'endColumnIndex': 8,
                          'sheetId': 1,
                          'startColumnIndex': 0,
                          'startRowIndex': 0 + 3
                        },
                        'warningOnly': True
                      }
                    }
                })
                assert_equal(reqs[2], {
                    'addProtectedRange': {
                      'protectedRange': {
                        'range': {
                          'endRowIndex': 3 + 3,
                          'endColumnIndex': 3,
                          'sheetId': 1,
                          'startColumnIndex': 0,
                          'startRowIndex': 1 + 3
                        },
                        'warningOnly': True
                      }
                    }
                })
                assert_equal(reqs[3], {
                    'addProtectedRange': {
                      'protectedRange': {
                        'range': {
                          'endRowIndex': 3 + 3,
                          'endColumnIndex': 6,
                          'sheetId': 1,
                          'startColumnIndex': 5,
                          'startRowIndex': 1 + 3
                        },
                        'warningOnly': True
                      }
                    }
                })
                assert_equal(reqs[4], {
                  'autoResizeDimensions': {
                    'dimensions': {
                      'sheetId': 1,
                      'dimension': 'COLUMNS',
                      'startIndex': 1,
                      'endIndex': 2,
                    }
                  }
                })
                assert_equal(reqs[5], {
                    'updateDimensionProperties': {
                      'range': {
                        'sheetId': 1,
                        'dimension': 'COLUMNS',
                        'startIndex': 8,
                        'endIndex': 9,
                      },
                      'properties': {
                        'hiddenByUser': True,
                      },
                      'fields': 'hiddenByUser',
                    }
                })
                assert_equal(reqs[6], {
                    'updateDimensionProperties': {
                      'range': {
                        'sheetId': 1,
                        'dimension': 'COLUMNS',
                        'startIndex': 9,
                        'endIndex': 10,
                      },
                      'properties': {
                        'hiddenByUser': True,
                      },
                      'fields': 'hiddenByUser',
                    }
                })

    def test_add_files_with_complex_dirs(self):
        client = SpreadsheetClient('0001')
        with mock.patch.object(client, 'ensure_columns',
                               side_effect=lambda sid, cols, row: cols):
            with mock.patch.object(client, '_make_request',
                                   return_value=MockResponse('{"test": true}',
                                                             200)) as mkreq:
                client.add_files('sheet01', 1, 'sheet02', 2,
                                 ['Data_2022_Sample/manuscript.tex',
                                  'Data_2022_Sample/suppl.tex',
                                  'Data_2022_Sample/Fig1/Sample.key',
                                  'Data_2022_Sample/Fig1/B/processed/SampleB.png',
                                  'Data_2022_Sample/Fig1/B/raw/Sample01.csv',
                                  'Data_2022_Sample/Fig1/B/raw/Sample02.csv',
                                  'Data_2022_Sample/Fig2/Sample.key',
                                  'Data_2022_Sample/Fig2/A/processed/SampleA.png',
                                  'Data_2022_Sample/Fig2/A/processed/SampleA.txt',
                                  'Data_2022_Sample/Fig2/A/raw/Sample03.csv',
                                  'Data_2022_Sample/Fig2/A/raw/Sample04.csv',
                                  'Data_2022_Sample/Fig2/C/processed/SampleC.png',
                                  'Data_2022_Sample/Fig2/C/processed/SampleC.txt',
                                  'Data_2022_Sample/Fig2/C/raw/Sample05.csv'])
                assert_equal(len(mkreq.mock_calls), 3)
                name, args, kwargs = mkreq.mock_calls[0]
                assert_equal(json.loads(kwargs['data']), {
                  'range': 'sheet02!A2:C2',
                  'values': [['FALSE']],
                  'majorDimension': 'ROWS'
                })
                name, args, kwargs = mkreq.mock_calls[1]
                assert_equal(json.loads(kwargs['data'])['range'], 'sheet01!A4:M4')
                assert_equal(len(json.loads(kwargs['data'])['values']), 26)
                assert_equal(json.loads(kwargs['data'])['values'][0],
                             ['Data_2022_Sample', '', '', '', '', '', '-', '', '', '.csv', '', ''])
                assert_equal(json.loads(kwargs['data'])['values'][1],
                             ['├−−', 'manuscript.tex', '', '', '', '', '.tex', '', '', '.key', '', ''])
                assert_equal(json.loads(kwargs['data'])['values'][2],
                             ['├−−', 'suppl.tex', '', '', '', '', '.tex', '', '', '.png', '', ''])
                assert_equal(json.loads(kwargs['data'])['values'][3],
                             ['├−−', 'Fig1', '', '', '', '', '-', '', '', '.tex', '', ''])
                assert_equal(json.loads(kwargs['data'])['values'][4],
                             ['│', '├−−', 'Sample.key', '', '', '', '.key', '', '', '.txt', '', ''])
                assert_equal(json.loads(kwargs['data'])['values'][5],
                             ['│', '└−−', 'B', '', '', '', '-', '', '', '', '', ''])
                assert_equal(json.loads(kwargs['data'])['values'][6],
                             ['│', '', '├−−', 'processed', '', '', '-', '', '', '', '', ''])
                assert_equal(json.loads(kwargs['data'])['values'][7],
                             ['│', '', '│', '└−−', 'SampleB.png', '', '.png', '', '', '', '', ''])
                assert_equal(json.loads(kwargs['data'])['values'][8],
                             ['│', '', '└−−', 'raw', '', '', '-', '', '', '', '', ''])
                assert_equal(json.loads(kwargs['data'])['values'][9],
                             ['│', '', '', '├−−', 'Sample01.csv', '', '.csv', '', '', '', '', ''])
                assert_equal(json.loads(kwargs['data'])['values'][10],
                             ['│', '', '', '└−−', 'Sample02.csv', '', '.csv', '', '', '', '', ''])
                assert_equal(json.loads(kwargs['data'])['values'][11],
                             ['└−−', 'Fig2', '', '', '', '', '-', '', '', '', '', ''])
                assert_equal(json.loads(kwargs['data'])['values'][12],
                             ['', '├−−', 'Sample.key', '', '', '', '.key', '', '', '', '', ''])
                assert_equal(json.loads(kwargs['data'])['values'][13],
                             ['', '├−−', 'A', '', '', '', '-', '', '', '', '', ''])
                assert_equal(json.loads(kwargs['data'])['values'][14],
                             ['', '│', '├−−', 'processed', '', '', '-', '', '', '', '', ''])
                assert_equal(json.loads(kwargs['data'])['values'][15],
                             ['', '│', '│', '├−−', 'SampleA.png', '', '.png', '', '', '', '', ''])
                assert_equal(json.loads(kwargs['data'])['values'][16],
                             ['', '│', '│', '└−−', 'SampleA.txt', '', '.txt', '', '', '', '', ''])
                assert_equal(json.loads(kwargs['data'])['values'][17],
                             ['', '│', '└−−', 'raw', '', '', '-', '', '', '', '', ''])
                assert_equal(json.loads(kwargs['data'])['values'][18],
                             ['', '│', '', '├−−', 'Sample03.csv', '', '.csv', '', '', '', '', ''])
                assert_equal(json.loads(kwargs['data'])['values'][19],
                             ['', '│', '', '└−−', 'Sample04.csv', '', '.csv', '', '', '', '', ''])
                assert_equal(json.loads(kwargs['data'])['values'][20],
                             ['', '└−−', 'C', '', '', '', '-', '', '', '', '', ''])
                assert_equal(json.loads(kwargs['data'])['values'][21],
                             ['', '', '├−−', 'processed', '', '', '-', '', '', '', '', ''])
                assert_equal(json.loads(kwargs['data'])['values'][22],
                             ['', '', '│', '├−−', 'SampleC.png', '', '.png', '', '', '', '', ''])
                assert_equal(json.loads(kwargs['data'])['values'][23],
                             ['', '', '│', '└−−', 'SampleC.txt', '', '.txt', '', '', '', '', ''])
                assert_equal(json.loads(kwargs['data'])['values'][24],
                             ['', '', '└−−', 'raw', '', '', '-', '', '', '', '', ''])
                assert_equal(json.loads(kwargs['data'])['values'][25],
                             ['', '', '', '└−−', 'Sample05.csv', '', '.csv', '', '', '', '', ''])
                assert_equal(json.loads(kwargs['data'])['majorDimension'], 'ROWS')
                name, args, kwargs = mkreq.mock_calls[2]
                requests = json.loads(kwargs['data'])['requests']
                assert_equal(len(requests), 5 + 12);
                assert_equal(requests[0], {
                    'addProtectedRange': {
                      'protectedRange': {
                        'range': {
                          'endRowIndex': 1,
                          'endColumnIndex': 12,
                          'sheetId': 1,
                          'startColumnIndex': 0,
                          'startRowIndex': 0
                        },
                        'warningOnly': True
                      }
                    }
                })
                assert_equal(requests[1], {
                    'addProtectedRange': {
                      'protectedRange': {
                        'range': {
                          'endRowIndex': 1 + 3,
                          'endColumnIndex': 12,
                          'sheetId': 1,
                          'startColumnIndex': 0,
                          'startRowIndex': 0 + 3
                        },
                        'warningOnly': True
                      }
                    }
                })
                assert_equal(requests[2], {
                    'addProtectedRange': {
                      'protectedRange': {
                        'range': {
                          'endRowIndex': 27 + 3,
                          'endColumnIndex': 7,
                          'sheetId': 1,
                          'startColumnIndex': 0,
                          'startRowIndex': 1 + 3
                        },
                        'warningOnly': True
                      }
                    }
                })
                assert_equal(requests[3], {
                    'addProtectedRange': {
                      'protectedRange': {
                        'range': {
                          'endRowIndex': 27 + 3,
                          'endColumnIndex': 10,
                          'sheetId': 1,
                          'startColumnIndex': 9,
                          'startRowIndex': 1 + 3
                        },
                        'warningOnly': True
                      }
                    }
                })
                assert_equal(requests[4], {
                  'autoResizeDimensions': {
                    'dimensions': {
                      'sheetId': 1,
                      'dimension': 'COLUMNS',
                      'startIndex': 1,
                      'endIndex': 6,
                    }
                  }
                })
                # Data_2022_Sample
                assert_equal(requests[5], {
                  'repeatCell': {
                    'range': {
                      'endRowIndex': 1 + 3 + 1,
                      'endColumnIndex': 1,
                      'sheetId': 1,
                      'startColumnIndex': 0,
                      'startRowIndex': 1 + 3,
                    },
                    'cell': {
                      'userEnteredFormat': {
                        'textFormat': {
                          'bold': True,
                          'italic': True,
                        },
                      },
                    },
                    'fields': 'userEnteredFormat.textFormat',
                  }
                })
                # Fig1
                assert_equal(requests[6], {
                  'repeatCell': {
                    'range': {
                      'endRowIndex': 4 + 3 + 1,
                      'endColumnIndex': 2,
                      'sheetId': 1,
                      'startColumnIndex': 1,
                      'startRowIndex': 4 + 3,
                    },
                    'cell': {
                      'userEnteredFormat': {
                        'textFormat': {
                          'bold': True,
                          'italic': True,
                        },
                      },
                    },
                    'fields': 'userEnteredFormat.textFormat',
                  }
                })
                # B
                assert_equal(requests[7], {
                  'repeatCell': {
                    'range': {
                      'endRowIndex': 6 + 3 + 1,
                      'endColumnIndex': 3,
                      'sheetId': 1,
                      'startColumnIndex': 2,
                      'startRowIndex': 6 + 3,
                    },
                    'cell': {
                      'userEnteredFormat': {
                        'textFormat': {
                          'bold': True,
                          'italic': True,
                        },
                      },
                    },
                    'fields': 'userEnteredFormat.textFormat',
                  }
                })
                # processed
                assert_equal(requests[8], {
                  'repeatCell': {
                    'range': {
                      'endRowIndex': 7 + 3 + 1,
                      'endColumnIndex': 4,
                      'sheetId': 1,
                      'startColumnIndex': 3,
                      'startRowIndex': 7 + 3,
                    },
                    'cell': {
                      'userEnteredFormat': {
                        'textFormat': {
                          'bold': True,
                          'italic': True,
                        },
                      },
                    },
                    'fields': 'userEnteredFormat.textFormat',
                  }
                })
                # raw
                assert_equal(requests[9], {
                  'repeatCell': {
                    'range': {
                      'endRowIndex': 9 + 3 + 1,
                      'endColumnIndex': 4,
                      'sheetId': 1,
                      'startColumnIndex': 3,
                      'startRowIndex': 9 + 3,
                    },
                    'cell': {
                      'userEnteredFormat': {
                        'textFormat': {
                          'bold': True,
                          'italic': True,
                        },
                      },
                    },
                    'fields': 'userEnteredFormat.textFormat',
                  }
                })
                # Fig2
                assert_equal(requests[10], {
                  'repeatCell': {
                    'range': {
                      'endRowIndex': 12 + 3 + 1,
                      'endColumnIndex': 2,
                      'sheetId': 1,
                      'startColumnIndex': 1,
                      'startRowIndex': 12 + 3,
                    },
                    'cell': {
                      'userEnteredFormat': {
                        'textFormat': {
                          'bold': True,
                          'italic': True,
                        },
                      },
                    },
                    'fields': 'userEnteredFormat.textFormat',
                  }
                })
                # A
                assert_equal(requests[11], {
                  'repeatCell': {
                    'range': {
                      'endRowIndex': 14 + 3 + 1,
                      'endColumnIndex': 3,
                      'sheetId': 1,
                      'startColumnIndex': 2,
                      'startRowIndex': 14 + 3,
                    },
                    'cell': {
                      'userEnteredFormat': {
                        'textFormat': {
                          'bold': True,
                          'italic': True,
                        },
                      },
                    },
                    'fields': 'userEnteredFormat.textFormat',
                  }
                })
                # processed
                assert_equal(requests[12], {
                  'repeatCell': {
                    'range': {
                      'endRowIndex': 15 + 3 + 1,
                      'endColumnIndex': 4,
                      'sheetId': 1,
                      'startColumnIndex': 3,
                      'startRowIndex': 15 + 3,
                    },
                    'cell': {
                      'userEnteredFormat': {
                        'textFormat': {
                          'bold': True,
                          'italic': True,
                        },
                      },
                    },
                    'fields': 'userEnteredFormat.textFormat',
                  }
                })
                # raw
                assert_equal(requests[13], {
                  'repeatCell': {
                    'range': {
                      'endRowIndex': 18 + 3 + 1,
                      'endColumnIndex': 4,
                      'sheetId': 1,
                      'startColumnIndex': 3,
                      'startRowIndex': 18 + 3,
                    },
                    'cell': {
                      'userEnteredFormat': {
                        'textFormat': {
                          'bold': True,
                          'italic': True,
                        },
                      },
                    },
                    'fields': 'userEnteredFormat.textFormat',
                  }
                })
                # C
                assert_equal(requests[14], {
                  'repeatCell': {
                    'range': {
                      'endRowIndex': 21 + 3 + 1,
                      'endColumnIndex': 3,
                      'sheetId': 1,
                      'startColumnIndex': 2,
                      'startRowIndex': 21 + 3,
                    },
                    'cell': {
                      'userEnteredFormat': {
                        'textFormat': {
                          'bold': True,
                          'italic': True,
                        },
                      },
                    },
                    'fields': 'userEnteredFormat.textFormat',
                  }
                })
                # processed
                assert_equal(requests[15], {
                  'repeatCell': {
                    'range': {
                      'endRowIndex': 22 + 3 + 1,
                      'endColumnIndex': 4,
                      'sheetId': 1,
                      'startColumnIndex': 3,
                      'startRowIndex': 22 + 3,
                    },
                    'cell': {
                      'userEnteredFormat': {
                        'textFormat': {
                          'bold': True,
                          'italic': True,
                        },
                      },
                    },
                    'fields': 'userEnteredFormat.textFormat',
                  }
                })
                # raw
                assert_equal(requests[16], {
                  'repeatCell': {
                    'range': {
                      'endRowIndex': 25 + 3 + 1,
                      'endColumnIndex': 4,
                      'sheetId': 1,
                      'startColumnIndex': 3,
                      'startRowIndex': 25 + 3,
                    },
                    'cell': {
                      'userEnteredFormat': {
                        'textFormat': {
                          'bold': True,
                          'italic': True,
                        },
                      },
                    },
                    'fields': 'userEnteredFormat.textFormat',
                  }
                })

class TestIQBRIMSWorkflowUserSettings(OsfTestCase):

    @mock.patch.object(IQBRIMSClient, 'files')
    @mock.patch.object(IQBRIMSClient, 'create_spreadsheet')
    @mock.patch.object(SpreadsheetClient, 'sheets')
    @mock.patch.object(SpreadsheetClient, 'ensure_columns')
    @mock.patch.object(SpreadsheetClient, 'get_row_values')
    def test_load_flowable(self, mock_get_row_values, mock_ensure_columns,
                           mock_sheets, mock_create_spreadsheet, mock_files):
        mock_files.return_value = []
        mock_create_spreadsheet.return_value = {'id': 'test_spreadsheet'}
        gp = {'rowCount': 1}
        mock_sheets.return_value = [
          {'properties': {'title': settings.USER_SETTINGS_SHEET_SHEET_NAME,
                          'gridProperties': gp}}
        ]
        mock_ensure_columns.side_effect = lambda sid, cols: cols
        keys = ['FLOWABLE_USER', 'FLOWABLE_PASSWORD', 'FLOWABLE_HOST',
                'FLOWABLE_RESEARCH_APP_ID', 'FLOWABLE_SCAN_APP_ID']
        values = ['john', 'test', 'https://test.someuniv.ac.jp/test/',
                  'workflow123', 'workflow456']
        mock_get_row_values.side_effect = lambda sid, col, rcount: keys if col == 0 else values
        if 'loadedTime' in _user_settings_cache:
            del _user_settings_cache['loadedTime']

        client = IQBRIMSWorkflowUserSettings('0001', 'test_folder')
        assert_equal(client.LABO_LIST, settings.LABO_LIST)
        assert_equal(client.FLOWABLE_HOST, 'https://test.someuniv.ac.jp/test/')
        assert_equal(client.FLOWABLE_USER, 'john')
        assert_equal(client.FLOWABLE_PASSWORD, 'test')
        assert_equal(client.FLOWABLE_RESEARCH_APP_ID, 'workflow123')
        assert_equal(client.FLOWABLE_SCAN_APP_ID, 'workflow456')

        assert_equal(len(mock_sheets.mock_calls), 1)

    @mock.patch.object(IQBRIMSClient, 'files')
    @mock.patch.object(IQBRIMSClient, 'create_spreadsheet')
    @mock.patch.object(SpreadsheetClient, 'sheets')
    @mock.patch.object(SpreadsheetClient, 'ensure_columns')
    @mock.patch.object(SpreadsheetClient, 'get_row_values')
    def test_load_labo_list(self, mock_get_row_values, mock_ensure_columns,
                            mock_sheets, mock_create_spreadsheet, mock_files):
        mock_files.return_value = []
        mock_create_spreadsheet.return_value = {'id': 'test_spreadsheet'}
        gp = {'rowCount': 1}
        mock_sheets.return_value = [
          {'properties': {'title': settings.USER_SETTINGS_SHEET_SHEET_NAME,
                          'gridProperties': gp}}
        ]
        mock_ensure_columns.side_effect = lambda sid, cols: cols
        keys = ['LABO_LIST']
        values = ['[{"id": "xxx", "text": "XXX"}, {"id": "yyy", "text": "YYY"}]']
        mock_get_row_values.side_effect = lambda sid, col, rcount: keys if col == 0 else values
        if 'loadedTime' in _user_settings_cache:
            del _user_settings_cache['loadedTime']

        client = IQBRIMSWorkflowUserSettings('0001', 'test_folder')
        assert_equal(client.LABO_LIST, [{'id': 'xxx', 'text': 'XXX'}, {'id': 'yyy', 'text': 'YYY'}])
        assert_equal(client.FLOWABLE_HOST, settings.FLOWABLE_HOST)
        assert_equal(client.FLOWABLE_USER, settings.FLOWABLE_USER)
        assert_equal(client.FLOWABLE_PASSWORD, settings.FLOWABLE_PASSWORD)
        assert_equal(client.FLOWABLE_RESEARCH_APP_ID, settings.FLOWABLE_RESEARCH_APP_ID)
        assert_equal(client.FLOWABLE_SCAN_APP_ID, settings.FLOWABLE_SCAN_APP_ID)

        assert_equal(len(mock_sheets.mock_calls), 1)

    @mock.patch.object(IQBRIMSClient, 'files')
    @mock.patch.object(IQBRIMSClient, 'create_spreadsheet')
    @mock.patch.object(SpreadsheetClient, 'sheets')
    @mock.patch.object(SpreadsheetClient, 'ensure_columns')
    @mock.patch.object(SpreadsheetClient, 'get_row_values')
    def test_load_invalid_labo_list(self, mock_get_row_values, mock_ensure_columns,
                                    mock_sheets, mock_create_spreadsheet, mock_files):
        mock_files.return_value = []
        mock_create_spreadsheet.return_value = {'id': 'test_spreadsheet'}
        gp = {'rowCount': 1}
        mock_sheets.return_value = [
          {'properties': {'title': settings.USER_SETTINGS_SHEET_SHEET_NAME,
                          'gridProperties': gp}}
        ]
        mock_ensure_columns.side_effect = lambda sid, cols: cols
        keys = ['LABO_LIST']
        values = ['[{"id": "xxx", "tet": "XXX"}, {"id": "yyy", "text": "YYY"}]']
        mock_get_row_values.side_effect = lambda sid, col, rcount: keys if col == 0 else values
        if 'loadedTime' in _user_settings_cache:
            del _user_settings_cache['loadedTime']

        client = IQBRIMSWorkflowUserSettings('0001', 'test_folder')
        assert_equal(client.LABO_LIST, [{'text': u"No text: {'id': 'xxx', 'tet': 'XXX'}", 'id': 'error'}])

    @mock.patch.object(IQBRIMSClient, 'files')
    @mock.patch.object(IQBRIMSClient, 'create_spreadsheet')
    @mock.patch.object(SpreadsheetClient, 'sheets')
    @mock.patch.object(SpreadsheetClient, 'ensure_columns')
    @mock.patch.object(SpreadsheetClient, 'get_row_values')
    def test_load_messages(self, mock_get_row_values, mock_ensure_columns,
                            mock_sheets, mock_create_spreadsheet, mock_files):
        mock_files.return_value = []
        mock_create_spreadsheet.return_value = {'id': 'test_spreadsheet'}
        gp = {'rowCount': 1}
        mock_sheets.return_value = [
          {'properties': {'title': settings.USER_SETTINGS_SHEET_SHEET_NAME,
                          'gridProperties': gp}}
        ]
        mock_ensure_columns.side_effect = lambda sid, cols: cols
        keys = ['MESSAGES', 'MESSAGES.0']
        values = ['{"msg1": {"data": "MESSAGE1"}}', '{"msg2": {"data": "MESSAGE2"}}']
        mock_get_row_values.side_effect = lambda sid, col, rcount: keys if col == 0 else values
        if 'loadedTime' in _user_settings_cache:
            del _user_settings_cache['loadedTime']

        client = IQBRIMSWorkflowUserSettings('0001', 'test_folder')
        assert_equal(client.MESSAGES, {
            'msg1': {'data': 'MESSAGE1'},
            'msg2': {'data': 'MESSAGE2'},
        })
        assert_equal(client.FLOWABLE_HOST, settings.FLOWABLE_HOST)
        assert_equal(client.FLOWABLE_USER, settings.FLOWABLE_USER)
        assert_equal(client.FLOWABLE_PASSWORD, settings.FLOWABLE_PASSWORD)
        assert_equal(client.FLOWABLE_RESEARCH_APP_ID, settings.FLOWABLE_RESEARCH_APP_ID)
        assert_equal(client.FLOWABLE_SCAN_APP_ID, settings.FLOWABLE_SCAN_APP_ID)

        assert_equal(len(mock_sheets.mock_calls), 1)


class TestIQBRIMSFlowableClient(OsfTestCase):

    def test_start_workflow(self):
        client = IQBRIMSFlowableClient('0001')
        with mock.patch.object(client, '_make_request',
                               return_value=MockResponse('{"test": true}',
                                                         200)) as mkreq:
            status = {'state': 'deposit', 'labo_id': 'labox'}
            client.start_workflow('x1234', 'XPaper', status, 'key')

            name, args, kwargs = mkreq.mock_calls[0]
            vars = json.loads(kwargs['data'])['variables']
            assert_equal([v for v in vars if v['name'] == 'projectId'][0], {
              'name': 'projectId',
              'type': 'string',
              'value': 'x1234'
            })
            assert_equal([v for v in vars if v['name'] == 'paperFolderPattern'][0], {
              'name': 'paperFolderPattern',
              'type': 'string',
              'value': 'deposit/labox/%-x1234/'
            })

    def test_start_check_workflow(self):
        client = IQBRIMSFlowableClient('test_app')
        with mock.patch.object(client, '_make_request',
                               return_value=MockResponse('{"test": true}',
                                                         200)) as mkreq:
            status = {'state': 'check',
                      'labo_id': 'rna'}
            client.start_workflow('abc01', 'Sample Test', status, 'hash123')
            name, args, kwargs = mkreq.mock_calls[0]
            #
            print(json.loads(kwargs['data']))
            assert_equal(json.loads(kwargs['data']), {
              u'variables': [{u'type': u'string',
                              u'name': u'projectId',
                              u'value': u'abc01'},
                             {u'type': u'string',
                              u'name': u'paperTitle',
                              u'value': u'Sample Test'},
                             {u'type': u'string',
                              u'name': u'paperFolderPattern',
                              u'value': u'check/rna/%-abc01/'},
                             {u'type': u'string',
                              u'name': u'laboName',
                              u'value': u'RNA分野'},
                             {u'type': u'string',
                              u'name': u'laboNameEN',
                              u'value': u'Laboratory of RNA'},
                             {u'type': u'boolean',
                              u'name': u'isDirectlySubmitData',
                              u'value': False},
                             {u'type': u'string',
                              u'name': u'acceptedDate',
                              u'value': u''},
                             {u'type': u'string',
                              u'name': u'acceptedDateTime',
                              u'value': u''},
                             {u'type': u'boolean',
                              u'name': u'hasPaper',
                              u'value': True},
                             {u'type': u'boolean',
                              u'name': u'hasRaw',
                              u'value': True},
                             {u'type': u'boolean',
                              u'name': u'hasChecklist',
                              u'value': True},
                             {u'name': u'inputOverview',
                              u'type': u'string',
                              u'value': u''},
                             {u'type': u'string',
                              u'name': u'flowableWorkflowUrl',
                              u'value': u'http://localhost:9999/flowable-task/'},
                             {u'type': u'string',
                              u'name': u'secret',
                              u'value': u'hash123'}],
              u'processDefinitionId': u'test_app'
            })
            assert_equal(client._auth,
                         (settings.FLOWABLE_USER, settings.FLOWABLE_PASSWORD))

    def test_start_deposit_workflow(self):
        client = IQBRIMSFlowableClient('test_app')
        with mock.patch.object(client, '_make_request',
                               return_value=MockResponse('{"test": true}',
                                                         200)) as mkreq:
            status = {'state': 'deposit',
                      'labo_id': 'rna',
                      'accepted_date': '2019-08-29T15:00:00.000Z',
                      'is_directly_submit_data': True}
            client.start_workflow('abc01', 'Sample Paper', status, 'hash123')
            name, args, kwargs = mkreq.mock_calls[0]
            print(json.loads(kwargs['data']))
            assert_equal(json.loads(kwargs['data']), {
              'variables': [{'type': 'string',
                             'name': 'projectId',
                             'value': 'abc01'},
                            {'type': 'string',
                             'name': 'paperTitle',
                             'value': 'Sample Paper'},
                            {u'type': u'string',
                             u'name': u'paperFolderPattern',
                             u'value': u'deposit/rna/%-abc01/'},
                            {'type': 'string',
                             'name': 'laboName',
                             'value': u'RNA分野'},
                            {'type': 'string',
                             'name': 'laboNameEN',
                             'value': u'Laboratory of RNA'},
                            {'type': 'boolean',
                             'name': 'isDirectlySubmitData',
                             'value': True},
                            {'type': 'string',
                             'name': 'acceptedDate',
                             'value': '2019-08-29'},
                            {'type': 'string',
                             'name': 'acceptedDateTime',
                             'value': '2019-08-29T15:00:00.000Z'},
                            {u'type': u'boolean',
                             u'name': u'hasPaper',
                             u'value': True},
                            {u'type': u'boolean',
                             u'name': u'hasRaw',
                             u'value': True},
                            {u'type': u'boolean',
                             u'name': u'hasChecklist',
                             u'value': True},
                            {u'name': u'inputOverview',
                             u'type': u'string',
                             u'value': u''},
                            {'type': 'string',
                             'name': 'flowableWorkflowUrl',
                             'value': u'http://localhost:9999/flowable-task/'},
                            {'type': 'string',
                             'name': 'secret',
                             'value': 'hash123'}],
              'processDefinitionId': 'test_app'
            })

    def test_start_deposit_overview_workflow(self):
        client = IQBRIMSFlowableClient('test_app')
        with mock.patch.object(client, '_make_request',
                               return_value=MockResponse('{"test": true}',
                                                         200)) as mkreq:
            status = {'state': 'deposit',
                      'labo_id': 'rna',
                      'accepted_date': '2019-08-29T15:00:00.000Z',
                      'is_directly_submit_data': True,
                      'input_overview': u'[{"header": "John", "value": "Doe"}]'}
            client.start_workflow('abc01', 'Sample Paper', status, 'hash123')
            name, args, kwargs = mkreq.mock_calls[0]
            print(json.loads(kwargs['data']))
            assert_equal(json.loads(kwargs['data']), {
              'variables': [{'type': 'string',
                             'name': 'projectId',
                             'value': 'abc01'},
                            {'type': 'string',
                             'name': 'paperTitle',
                             'value': 'Sample Paper'},
                            {u'type': u'string',
                             u'name': u'paperFolderPattern',
                             u'value': u'deposit/rna/%-abc01/'},
                            {'type': 'string',
                             'name': 'laboName',
                             'value': u'RNA分野'},
                            {'type': 'string',
                             'name': 'laboNameEN',
                             'value': u'Laboratory of RNA'},
                            {'type': 'boolean',
                             'name': 'isDirectlySubmitData',
                             'value': True},
                            {'type': 'string',
                             'name': 'acceptedDate',
                             'value': '2019-08-29'},
                            {'type': 'string',
                             'name': 'acceptedDateTime',
                             'value': '2019-08-29T15:00:00.000Z'},
                            {u'type': u'boolean',
                             u'name': u'hasPaper',
                             u'value': True},
                            {u'type': u'boolean',
                             u'name': u'hasRaw',
                             u'value': True},
                            {u'type': u'boolean',
                             u'name': u'hasChecklist',
                             u'value': True},
                            {u'name': u'inputOverview',
                             u'type': u'string',
                             u'value': u'[{"header": "John", "value": "Doe"}]'},
                            {'type': 'string',
                             'name': 'flowableWorkflowUrl',
                             'value': u'http://localhost:9999/flowable-task/'},
                            {'type': 'string',
                             'name': 'secret',
                             'value': 'hash123'}],
              'processDefinitionId': 'test_app'
            })

    def test_start_deposit_paper_workflow(self):
        client = IQBRIMSFlowableClient('test_app')
        with mock.patch.object(client, '_make_request',
                               return_value=MockResponse('{"test": true}',
                                                         200)) as mkreq:
            status = {'state': 'deposit',
                      'labo_id': 'rna',
                      'accepted_date': '2019-08-29T15:00:00.000Z',
                      'is_directly_submit_data': True,
                      'has_paper': True,
                      'has_raw': False,
                      'has_checklist': False}
            client.start_workflow('abc01', 'Sample Paper', status, 'hash123')
            name, args, kwargs = mkreq.mock_calls[0]
            print(json.loads(kwargs['data']))
            assert_equal(json.loads(kwargs['data']), {
              'variables': [{'type': 'string',
                             'name': 'projectId',
                             'value': 'abc01'},
                            {'type': 'string',
                             'name': 'paperTitle',
                             'value': 'Sample Paper'},
                            {u'type': u'string',
                             u'name': u'paperFolderPattern',
                             u'value': u'deposit/rna/%-abc01/'},
                            {'type': 'string',
                             'name': 'laboName',
                             'value': u'RNA分野'},
                            {'type': 'string',
                             'name': 'laboNameEN',
                             'value': u'Laboratory of RNA'},
                            {'type': 'boolean',
                             'name': 'isDirectlySubmitData',
                             'value': True},
                            {'type': 'string',
                             'name': 'acceptedDate',
                             'value': '2019-08-29'},
                            {'type': 'string',
                             'name': 'acceptedDateTime',
                             'value': '2019-08-29T15:00:00.000Z'},
                            {u'type': u'boolean',
                             u'name': u'hasPaper',
                             u'value': True},
                            {u'type': u'boolean',
                             u'name': u'hasRaw',
                             u'value': False},
                            {u'type': u'boolean',
                             u'name': u'hasChecklist',
                             u'value': False},
                            {u'name': u'inputOverview',
                             u'type': u'string',
                             u'value': u''},
                            {'type': 'string',
                             'name': 'flowableWorkflowUrl',
                             'value': u'http://localhost:9999/flowable-task/'},
                            {'type': 'string',
                             'name': 'secret',
                             'value': 'hash123'}],
              'processDefinitionId': 'test_app'
            })

    def test_start_deposit_raw_workflow(self):
        client = IQBRIMSFlowableClient('test_app')
        with mock.patch.object(client, '_make_request',
                               return_value=MockResponse('{"test": true}',
                                                         200)) as mkreq:
            status = {'state': 'deposit',
                      'labo_id': 'rna',
                      'accepted_date': '2019-08-29T15:00:00.000Z',
                      'is_directly_submit_data': True,
                      'has_paper': False,
                      'has_raw': True,
                      'has_checklist': False}
            client.start_workflow('abc01', 'Sample Paper', status, 'hash123')
            name, args, kwargs = mkreq.mock_calls[0]
            print(json.loads(kwargs['data']))
            assert_equal(json.loads(kwargs['data']), {
              'variables': [{'type': 'string',
                             'name': 'projectId',
                             'value': 'abc01'},
                            {'type': 'string',
                             'name': 'paperTitle',
                             'value': 'Sample Paper'},
                            {u'type': u'string',
                             u'name': u'paperFolderPattern',
                             u'value': u'deposit/rna/%-abc01/'},
                            {'type': 'string',
                             'name': 'laboName',
                             'value': u'RNA分野'},
                            {'type': 'string',
                             'name': 'laboNameEN',
                             'value': u'Laboratory of RNA'},
                            {'type': 'boolean',
                             'name': 'isDirectlySubmitData',
                             'value': True},
                            {'type': 'string',
                             'name': 'acceptedDate',
                             'value': '2019-08-29'},
                            {'type': 'string',
                             'name': 'acceptedDateTime',
                             'value': '2019-08-29T15:00:00.000Z'},
                            {u'type': u'boolean',
                             u'name': u'hasPaper',
                             u'value': False},
                            {u'type': u'boolean',
                             u'name': u'hasRaw',
                             u'value': True},
                            {u'type': u'boolean',
                             u'name': u'hasChecklist',
                             u'value': False},
                            {u'name': u'inputOverview',
                             u'type': u'string',
                             u'value': u''},
                            {'type': 'string',
                             'name': 'flowableWorkflowUrl',
                             'value': u'http://localhost:9999/flowable-task/'},
                            {'type': 'string',
                             'name': 'secret',
                             'value': 'hash123'}],
              'processDefinitionId': 'test_app'
            })

    def test_start_deposit_checklist_workflow(self):
        client = IQBRIMSFlowableClient('test_app')
        with mock.patch.object(client, '_make_request',
                               return_value=MockResponse('{"test": true}',
                                                         200)) as mkreq:
            status = {'state': 'deposit',
                      'labo_id': 'rna',
                      'accepted_date': '2019-08-29T15:00:00.000Z',
                      'is_directly_submit_data': True,
                      'has_paper': False,
                      'has_raw': False,
                      'has_checklist': True}
            client.start_workflow('abc01', 'Sample Paper', status, 'hash123')
            name, args, kwargs = mkreq.mock_calls[0]
            print(json.loads(kwargs['data']))
            assert_equal(json.loads(kwargs['data']), {
              'variables': [{'type': 'string',
                             'name': 'projectId',
                             'value': 'abc01'},
                            {'type': 'string',
                             'name': 'paperTitle',
                             'value': 'Sample Paper'},
                            {u'type': u'string',
                             u'name': u'paperFolderPattern',
                             u'value': u'deposit/rna/%-abc01/'},
                            {'type': 'string',
                             'name': 'laboName',
                             'value': u'RNA分野'},
                            {'type': 'string',
                             'name': 'laboNameEN',
                             'value': u'Laboratory of RNA'},
                            {'type': 'boolean',
                             'name': 'isDirectlySubmitData',
                             'value': True},
                            {'type': 'string',
                             'name': 'acceptedDate',
                             'value': '2019-08-29'},
                            {'type': 'string',
                             'name': 'acceptedDateTime',
                             'value': '2019-08-29T15:00:00.000Z'},
                            {u'type': u'boolean',
                             u'name': u'hasPaper',
                             u'value': False},
                            {u'type': u'boolean',
                             u'name': u'hasRaw',
                             u'value': False},
                            {u'type': u'boolean',
                             u'name': u'hasChecklist',
                             u'value': True},
                            {u'name': u'inputOverview',
                             u'type': u'string',
                             u'value': u''},
                            {'type': 'string',
                             'name': 'flowableWorkflowUrl',
                             'value': u'http://localhost:9999/flowable-task/'},
                            {'type': 'string',
                             'name': 'secret',
                             'value': 'hash123'}],
              'processDefinitionId': 'test_app'
            })
