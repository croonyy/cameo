import random
from collections import OrderedDict

udstrip = lambda x: (
    "\n".join(x.split("\n")[1:])
    if x.split("\n")[0].strip() == ""
    else "\n".join(x.split("\n")[0:])
).rstrip("\n")

rainbow_colors = OrderedDict(
    {
        "红": (255, 0, 0),
        "橙": (255, 125, 0),
        "黄": (255, 255, 0),
        "绿": (0, 255, 0),
        "青": (0, 255, 255),
        "蓝": (0, 0, 255),
        "紫": (255, 0, 255),
    }
)


def rgb_f(text, rgb=(0, 255, 0)):
    return "\033[38;2;{};{};{}m{text}\033[0m".format(text=text, *rgb)


def cprint(text, colors=None, order=False):
    if colors:
        d = OrderedDict(colors)
        dlen = len(d)
        cl = list(d.values())
        if order:
            for line in text.split("\n"):
                line_mod = []
                for i, c in enumerate(line):
                    line_mod.append(rgb_f(c, cl[i % dlen]))
                print("".join(line_mod))
        else:
            for line in text.split("\n"):
                line_mod = []
                for i, c in enumerate(line):
                    line_mod.append(rgb_f(c, random.choice(cl)))
                print("".join(line_mod))
    else:
        for line in text.split("\n"):
            line_mod = []
            for i, c in enumerate(line):
                line_mod.append(rgb_f(c, tuple(random.randint(0, 255) for _ in range(3))))
            print("".join(line_mod))
        


if __name__ == "__main__":
    # print("".join([rgb_f("#", rgb) for color, rgb in rainbow_colors.items()]))

    # colors = [31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47]
    # print("".join([f"\033[{color}m#\033[0m" for color in colors]))
    cprint("测试文本")