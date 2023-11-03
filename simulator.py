#! python3.12
from random import random
from dataclasses import dataclass
# from typing import ...
import json
import pprint as pp


@dataclass
class StarRank:
    """
    星级数据结构
    [("Texas the Omertosa", 0.02, ("RETRO", "LIMITED", "WANTED")), ...]
      名称     概率   备注(ROUTINE, UP, LIMITED, RETRO, WANTED)
    """
    box: list[tuple[str, float, tuple[str]]]


class Simulator:
    """模拟器"""

    def __init__(self, path: str) -> None:
        self.path = path
        self.box = self.load_box(path)

        self.uprate = 0.02

        self.ranks = {i: StarRank(self.analyze(
            self.box[f"{i}"])) for i in range(6, 2, -1)}

        self.rates = {6: self.box["6"]["rate"],
                      5: self.box["5"]["rate"],
                      4: self.box["4"]["rate"],
                      3: self.box["3"]["rate"]
                      }

        self.six_rate = self.rates[6]
        self.five_rate = self.rates[5]
        self.four_rate = self.rates[4]
        self.three_rate = self.rates[3]

        self.cache = {
            "up": len(self.box["6"]["up"]),
            "retro": len(self.box["6"]["retro"]),
            "routine": len(self.box["6"]["box"]),
            "rate": self.box["6"]["up_rate"],
            "radio": self.box["6"]["retro_radio"]
        }

        for i in range(3, 6 + 1):
            self.ranks[i] = self.calc(i, self.ranks[i])

        @dataclass
        class Results:
            total = 0
            distance = 0
            operators = []
            star = []

        self.results = Results()

    def load_box(self, path: str) -> dict:
        """从路径加载 JSON 数据"""

        res = {}
        with open(path, encoding="utf-8") as f:
            res = json.loads(f.read())
        return res

    def analyze(self, rank: dict) -> list:
        """分析 JSON 数据"""

        ret = []
        for name in rank["box"]:
            ret.append((name, 0, ("ROUTINE", )))

        if 'up' in list(rank.keys()):
            for item in rank["up"]:
                name = list(item.keys())[0]
                tags = list(item.values())[0]
                ret.append((name, 0, ("UP", *tuple(tags))))

        if 'retro' in list(rank.keys()):
            for item in rank["retro"]:
                name = list(item.keys())[0]
                tags = list(item.values())[0]
                ret.append((name, 0, ("RETRO", *tuple(tags))))

        return ret

    def calc(self, rank: int, starRank: StarRank) -> StarRank:
        """计算对应星级的概率"""

        ret = StarRank(starRank.box)
        rate = 0  # 概率
        length = ret.box.__len__()

        match rank:  # 匹配星级
            case 3 | 4:
                if rank == 3:
                    rate = self.three_rate
                else:
                    rate = self.four_rate
                for i in range(length):
                    ret.box[i] = (ret.box[i][0], rate / length, ret.box[i][2])

            case 5:
                rate = self.five_rate
                if self.box["5"]["up"]:
                    num = self.box["5"]["up"].__len__()  # up 的个数
                    # 存在概率 up
                    for i in range(length):
                        if "UP" in ret.box[i][2]:  # up 对象
                            ret.box[i] = (
                                ret.box[i][0], rate * self.box["5"]["up_rate"] / num, ret.box[i][2])
                        else:
                            ret.box[i] = (
                                ret.box[i][0], rate / length * self.box["5"]["up_rate"], ret.box[i][2])
                else:
                    for i in range(length):
                        ret.box[i] = (ret.box[i][0], rate /
                                      length, ret.box[i][2])

            case 6:
                rate = self.six_rate
                up_rate = rate * self.cache["rate"]
                other_rate = rate * (1 - self.cache["rate"])

                up_rate_each = up_rate / self.cache["up"]  # 概率提升的对象概率
                num = self.cache["routine"] + \
                    self.cache["radio"] * self.cache["retro"]
                retro_rate = self.cache["radio"] * other_rate / num  # 复刻对象概率
                other_rate_each = other_rate / num  # 加权以外的概率

                for i in range(length):
                    if "ROUTINE" in ret.box[i][2]:
                        ret.box[i] = (
                            ret.box[i][0], other_rate_each, ret.box[i][2])
                    elif "UP" in ret.box[i][2]:
                        ret.box[i] = (
                            ret.box[i][0], up_rate_each, ret.box[i][2])
                    elif "RETRO" in ret.box[i][2]:
                        ret.box[i] = (ret.box[i][0], retro_rate, ret.box[i][2])

            case _:
                raise Exception(f"Undefined star rank {rank}.")

        return ret

    def gacha(self):
        # print(f"{self.six_rate}$", end="")
        self.results.total += 1
        operators = []
        star = {}
        rates = []

        for j in range(3, 6 + 1):
            for i in sorted(self.ranks[j].box, key=lambda t: t[1], reverse=True):
                operators.append(i[0])
                rates.append(i[1])
                star[i[0]] = j

        v = random()
        # print(round(sum(rates), 3), end=" $ ")
        if v > sum(rates):
            self.gacha()
            return
        for i in range(operators.__len__()):
            if v <= sum(rates[:i]):
                print(operators[i])
                self.results.operators.append(operators[i])
                self.results.star.append((operators[i], star[operators[i]]))
                if star[operators[i]] == 6:
                    self.results.distance = 0
                    self.six_rate = self.rates[6]
                    self.five_rate = self.rates[5]
                    self.four_rate = self.rates[4]
                    self.three_rate = self.rates[3]
                    for i in range(3, 6 + 1):
                        self.ranks[i] = self.calc(i, self.ranks[i])
                else:
                    self.results.distance += 1
                    if self.results.distance > 50:
                        self.six_rate += self.uprate
                        factor = (1 - self.six_rate) / (1 - self.rates[6])
                        self.five_rate = factor * self.rates[5]
                        self.four_rate = factor * self.rates[4]
                        self.three_rate = factor * self.rates[3]
                        for i in range(3, 6 + 1):
                            self.ranks[i] = self.calc(i, self.ranks[i])
                break


    def gacha10(self):
        for i in range(10):
            self.gacha()


def main() -> None:
    print("Simulation start...\n")
    s = Simulator("box.json")
    for i in range(200):
        print(i + 1, end=": ")
        s.gacha()
    # pp.pprint(s.results.operators)
    # print(len(s.results.star))
    print("\nSimulation accomplished")


if __name__ == "__main__":
    main()
