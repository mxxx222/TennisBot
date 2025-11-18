"""
Ensemble Aggregation Module
Weighted voting and ensemble combination strategies
"""

from math_utils import weighted_sum, softmax

alias DType = DType.float64

fn weighted_voting(
    predictions: List[Tensor[DType]],
    weights: Tensor[DType],
) -> Tensor[DType]:
    """Weighted voting ensemble method"""
    return ensemble_aggregate(predictions, weights)


fn majority_voting(
    predictions: List[Tensor[DType]],
) -> Tensor[DType]:
    """Majority voting ensemble method"""
    var num_models = len(predictions)
    var batch_size = predictions[0].shape()[0]
    var result = Tensor[DType](shape=(batch_size,))
    
    for batch_idx in range(batch_size):
        var sum_prob: Float64 = 0.0
        for model_idx in range(num_models):
            sum_prob += predictions[model_idx][batch_idx]
        result[batch_idx] = sum_prob / num_models
    
    return result

