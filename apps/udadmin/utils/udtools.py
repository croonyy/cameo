import re


def font(text=None, color=None, size=None, face=None):
    color = f"color={color} " if color else ""
    size = f"size={size} " if size else ""
    face = f'face="{face}" ' if face else ""
    return f"<font {color}{size}{face}>{text}</font>"


def camel_to_snake_case(camel_str):
    """
    将CamelCase字符串转换为snake_case字符串。

    :param camel_str: CamelCase格式的字符串
    :return: 转换为snake_case格式的字符串
    """
    # 使用正则表达式查找所有大写字母前不是下划线或大写字母的位置，并在那里插入下划线
    s1 = re.sub("([A-Z]+)", r"_\1", camel_str)
    # 将字符串转换为小写并去掉开头的下划线（如果有的话）
    return s1.lower().lstrip("_")
