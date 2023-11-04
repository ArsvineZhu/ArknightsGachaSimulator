#! python3.12

"""
Arknights Gacha Simulator
明日方舟抽卡模拟

可自己定义卡池, 概率等. 目前已经优化了一部分, 效率有所提升, 应该没有有BUG, 一经发现会后续修改.
You can customize your own Gacha box, probability, etc.
At present, some of the optimizations have been made,
the efficiency has been improved, there should be no bugs,
and it will be modified once found.
"""

from random import random
from typing import Any
from json import loads


class StarRank:
    """
    星级数据结构

    [("Texas the Omertosa", 0.02, ("RETRO", "LIMITED", "WANTED")), ...]
      名称                   概率  备注 (ROUTINE, UP, LIMITED, RETRO, WANTED)

    WANTED, LIMITED, UP, RETRO 标签可以定义获取提示
    """

    def __init__(self, box: list[tuple[str, float, tuple[str]]]) -> None:
        self.box = box


class Simulator:
    """抽卡模拟器 | Gacha simulaor"""

    def __init__(self, path: str) -> None:
        self.box = self.load_box(path)  # 加载卡池

        self.uprate = 0.02  # 一定抽数后的概率提升数值
        self.guarant = 50  # 此抽数后会概率提升

        self.ranks = {i: StarRank(self.analyze(
            self.box[f"{i}"])) for i in range(6, 2, -1)}
        """各星级的卡池数据(只读)"""

        self.rates = {6: self.box["6"]["rate"],
                      5: self.box["5"]["rate"],
                      4: self.box["4"]["rate"],
                      3: self.box["3"]["rate"]
                      }
        """各星级的概率(只读)"""

        # 各星级的概率(可变)
        self.six_rate = self.rates[6]
        self.five_rate = self.rates[5]
        self.four_rate = self.rates[4]
        self.three_rate = self.rates[3]

        # 快速访问缓存
        self.cache = {
            "up": len(self.box["6"]["up"]),
            "retro": len(self.box["6"]["retro"]),
            "routine": len(self.box["6"]["box"]),
            "rate": self.box["6"]["up_rate"],
            "radio": self.box["6"]["retro_radio"]
        }

        # 初始计算各级概率
        for i in range(3, 6 + 1):
            self.ranks[i] = self.calc(i, self.ranks[i])

        class Results:
            """统计数据接口 | Statistics interface"""

            total: int = 0  # 总抽数
            distance: int = 0  # 六星距离 (多少抽没出六星, 距离上一个六星的抽数)
            operators: list = []  # 抽中的干员名称
            star: list = []  # 对应星级
            stats: dict[int, int] = {3: 0, 4: 0, 5: 0, 6: 0}  # 个数统计

        self.results = Results()  # 创建统计数据

    def load_box(self, path: str) -> dict:
        """从路径加载 JSON 数据 | Load JSON data from the path

        Parameters
        ----------
        path
            路径 | Path

        Returns
        -------
            卡池信息字典 | Dictionary of Gacha box information
        """

        res = {}
        with open(path, encoding="utf-8") as f:
            res = loads(f.read())
        return res

    def analyze(self, rank: dict[str, Any]) -> list:
        """分析 JSON 数据 | Analyze JSON data"""

        ret = []
        # 获取每个星级的基本卡池数据
        for name in rank["box"]:
            ret.append((name, 0, ("ROUTINE", )))

        # 6, 5 星会有概率 UP
        if 'up' in list(rank.keys()):
            for item in rank["up"]:
                ret.append(
                    (list(item.keys())[0], 0, ("UP", *tuple(list(item.values())[0]))))

        if 'retro' in list(rank.keys()):
            for item in rank["retro"]:
                ret.append(
                    (list(item.keys())[0], 0, ("RETRO", *tuple(list(item.values())[0]))))

        return ret

    def calc(self, rank: int, starRank: StarRank) -> StarRank:
        """
        计算对应星级的概率 | Calculate the probability of the corresponding star rank

        Parameters
        ----------
        rank
            星级 | Star rank
        starRank
            星级数据结构 | Star rank data structure

        Returns
        -------
            星级数据结构 | Star rank data structure

        Raises
        ------
        Exception
            未定义的星级 | Undefined star rank
        """

        ret = StarRank(starRank.box)
        rate = 0  # 概率
        length = ret.box.__len__()

        # 生成元组模板, 传入概率
        def temp(_rate): return (ret.box[i][0], _rate, ret.box[i][2])

        match rank:  # 匹配星级
            case 3 | 4:
                # 载入概率
                if rank == 3:
                    rate = self.three_rate
                else:
                    rate = self.four_rate

                for i in range(length):
                    # 3, 4 星没有 UP, 概率均分
                    ret.box[i] = temp(rate / length)

            case 5:
                rate = self.five_rate  # 载入概率

                if self.box["5"]["up"]:
                    num = self.box["5"]["up"].__len__()  # up 的个数
                    # 存在概率 up
                    for i in range(length):
                        if "UP" in ret.box[i][2]:  # 是 up 对象
                            ret.box[i] = temp(
                                rate * self.box["5"]["up_rate"] / num)
                        else:
                            ret.box[i] = temp(
                                rate / length * self.box["5"]["up_rate"])
                else:
                    for i in range(length):
                        ret.box[i] = temp(rate / length)

            case 6:
                _cache = self.cache  # 避免频繁类内属性访问
                rate = self.six_rate
                up_rate = rate * _cache["rate"]
                other_rate = rate * (1 - _cache["rate"])
                num = _cache["routine"] + \
                    _cache["radio"] * _cache["retro"]

                for i in range(length):
                    if "ROUTINE" in ret.box[i][2]:
                        ret.box[i] = temp(other_rate / num)  # 加权以外的概率
                    elif "UP" in ret.box[i][2]:
                        ret.box[i] = temp(
                            up_rate / _cache["up"])  # 概率提升的对象概率
                    elif "RETRO" in ret.box[i][2]:
                        ret.box[i] = temp(_cache["radio"]
                                          * other_rate / num)  # 复刻对象概率

            case _:
                raise Exception(f"Undefined star rank: {rank}.")

        return ret

    def gacha(self) -> str:
        """
        进行一次单抽 | Perform one Gacha

        Returns
        -------
            一个干员名称 | A operator name
        """

        _results = self.results  # 避免频繁类内属性访问
        _ranks = self.ranks  # 避免频繁类内属性访问
        _results.total += 1  # 抽取次数加一
        operators = []  # 临时星级记录
        star = {}  # 临时星级记录
        rates = []  # 临时概率记录
        optr = ""  # 抽取结果

        for j in range(3, 6 + 1):
            for i in sorted(_ranks[j].box, key=lambda _: _[1], reverse=True):
                # 以概率由小到大排序, 并记录卡池信息
                operators.append(i[0])
                rates.append(i[1])
                star[i[0]] = j

        _sum = sum(rates)  # 临时概率求和
        v = random()  # 获取随机值
        while 1:
            if v <= _sum:  # 未超出精度范围, 否则重新抽取
                break
            v = random()

        _sum = 0  # 临时概率求和清零
        for _ in range(operators.__len__()):  # 便利所有干员
            _sum += rates[_]  # 累加概率
            if v <= _sum:  # 寻找抽中的对象
                optr = operators[_]  # 记录名称, 并更新统计数据
                _results.operators.append(operators[_])
                _results.star.append((operators[_], star[operators[_]]))
                _results.stats[star[operators[_]]] += 1

                _rates = self.rates  # 避免频繁类内属性访问
                if star[operators[_]] == 6:  # 抽中 6 星
                    _results.distance = 0  # 重置 6 星距离, 恢复所有概率
                    self.six_rate = _rates[6]
                    self.five_rate = _rates[5]
                    self.four_rate = _rates[4]
                    self.three_rate = _rates[3]
                    for _ in range(3, 6 + 1):  # 重新计算概率
                        _ranks[_] = self.calc(_, _ranks[_])
                else:
                    _results.distance += 1  # 未抽中 6 星, 6 星距离加一
                    if _results.distance > self.guarant:  # 大于保底线
                        self.six_rate += self.uprate  # 概率提升
                        factor = (1 - self.six_rate) / \
                            (1 - _rates[6])  # 其他星级概率降低因子
                        self.five_rate = factor * _rates[5]
                        self.four_rate = factor * _rates[4]
                        self.three_rate = factor * _rates[3]
                        for _ in range(3, 6 + 1):  # 重新计算概率
                            _ranks[_] = self.calc(_, _ranks[_])
                break  # 抽中后立刻终止
        return optr

    def gacha10(self) -> list[str]:
        """
        进行一次十连抽 | Perform 10 Gachas

        Returns
        -------
            干员名称的列表 | A list of operator names
        """

        return [self.gacha() for _ in range(10)]
