# compare_performance.py
import time
from py_impl.python_sum import py_sum
from compiled.modules.subf.math_ops import cy_sum # type: ignore
 
def test_performance(n):
    """测试并比较两种实现的性能"""
    print(f"\n测试规模: n = {n:,}")
    
    # 测试Python实现
    start = time.time()
    py_result = py_sum(n)
    py_time = time.time() - start
    
    # 测试Cython实现
    start = time.time()
    cy_result = cy_sum(n)
    cy_time = time.time() - start
    print(f"Python实现结果: {py_result:,}")
    print(f"Cython实现结果: {cy_result:,}")
    print(f"Python耗时: {py_time:.9f}秒")
    print(f"Cython耗时: {cy_time:.9f}秒")

    times = f"{py_time/cy_time:.3f}" if cy_time>0 else 'N/A'
    # 比较结果
    print("="*80)
    print(f"Cython比Python快: {times}倍")
    
    # # 验证结果是否一致
    # assert py_result == cy_result, "两种实现结果不一致!"
 
if __name__ == "__main__":
    # 小规模测试
    # test_performance(1_000_000)
    
    # # 大规模测试
    test_performance(10_000_000)