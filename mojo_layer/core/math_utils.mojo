"""
Math Utilities for Mojo Performance Layer
Core mathematical operations optimized for performance
"""

fn clip_value(value: Float64, min_val: Float64, max_val: Float64) -> Float64:
    """Clip value between min and max"""
    if value < min_val:
        return min_val
    elif value > max_val:
        return max_val
    return value


fn sigmoid(x: Float64) -> Float64:
    """Sigmoid activation function"""
    if x < -500.0:
        return 0.0
    elif x > 500.0:
        return 1.0
    return 1.0 / (1.0 + exp(-x))


fn softmax(values: Tensor[DType.float64]) -> Tensor[DType.float64]:
    """Softmax normalization"""
    var result = Tensor[DType.float64](values.shape())
    var max_val: Float64 = values[0]
    
    # Find max for numerical stability
    for i in range(values.num_elements()):
        if values[values.get_flat_index(i)] > max_val:
            max_val = values[values.get_flat_index(i)]
    
    var sum_exp: Float64 = 0.0
    for i in range(values.num_elements()):
        let exp_val = exp(values[values.get_flat_index(i)] - max_val)
        result[result.get_flat_index(i)] = exp_val
        sum_exp += exp_val
    
    # Normalize
    for i in range(values.num_elements()):
        result[result.get_flat_index(i)] = result[result.get_flat_index(i)] / sum_exp
    
    return result


fn weighted_sum(values: Tensor[DType.float64], weights: Tensor[DType.float64]) -> Float64:
    """Calculate weighted sum"""
    var sum: Float64 = 0.0
    for i in range(values.num_elements()):
        sum += values[values.get_flat_index(i)] * weights[weights.get_flat_index(i)]
    return sum

