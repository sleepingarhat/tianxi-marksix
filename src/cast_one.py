# -*- coding: utf-8 -*-
"""單盤：python src/cast_one.py 1988 2 8 4"""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from yongshen_c import yongshen_c

def main():
    if len(sys.argv) < 4:
        print("用法: python src/cast_one.py YYYY M D [hour]")
        sys.exit(1)
    y, m, d = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
    h = int(sys.argv[4]) if len(sys.argv) > 4 else 21
    print(json.dumps(yongshen_c(y, m, d, h), ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
