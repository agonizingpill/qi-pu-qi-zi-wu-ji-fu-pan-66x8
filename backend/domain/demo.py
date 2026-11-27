from domain.matches_model import matches
from domain.plies_model import plies
from domain.referee_flags_model import referee_flags
from domain.errata_model import errata

FIXTURES = [
    (matches, [{'code': 'G-41', 'white': '澄泉', 'black': '青石', 'round_no': 4, 'open': True},
               {'code': 'G-42', 'white': '松风', 'black': '砚池', 'round_no': 5, 'open': True}]),
    (plies, [{'code': 'MV-31',
  'game': 'G-41',
  'number': 31,
  'gap': 8,
  'capture_claim': 2,
  'replayed': 0,
  'repeat_move': True,
  'witness': False,
  'adjudicated': False},
 {'code': 'MV-41',
  'game': 'G-42',
  'number': 24,
  'gap': 16,
  'capture_claim': 4,
  'replayed': 0,
  'repeat_move': False,
  'witness': False,
  'adjudicated': False}]),
    (referee_flags, [{'code': 'FLAG-00',
  'ply': 'MV-31',
  'reason': '原件人工复盘',
  'holdout': 0,
  'token': 'initial'}]),
    (errata, [{'code': 'ER-14', 'flag': 'FLAG-00', 'official': 2, 'corrigendum': '历史只读样条'}]),
]
