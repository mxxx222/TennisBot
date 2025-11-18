"""
Feature Transformation Module
Additional transformation utilities
"""

from math_utils import clip_value, sigmoid

alias DType = DType.float64

fn log_transform(data: Tensor[DType]) -> Tensor[DType]:
    """Log transformation for skewed features"""
    var result = Tensor[DType](data.shape())
    for i in range(data.num_elements()):
        let val = data[data.get_flat_index(i)]
        result[result.get_flat_index(i)] = log(val + 1.0)  # Add 1 to avoid log(0)
    return result


fn scale_to_range(data: Tensor[DType], min_val: Float64, max_val: Float64) -> Tensor[DType]:
    """Scale tensor values to specified range"""
    var current_min: Float64 = data[0]
    var current_max: Float64 = data[0]
    
    # Find current min/max
    for i in range(data.num_elements()):
        let val = data[data.get_flat_index(i)]
        if val < current_min:
            current_min = val
        if val > current_max:
            current_max = val
    
    var result = Tensor[DType](data.shape())
    let range_diff = current_max - current_min
    let target_range = max_val - min_val
    
    if range_diff > 0.0001:
        for i in range(data.num_elements()):
            let normalized = (data[data.get_flat_index(i)] - current_min) / range_diff
            result[result.get_flat_index(i)] = min_val + normalized * target_range
    else:
        # All values are the same
        for i in range(data.num_elements()):
            result[result.get_flat_index(i)] = (min_val + max_val) / 2.0
    
    return result

