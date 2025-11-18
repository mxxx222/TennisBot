"""
Core Tensor Operations for Mojo Performance Layer
High-performance tensor manipulation functions
"""

from python import Python
from python.object import PythonObject

alias DType = DType.float64

fn tensor_mean(data: Tensor[DType]) -> Float64:
    """Calculate mean of tensor"""
    var sum: Float64 = 0.0
    var count = data.num_elements()
    for i in range(count):
        sum += data[data.get_flat_index(i)]
    return sum / count


fn tensor_std(data: Tensor[DType]) -> Float64:
    """Calculate standard deviation of tensor"""
    let mean_val = tensor_mean(data)
    var sum_sq_diff: Float64 = 0.0
    var count = data.num_elements()
    
    for i in range(count):
        let diff = data[data.get_flat_index(i)] - mean_val
        sum_sq_diff += diff * diff
    
    return (sum_sq_diff / count) ** 0.5


fn tensor_sum(data: Tensor[DType]) -> Float64:
    """Calculate sum of tensor"""
    var sum: Float64 = 0.0
    for i in range(data.num_elements()):
        sum += data[data.get_flat_index(i)]
    return sum


fn tensor_multiply(a: Tensor[DType], b: Tensor[DType]) -> Tensor[DType]:
    """Element-wise multiplication of two tensors"""
    var result = Tensor[DType](a.shape())
    for i in range(a.num_elements()):
        result[result.get_flat_index(i)] = a[a.get_flat_index(i)] * b[b.get_flat_index(i)]
    return result


fn tensor_add(a: Tensor[DType], b: Tensor[DType]) -> Tensor[DType]:
    """Element-wise addition of two tensors"""
    var result = Tensor[DType](a.shape())
    for i in range(a.num_elements()):
        result[result.get_flat_index(i)] = a[a.get_flat_index(i)] + b[b.get_flat_index(i)]
    return result


fn normalize_tensor(data: Tensor[DType], mean: Float64, std: Float64) -> Tensor[DType]:
    """Normalize tensor using mean and std"""
    var result = Tensor[DType](data.shape())
    for i in range(data.num_elements()):
        if std > 0.0:
            result[result.get_flat_index(i)] = (data[data.get_flat_index(i)] - mean) / std
        else:
            result[result.get_flat_index(i)] = data[data.get_flat_index(i)]
    return result

