from functools import wraps
from datetime import datetime


def rgb_f(text, rgb=(0, 255, 0)):
    return "\033[38;2;{};{};{}m{text}\033[0m".format(text=text, *rgb)


def gap(a, b):
    gap = (b - a).total_seconds()
    # color =(0, 255, 180) if gap>0.021 else (0, 255, 255)
    color = (0, 255, 255)
    return rgb_f(f"[time:{gap:,.6f}s]", color)


# 装饰器，计时函数执行时间。
def timer(func):
    """
    decorator for get the execute_time of a func
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        tmp = locals()
        vars = {i: tmp[i] for i in ["args", "kwargs"]}
        time_a = datetime.now()
        result = func(*args, **kwargs)
        time_b = datetime.now()
        # print('start time:' + time_a.strftime('%Y-%m-%d %H:%M:%S.%f'))
        # print('end   time:' + time_b.strftime('%Y-%m-%d %H:%M:%S.%f'))
        info = str(vars)
        if info:
            p_len = 500
            if len(info) < p_len:
                print(f"{gap(time_a,time_b)} func[{func.__name__}({info})]")
            else:
                print(f"{gap(time_a,time_b)} func[{func.__name__}({info[0:p_len]}...)]")
        else:
            print(f"{gap(time_a,time_b)} func[{func.__name__}()]")
        return result

    return wrapper


@timer
def test(a, b, c=1):
    args = locals()
    print(args)
    return a + b


if __name__ == "__main__":
    test(1, 2, c=3)
