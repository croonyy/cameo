from datetime import datetime
from functools import wraps

# 装饰器，计时函数执行时间。
def timer(func):
    """
    decorator for get the execute_time of a func
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        time_a = datetime.now()
        result = func(*args, **kwargs)
        time_b = datetime.now()
        print('start time:' + time_a.strftime('%Y-%m-%d %H:%M:%S.%f'))
        print('end   time:' + time_b.strftime('%Y-%m-%d %H:%M:%S.%f'))
        info = ''
        if args:
            info = info + str(args)
        if kwargs:
            info = info + str(kwargs)
        if info:
            if len(info) < 100:
                # print(f'Execute time:{(time_b - time_a).total_seconds():0.4f}s.func[{func.__name__}({info})]')
                print(
                    f'Execute time:{(time_b - time_a).total_seconds()}s.func[{func.__name__}({info})]')
            else:
                print(
                    f'Execute time:{(time_b - time_a).total_seconds()}s.func[{func.__name__}({info[0:100]})]')
        else:
            print(
                f'Execute time:{(time_b - time_a).total_seconds()}s.func[{func.__name__}()]')
        return result

    return wrapper