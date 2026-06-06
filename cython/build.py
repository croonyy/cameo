import os
from setuptools import setup, Extension
import shutil
from Cython.Build import cythonize
import re

working_dir = os.getcwd()
script_dir = os.path.dirname(__file__)


os.makedirs(os.path.join(script_dir, "compiled"), exist_ok=True)


def find_pyx_files(root_dir, mpatterns):
    """递归查找所有 .pyx 文件，返回 (模块名, 文件路径) 的列表"""
    pyx_files = []
    root_dir = os.path.abspath(root_dir)  # 转为绝对路径
    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".pyx"):
                # 计算模块名（替换路径分隔符为 .，并去掉 .pyx 后缀）
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, start=script_dir)  # 相对路径
                module_name = os.path.splitext(rel_path)[0].replace(
                    os.sep, "."
                )  # 转为模块名
                matchs = [re.fullmatch(p, module_name) for p in mpatterns]
                if any(matchs):
                    pyx_files.append((module_name, full_path))
    return pyx_files


def build(mpatterns):
    # # 删除脚本目录下的compiled目录，重新编译
    # compiled_dir = os.path.join(script_dir, "compiled")
    # if os.path.exists(compiled_dir):
    #     shutil.rmtree(compiled_dir)
    # 1. 查找所有匹配的 .pyx 文件
    pyx_files = find_pyx_files(os.path.join(script_dir, "modules"), mpatterns)

    # 2. 动态生成 Extension 列表
    extensions = [
        Extension(
            name=module_name,
            sources=[pyx_path],
            extra_compile_args=[],  # 可选编译优化
        )
        for module_name, pyx_path in pyx_files
    ]

    # 3. 编译
    setup(
        ext_modules=cythonize(
            extensions,
            # build_dir 只能指定c 文件位置。不能指定build文件夹位置
            build_dir=os.path.relpath(
                os.path.join(script_dir, "compiled/c_code"), working_dir
            ),
            language_level=3,
        ),
        script_args=[
            "build_ext",
            # 这个参数会吧pyd文件放在当前命令执行的目录下
            # "--inplace",
            # .pyd(windows)或.so(linux)文件输出到 compiled 目录
            f"--build-lib={os.path.join(script_dir, 'compiled')}",
            "--quiet",
        ],
        zip_safe=False,
    )
    # 编译后删除工作目录的 build 目录（编译的临时文件家，有些.exp|.lib|.obj文件），
    build_dir = os.path.join(working_dir, "build")
    if os.path.exists(build_dir):
        shutil.rmtree(build_dir)


if __name__ == "__main__":
    paterns = [
        r"^modules\.subf.*",
        # r"^modules\..*",
    ]
    build(paterns)
    print(f"✅ Cython 模块编译完成！输出目录: {os.path.join(script_dir, 'compiled')}")
