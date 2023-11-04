#! python12

"""对模拟器进行一系列演示"""

from simulator import Simulator
from time import time
try:
    from tqdm import trange
except:
    from sys import exit
    input("[!] 必要的进度条模块 tqdm 未安装!")
    exit()


def main() -> None:
    print("[*] 模拟开始\n")

    path = "box.json"

    # -----

    print("[1] 尝试从 %s 加载卡池数据..." % path)
    s = Simulator(path)
    _r = s.results
    print("[1] 完成\n")

    # -----

    print("[2] 模拟 20 次单抽...")
    for i in range(20):
        print(f" - {i + 1}: {s.gacha()}")
    print("[2] 完成\n")

    # -----

    print("[3] 模拟 8 次十连抽...")
    for i in range(8):
        print(f" - {i + 1}: {s.gacha10()}")
    print("[3] 完成\n")

    # -----

    print("[4] 输出 8 次十连抽以及 20 次单抽, 共计 100 抽的统计数据...")
    print(f""" - 统计数据:
        三星个数: {_r.stats[3]}
        四星个数: {_r.stats[4]}
        五星个数: {_r.stats[5]}
        六星个数: {_r.stats[6]}
        六星距离: {_r.distance}
        总抽数: {_r.total}""")
    print("[4] 完成\n")

    # -----

    print("[5] 模拟 49900 抽, 并输出测试数据, 请耐心等待...")

    dt = time()
    for i in trange(49900):
        s.gacha()
    dt = time() - dt

    print(f" - 49900 抽共用时 {round(1000 * dt, 1)} 毫秒\n")

    print(f""" - 统计数据:
        三星个数: {_r.stats[3]} ({round(100 * _r.stats[3] / _r.total, 2)}%)
        四星个数: {_r.stats[4]} ({round(100 * _r.stats[4] / _r.total, 2)}%)
        五星个数: {_r.stats[5]} ({round(100 * _r.stats[5] / _r.total, 2)}%)
        六星个数: {_r.stats[6]} ({round(100 * _r.stats[6] / _r.total, 2)}%)
        六星距离: {_r.distance}
        总抽数: {_r.total}""")
    print("[5] 完成\n")

    # -----

    print("处理六星干员统计数据...\n")
    optrs = {}
    for i in range(len(_r.operators)):
        if _r.star[i][1] == 6:
            optrs.setdefault(_r.operators[i], 0)
            optrs[_r.operators[i]] += 1

    _sorted = sorted(optrs, key=lambda _: optrs[_], reverse=True)
    for i in _sorted:
        print(f"{i}: {optrs[i]}  ({round(100 * optrs[i] / _r.stats[6], 2)}%)")

    # -----

    print("\n[*] 模拟完成")


if __name__ == "__main__":
    main()
