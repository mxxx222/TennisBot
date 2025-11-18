"""
ML Inference Module for Mojo Performance Layer
High-performance batch prediction and ensemble aggregation
"""

from python import Python
from python.object import PythonObject
from tensor_ops import tensor_sum, tensor_multiply, tensor_add
from math_utils import sigmoid, softmax, weighted_sum

alias DType = DType.float64

fn batch_predict(
    features: Tensor[DType],
    model_weights: Tensor[DType],
    predictions_list: List[Tensor[DType]],
) -> Tensor[DType]:
    """
    High-performance batch prediction with weighted ensemble
    
    Args:
        features: Input feature tensor (batch_size x num_features)
        model_weights: Weights for each model in ensemble
        predictions_list: List of prediction tensors from different models
    
    Returns:
        Ensemble predictions tensor
    """
    var batch_size = features.shape()[0]
    var num_models = len(predictions_list)
    var result = Tensor[DType](shape=(batch_size,))
    
    # Weighted ensemble aggregation
    for batch_idx in range(batch_size):
        var ensemble_prob: Float64 = 0.0
        
        for model_idx in range(num_models):
            let pred_prob = predictions_list[model_idx][batch_idx]
            let weight = model_weights[model_idx] if model_idx < model_weights.num_elements() else 1.0 / num_models
            ensemble_prob += pred_prob * weight
        
        result[batch_idx] = clip_value(ensemble_prob, 0.0, 1.0)
    
    return result


fn ensemble_aggregate(
    predictions: List[Tensor[DType]],
    weights: Tensor[DType],
) -> Tensor[DType]:
    """
    Aggregate multiple model predictions using weighted voting
    
    Args:
        predictions: List of prediction probability tensors
        weights: Weights for each model
    
    Returns:
        Aggregated ensemble predictions
    """
    var num_models = len(predictions)
    if num_models == 0:
        raise Error("No predictions provided")
    
    var batch_size = predictions[0].shape()[0]
    var result = Tensor[DType](shape=(batch_size,))
    
    for batch_idx in range(batch_size):
        var weighted_sum: Float64 = 0.0
        var total_weight: Float64 = 0.0
        
        for model_idx in range(num_models):
            let pred = predictions[model_idx][batch_idx]
            let weight = weights[model_idx] if model_idx < weights.num_elements() else 1.0 / num_models
            weighted_sum += pred * weight
            total_weight += weight
        
        result[batch_idx] = weighted_sum / total_weight if total_weight > 0.0 else 0.0
    
    return result


fn feature_transform(
    features: Tensor[DType],
    mean: Tensor[DType],
    std: Tensor[DType],
) -> Tensor[DType]:
    """
    Normalize features using pre-computed mean and std
    
    Args:
        features: Input features (batch_size x num_features)
        mean: Mean values for each feature
        std: Std values for each feature
    
    Returns:
        Normalized features tensor
    """
    var batch_size = features.shape()[0]
    var num_features = features.shape()[1]
    var result = Tensor[DType](shape=(batch_size, num_features))
    
    for batch_idx in range(batch_size):
        for feat_idx in range(num_features):
            let val = features[batch_idx, feat_idx]
            let feat_mean = mean[feat_idx] if feat_idx < mean.num_elements() else 0.0
            let feat_std = std[feat_idx] if feat_idx < std.num_elements() else 1.0
            
            if feat_std > 0.0:
                result[batch_idx, feat_idx] = (val - feat_mean) / feat_std
            else:
                result[batch_idx, feat_idx] = val
    
    return result

