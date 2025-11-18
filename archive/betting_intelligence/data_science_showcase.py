#!/usr/bin/env python3
"""
DATA SCIENCE SHOWCASE - Advanced Analytics & Pattern Recognition
===============================================================

Educational implementation of advanced data science techniques for pattern
recognition, machine learning, and statistical modeling using educational datasets.

⚠️  EDUCATIONAL PURPOSES ONLY - NO REAL MONEY
⚠️  This showcase demonstrates advanced analytics concepts, ML techniques,
    and statistical modeling for educational purposes only.

Author: Betfury.io Educational Research System
License: Educational Use Only
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import json
from datetime import datetime, timedelta
import logging
import warnings
warnings.filterwarnings('ignore')

# Advanced analytics libraries
from sklearn.model_selection import train_test_split, cross_val_score, TimeSeriesSplit
from sklearn.preprocessing import StandardScaler, MinMaxScaler, LabelEncoder
from sklearn.decomposition import PCA, FastICA
from sklearn.cluster import DBSCAN, AgglomerativeClustering
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.svm import SVC, OneClassSVM
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
from sklearn.feature_selection import SelectKBest, f_classif, mutual_info_classif
import matplotlib.pyplot as plt
import seaborn as sns

logger = logging.getLogger(__name__)


class PatternType(Enum):
    """Educational pattern types for recognition"""
    TRENDING = "trending"
    MEAN_REVERTING = "mean_reverting"
    CYCLIC = "cyclic"
    SEASONAL = "seasonal"
    BREAKOUT = "breakout"
    ANOMALY = "anomaly"
    CLUSTERED = "clustered"
    UNKNOWN = "unknown"


class ModelType(Enum):
    """Educational ML model types"""
    SUPERVISED = "supervised"
    UNSUPERVISED = "unsupervised"
    SEMI_SUPERVISED = "semi_supervised"
    REINFORCEMENT = "reinforcement"
    DEEP_LEARNING = "deep_learning"
    ENSEMBLE = "ensemble"


@dataclass
class EducationalFeature:
    """Educational feature for machine learning"""
    name: str
    feature_type: str  # numeric, categorical, datetime, text
    importance: float
    description: str
    transformation: Optional[str] = None


@dataclass
class ModelPerformance:
    """Educational model performance metrics"""
    model_name: str
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    auc_score: float
    training_time: float
    feature_importance: Dict[str, float]
    confusion_matrix: np.ndarray
    educational_notes: List[str]


class FeatureEngineering:
    """Educational feature engineering for pattern recognition"""
    
    def __init__(self):
        """Initialize feature engineering toolkit"""
        self.feature_importances = {}
    
    def create_lag_features(self, 
                          data: pd.Series, 
                          lag_periods: List[int] = [1, 2, 3, 5, 10]) -> pd.DataFrame:
        """Create lag features for time series"""
        
        features = pd.DataFrame()
        features['original'] = data
        
        for lag in lag_periods:
            features[f'lag_{lag}'] = data.shift(lag)
            features[f'return_lag_{lag}'] = data.pct_change(lag)
        
        return features
    
    def create_rolling_features(self, 
                              data: pd.Series, 
                              windows: List[int] = [5, 10, 20, 50]) -> pd.DataFrame:
        """Create rolling window features"""
        
        features = pd.DataFrame()
        features['original'] = data
        
        for window in windows:
            features[f'ma_{window}'] = data.rolling(window).mean()
            features[f'std_{window}'] = data.rolling(window).std()
            features[f'min_{window}'] = data.rolling(window).min()
            features[f'max_{window}'] = data.rolling(window).max()
            features[f'skew_{window}'] = data.rolling(window).skew()
            features[f'kurt_{window}'] = data.rolling(window).kurt()
        
        return features
    
    def create_technical_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Create educational technical analysis features"""
        
        if 'price' not in data.columns:
            data['price'] = data.get('close', data.iloc[:, 0])
        
        features = data.copy()
        
        # Price-based features
        features['price_change'] = features['price'].pct_change()
        features['price_volatility'] = features['price_change'].rolling(20).std()
        features['price_momentum'] = features['price'].rolling(10).mean() / features['price'].rolling(20).mean() - 1
        
        # Volume-based features
        if 'volume' in features.columns:
            features['volume_ma'] = features['volume'].rolling(20).mean()
            features['volume_ratio'] = features['volume'] / features['volume_ma']
            features['volume_volatility'] = features['volume'].rolling(10).std()
        
        # Range-based features
        if all(col in features.columns for col in ['high', 'low', 'close']):
            features['daily_range'] = (features['high'] - features['low']) / features['close']
            features['upper_shadow'] = (features['high'] - np.maximum(features['open'], features['close'])) / features['close']
            features['lower_shadow'] = (np.minimum(features['open'], features['close']) - features['low']) / features['close']
            features['body_size'] = np.abs(features['close'] - features['open']) / features['close']
        
        # Time-based features
        if 'timestamp' in features.columns:
            features['timestamp'] = pd.to_datetime(features['timestamp'])
            features['hour'] = features['timestamp'].dt.hour
            features['day_of_week'] = features['timestamp'].dt.dayofweek
            features['month'] = features['timestamp'].dt.month
        
        return features
    
    def create_interaction_features(self, features: pd.DataFrame) -> pd.DataFrame:
        """Create interaction features between variables"""
        
        # Select numeric columns
        numeric_cols = features.select_dtypes(include=[np.number]).columns
        
        if len(numeric_cols) < 2:
            return features
        
        # Create top 10 interaction features
        interaction_features = pd.DataFrame()
        
        for i, col1 in enumerate(numeric_cols[:5]):  # Limit to prevent explosion
            for j, col2 in enumerate(numeric_cols[1:6]):
                if i < j:
                    interaction_features[f'{col1}_x_{col2}'] = features[col1] * features[col2]
                    interaction_features[f'{col1}_div_{col2}'] = features[col1] / (features[col2] + 1e-8)
        
        # Concatenate with original features
        combined = pd.concat([features, interaction_features], axis=1)
        
        return combined


class PatternRecognition:
    """Educational pattern recognition system"""
    
    def __init__(self):
        """Initialize pattern recognition engine"""
        self.patterns_detected = []
    
    def detect_trends(self, data: pd.Series, window: int = 20) -> Dict[str, Any]:
        """Detect trend patterns in educational data"""
        
        # Calculate trend strength using linear regression slope
        x = np.arange(len(data))
        slope, intercept = np.polyfit(x, data, 1)
        
        # Trend direction and strength
        trend_strength = abs(slope) / np.std(data)
        trend_direction = "up" if slope > 0 else "down" if slope < 0 else "sideways"
        
        # Statistical significance (simplified)
        correlation = np.corrcoef(x, data)[0, 1]
        
        # Moving average comparisons
        ma_short = data.rolling(window//2).mean()
        ma_long = data.rolling(window).mean()
        
        trend_signals = 0
        if not ma_short.isna().iloc[-1]:
            if ma_short.iloc[-1] > ma_long.iloc[-1]:
                trend_signals += 1
            if slope > 0:
                trend_signals += 1
            if correlation > 0.3:
                trend_signals += 1
        
        trend_score = trend_signals / 3 if trend_signals > 0 else 0
        
        return {
            'pattern_type': PatternType.TRENDING.value,
            'trend_direction': trend_direction,
            'trend_strength': trend_strength,
            'slope': slope,
            'correlation': correlation,
            'trend_score': trend_score,
            'statistical_significance': abs(correlation) > 0.3
        }
    
    def detect_mean_reversion(self, data: pd.Series, window: int = 20) -> Dict[str, Any]:
        """Detect mean reversion patterns"""
        
        # Calculate Z-score (standardized distance from mean)
        rolling_mean = data.rolling(window).mean()
        rolling_std = data.rolling(window).std()
        z_score = (data - rolling_mean) / rolling_std
        
        # Mean reversion metrics
        current_z_score = z_score.iloc[-1] if not z_score.isna().iloc[-1] else 0
        extreme_z_scores = (np.abs(z_score) > 2).sum()
        reversion_speed = np.abs(z_score.diff()).mean()
        
        # Mean reversion tendency
        oversold = current_z_score < -1.5
        overbought = current_z_score > 1.5
        
        # Calculate half-life of mean reversion
        prices = data.dropna().values
        if len(prices) > window:
            mean_price = np.mean(prices)
            deviations = np.abs(prices - mean_price)
            
            # Simple half-life estimation
            half_life = None
            for i in range(window, len(deviations)):
                if deviations[i] < deviations[window] / 2:
                    half_life = i - window
                    break
            
            if half_life is None:
                half_life = len(deviations) - window
        else:
            half_life = window
        
        mean_reversion_score = min(1.0, extreme_z_scores / len(data) * 10)
        
        return {
            'pattern_type': PatternType.MEAN_REVERTING.value,
            'current_z_score': current_z_score,
            'extreme_values_count': extreme_z_scores,
            'reversion_speed': reversion_speed,
            'half_life': half_life,
            'oversold_condition': oversold,
            'overbought_condition': overbought,
            'mean_reversion_score': mean_reversion_score
        }
    
    def detect_cyclical_patterns(self, data: pd.Series, min_period: int = 5) -> Dict[str, Any]:
        """Detect cyclical patterns using Fourier analysis"""
        
        # Simplified cyclical detection using autocorrelation
        autocorr = []
        max_lag = min(len(data) // 4, 50)
        
        for lag in range(min_period, max_lag):
            if len(data) > lag:
                correlation = np.corrcoef(data[:-lag], data[lag:])[0, 1]
                if not np.isnan(correlation):
                    autocorr.append((lag, correlation))
        
        # Find strongest cyclical component
        if autocorr:
            strongest_cycle = max(autocorr, key=lambda x: abs(x[1]))
            cycle_period, cycle_strength = strongest_cycle
            
            # Classify cycle strength
            if abs(cycle_strength) > 0.7:
                cycle_strength_label = "strong"
            elif abs(cycle_strength) > 0.4:
                cycle_strength_label = "moderate"
            else:
                cycle_strength_label = "weak"
        else:
            cycle_period = 0
            cycle_strength = 0
            cycle_strength_label = "none"
        
        return {
            'pattern_type': PatternType.CYCLIC.value,
            'cycle_period': cycle_period,
            'cycle_strength': cycle_strength,
            'cycle_strength_label': cycle_strength_label,
            'significant_cycles': len([x for x in autocorr if abs(x[1]) > 0.3]),
            'autocorrelation_peaks': autocorr[:5]  # Top 5 peaks
        }
    
    def detect_anomalies(self, data: pd.Series, contamination: float = 0.1) -> Dict[str, Any]:
        """Detect anomalous patterns using statistical methods"""
        
        # Z-score based anomaly detection
        mean_val = data.mean()
        std_val = data.std()
        z_scores = np.abs((data - mean_val) / std_val)
        
        # IQR based anomaly detection
        Q1 = data.quantile(0.25)
        Q3 = data.quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        # Anomaly flags
        z_score_anomalies = z_scores > 3
        iqr_anomalies = (data < lower_bound) | (data > upper_bound)
        
        # Isolation Forest (simplified version)
        isolation_scores = np.random.uniform(0, 1, len(data))  # Simplified for education
        
        # Combine anomaly detection methods
        anomaly_votes = z_score_anomalies.astype(int) + iqr_anomalies.astype(int)
        consensus_anomalies = anomaly_votes >= 1
        
        # Anomaly characteristics
        anomaly_indices = np.where(consensus_anomalies)[0]
        anomaly_values = data.iloc[anomaly_indices] if len(anomaly_indices) > 0 else pd.Series()
        
        return {
            'pattern_type': PatternType.ANOMALY.value,
            'total_anomalies': consensus_anomalies.sum(),
            'anomaly_rate': consensus_anomalies.mean(),
            'z_score_anomalies': z_score_anomalies.sum(),
            'iqr_anomalies': iqr_anomalies.sum(),
            'anomaly_indices': anomaly_indices.tolist(),
            'anomaly_values': anomaly_values.tolist() if len(anomaly_values) > 0 else [],
            'anomaly_magnitude': np.abs(z_scores[consensus_anomalies]).mean() if consensus_anomalies.sum() > 0 else 0
        }


class TimeSeriesAnalyzer:
    """Educational time series analysis and forecasting"""
    
    def __init__(self):
        """Initialize time series analyzer"""
        self.seasonality_detected = False
        self.trend_components = {}
    
    def decompose_time_series(self, data: pd.Series) -> Dict[str, Any]:
        """Educational time series decomposition"""
        
        # Simple additive decomposition (educational approximation)
        
        # Trend component (moving average)
        trend_window = max(7, len(data) // 10)
        trend = data.rolling(window=trend_window, center=True).mean()
        
        # Detrended data
        detrended = data - trend
        
        # Seasonal component (simplified)
        # Group by time period and calculate average
        seasonal = pd.Series(index=data.index, dtype=float)
        
        if hasattr(data.index, 'dayofweek'):
            # Weekly seasonality
            seasonal_avg = detrended.groupby(data.index.dayofweek).mean()
            for day in seasonal_avg.index:
                seasonal[data.index.dayofweek == day] = seasonal_avg[day]
        else:
            # Simple periodic seasonality
            period = max(5, len(data) // 20)
            for i in range(len(data)):
                seasonal.iloc[i] = detrended.iloc[i % period] if i % period < len(detrended) else 0
        
        # Residual component
        residual = data - trend - seasonal
        
        # Component analysis
        trend_strength = 1 - (residual.var() / data.var())
        seasonal_strength = 1 - ((data - trend - residual).var() / data.var())
        
        return {
            'original': data,
            'trend': trend,
            'seasonal': seasonal,
            'residual': residual,
            'trend_strength': trend_strength,
            'seasonal_strength': seasonal_strength,
            'decomposition_quality': min(trend_strength, seasonal_strength)
        }
    
    def detect_seasonality(self, data: pd.Series, periods: List[int] = [7, 30, 365]) -> Dict[str, Any]:
        """Detect seasonal patterns in educational data"""
        
        seasonality_results = {}
        
        for period in periods:
            if len(data) < period * 2:  # Need at least 2 complete cycles
                continue
            
            # Calculate seasonal component using simpler approach
            seasonal_data = pd.Series(index=data.index, dtype=float, data=0.0)
            
            # Calculate seasonal pattern by grouping values
            for i in range(period):
                # Get values at this position in the cycle
                cycle_values = data.iloc[i::period]
                if len(cycle_values) > 0:
                    seasonal_avg = cycle_values.mean()
                    # Assign to all positions in this cycle
                    data_positions = data.index[i::period]
                    for idx in data_positions:
                        seasonal_data.loc[idx] = seasonal_avg
            
            # Calculate seasonal strength
            seasonal_variance = seasonal_data.var()
            total_variance = data.var()
            seasonal_strength = seasonal_variance / total_variance if total_variance > 0 else 0
            
            # Significance test (simplified)
            autocorr_lag = period
            if len(data) > autocorr_lag:
                correlation = np.corrcoef(data[:-autocorr_lag], data[autocorr_lag:])[0, 1]
                significance = abs(correlation) > 0.3
            else:
                significance = False
            
            seasonality_results[f'period_{period}'] = {
                'seasonal_strength': seasonal_strength,
                'is_significant': significance,
                'seasonal_component': seasonal_data,
                'correlation': correlation if 'correlation' in locals() else 0
            }
        
        # Overall seasonality assessment
        max_strength = max([result['seasonal_strength'] for result in seasonality_results.values()]) if seasonality_results else 0
        significant_periods = [period for period, result in seasonality_results.items() if result['is_significant']]
        
        return {
            'has_seasonality': max_strength > 0.1,
            'dominant_period': max_strength,
            'significant_periods': significant_periods,
            'seasonality_details': seasonality_results
        }
    
    def forecast_with_ml(self, data: pd.Series, forecast_horizon: int = 10) -> Dict[str, Any]:
        """Educational time series forecasting using ML"""
        
        if len(data) < 20:
            return {'error': 'Insufficient data for ML forecasting'}
        
        # Prepare features
        feature_engineering = FeatureEngineering()
        
        # Create lag features
        lag_features = feature_engineering.create_lag_features(data, [1, 2, 3, 5, 10])
        
        # Create rolling features  
        rolling_features = feature_engineering.create_rolling_features(data, [5, 10, 20])
        
        # Combine features
        features_df = pd.concat([lag_features, rolling_features], axis=1)
        
        # Create target (future value)
        target = data.shift(-1)  # Next value as target
        
        # Remove NaN values
        valid_indices = ~(features_df.isna().any(axis=1) | target.isna())
        X = features_df[valid_indices]
        y = target[valid_indices]
        
        if len(X) < 10:
            return {'error': 'Insufficient valid data for modeling'}
        
        # Split data (time series aware)
        split_point = int(len(X) * 0.8)
        X_train, X_test = X[:split_point], X[split_point:]
        y_train, y_test = y[:split_point], y[split_point:]
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Train simple regression model
        from sklearn.ensemble import RandomForestRegressor
        from sklearn.linear_model import LinearRegression
        
        models = {
            'RandomForest': RandomForestRegressor(n_estimators=50, random_state=42),
            'LinearRegression': LinearRegression()
        }
        
        results = {}
        
        for model_name, model in models.items():
            try:
                # Train model
                model.fit(X_train_scaled, y_train)
                
                # Make predictions
                y_pred_train = model.predict(X_train_scaled)
                y_pred_test = model.predict(X_test_scaled)
                
                # Calculate metrics
                from sklearn.metrics import mean_absolute_error, mean_squared_error
                
                train_mae = mean_absolute_error(y_train, y_pred_train)
                test_mae = mean_absolute_error(y_test, y_pred_test)
                train_rmse = np.sqrt(mean_squared_error(y_train, y_pred_train))
                test_rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))
                
                # Feature importance (if available)
                feature_importance = {}
                if hasattr(model, 'feature_importances_'):
                    for i, feature in enumerate(X.columns):
                        feature_importance[feature] = model.feature_importances_[i]
                
                results[model_name] = {
                    'train_mae': train_mae,
                    'test_mae': test_mae,
                    'train_rmse': train_rmse,
                    'test_rmse': test_rmse,
                    'feature_importance': feature_importance,
                    'model': model
                }
                
            except Exception as e:
                results[model_name] = {'error': str(e)}
        
        # Select best model based on test MAE
        best_model_name = min([name for name, result in results.items() if 'error' not in result], 
                            key=lambda name: results[name]['test_mae'], 
                            default=None)
        
        if best_model_name:
            best_result = results[best_model_name]
            
            # Generate forecast
            last_features = X.iloc[-1:].values
            last_features_scaled = scaler.transform(last_features)
            
            forecast = best_result['model'].predict(last_features_scaled)[0]
            
            return {
                'forecast': forecast,
                'best_model': best_model_name,
                'forecast_accuracy': {
                    'test_mae': best_result['test_mae'],
                    'test_rmse': best_result['test_rmse']
                },
                'all_models': results,
                'feature_importance': best_result['feature_importance']
            }
        else:
            return {'error': 'No valid models could be trained'}


class ClusterAnalysis:
    """Educational cluster analysis for pattern discovery"""
    
    def __init__(self):
        """Initialize cluster analysis"""
        self.cluster_results = {}
    
    def kmeans_clustering(self, 
                         data: np.ndarray, 
                         n_clusters: int = 3, 
                         random_state: int = 42) -> Dict[str, Any]:
        """Perform K-means clustering"""
        
        from sklearn.cluster import KMeans
        
        # Apply K-means
        kmeans = KMeans(n_clusters=n_clusters, random_state=random_state)
        cluster_labels = kmeans.fit_predict(data)
        
        # Calculate cluster characteristics
        cluster_centers = kmeans.cluster_centers_
        inertia = kmeans.inertia_
        
        # Analyze each cluster
        cluster_analysis = {}
        for i in range(n_clusters):
            cluster_points = data[cluster_labels == i]
            
            cluster_analysis[f'cluster_{i}'] = {
                'size': len(cluster_points),
                'percentage': len(cluster_points) / len(data) * 100,
                'center': cluster_centers[i].tolist(),
                'std_deviation': np.std(cluster_points, axis=0).tolist(),
                'characteristics': self._analyze_cluster_characteristics(cluster_points, data)
            }
        
        # Calculate silhouette score
        from sklearn.metrics import silhouette_score
        silhouette_avg = silhouette_score(data, cluster_labels)
        
        return {
            'algorithm': 'K-Means',
            'n_clusters': n_clusters,
            'cluster_labels': cluster_labels.tolist(),
            'cluster_centers': cluster_centers.tolist(),
            'inertia': inertia,
            'silhouette_score': silhouette_avg,
            'cluster_analysis': cluster_analysis
        }
    
    def dbscan_clustering(self, 
                         data: np.ndarray, 
                         eps: float = 0.5, 
                         min_samples: int = 5) -> Dict[str, Any]:
        """Perform DBSCAN clustering"""
        
        from sklearn.cluster import DBSCAN
        
        # Apply DBSCAN
        dbscan = DBSCAN(eps=eps, min_samples=min_samples)
        cluster_labels = dbscan.fit_predict(data)
        
        # Analyze clusters
        n_clusters = len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)
        n_noise = list(cluster_labels).count(-1)
        
        cluster_analysis = {}
        
        # Analyze each cluster
        unique_labels = set(cluster_labels)
        for label in unique_labels:
            if label == -1:
                continue  # Skip noise points
            
            cluster_points = data[cluster_labels == label]
            
            cluster_analysis[f'cluster_{label}'] = {
                'size': len(cluster_points),
                'percentage': len(cluster_points) / len(data) * 100,
                'center': np.mean(cluster_points, axis=0).tolist(),
                'characteristics': self._analyze_cluster_characteristics(cluster_points, data)
            }
        
        return {
            'algorithm': 'DBSCAN',
            'n_clusters': n_clusters,
            'n_noise_points': n_noise,
            'cluster_labels': cluster_labels.tolist(),
            'cluster_analysis': cluster_analysis,
            'noise_percentage': n_noise / len(data) * 100
        }
    
    def hierarchical_clustering(self, 
                              data: np.ndarray, 
                              n_clusters: int = 3) -> Dict[str, Any]:
        """Perform hierarchical clustering"""
        
        from sklearn.cluster import AgglomerativeClustering
        
        # Apply hierarchical clustering
        hierarchical = AgglomerativeClustering(n_clusters=n_clusters)
        cluster_labels = hierarchical.fit_predict(data)
        
        # Calculate linkage matrix (simplified)
        from scipy.cluster.hierarchy import dendrogram, linkage
        try:
            linkage_matrix = linkage(data, method='ward')
            hierarchical_info = 'Linkage matrix calculated successfully'
        except:
            linkage_matrix = None
            hierarchical_info = 'Linkage matrix calculation failed'
        
        # Analyze clusters
        cluster_analysis = {}
        for i in range(n_clusters):
            cluster_points = data[cluster_labels == i]
            
            cluster_analysis[f'cluster_{i}'] = {
                'size': len(cluster_points),
                'percentage': len(cluster_points) / len(data) * 100,
                'center': np.mean(cluster_points, axis=0).tolist(),
                'characteristics': self._analyze_cluster_characteristics(cluster_points, data)
            }
        
        return {
            'algorithm': 'Hierarchical',
            'n_clusters': n_clusters,
            'cluster_labels': cluster_labels.tolist(),
            'cluster_analysis': cluster_analysis,
            'linkage_info': hierarchical_info
        }
    
    def _analyze_cluster_characteristics(self, 
                                       cluster_points: np.ndarray, 
                                       full_data: np.ndarray) -> Dict[str, Any]:
        """Analyze characteristics of a cluster"""
        
        cluster_mean = np.mean(cluster_points, axis=0)
        full_data_mean = np.mean(full_data, axis=0)
        
        # Find distinguishing features
        differences = np.abs(cluster_mean - full_data_mean)
        top_distinguishing_features = np.argsort(differences)[-3:]  # Top 3
        
        return {
            'mean_values': cluster_mean.tolist(),
            'std_deviation': np.std(cluster_points, axis=0).tolist(),
            'distinguishing_features': top_distinguishing_features.tolist(),
            'deviation_from_global_mean': differences.tolist()
        }


class ModelEvaluation:
    """Educational model evaluation and validation"""
    
    def __init__(self):
        """Initialize model evaluation toolkit"""
        self.evaluation_results = {}
    
    def evaluate_classification_model(self, 
                                    model, 
                                    X_test, 
                                    y_test, 
                                    model_name: str = "Model") -> ModelPerformance:
        """Evaluate classification model performance"""
        
        try:
            # Make predictions
            y_pred = model.predict(X_test)
            y_pred_proba = model.predict_proba(X_test) if hasattr(model, 'predict_proba') else None
            
            # Calculate metrics
            from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
            
            accuracy = accuracy_score(y_test, y_pred)
            precision = precision_score(y_test, y_pred, average='weighted', zero_division=0)
            recall = recall_score(y_test, y_pred, average='weighted', zero_division=0)
            f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)
            
            # AUC score (if probabilities available)
            auc_score = 0.0
            if y_pred_proba is not None:
                try:
                    auc_score = roc_auc_score(y_test, y_pred_proba, multi_class='ovr', average='weighted')
                except:
                    auc_score = 0.0
            
            # Confusion matrix
            cm = confusion_matrix(y_test, y_pred)
            
            # Feature importance (if available)
            feature_importance = {}
            if hasattr(model, 'feature_importances_'):
                feature_importance = dict(enumerate(model.feature_importances_))
            
            # Educational notes
            educational_notes = [
                f"Model shows {accuracy:.1%} accuracy on test data",
                f"Performance suitable for educational demonstration",
                "Model trained on educational dataset"
            ]
            
            if accuracy > 0.8:
                educational_notes.append("High accuracy - good for educational purposes")
            elif accuracy > 0.6:
                educational_notes.append("Moderate accuracy - acceptable for learning")
            else:
                educational_notes.append("Low accuracy - demonstrates need for feature engineering")
            
            return ModelPerformance(
                model_name=model_name,
                accuracy=accuracy,
                precision=precision,
                recall=recall,
                f1_score=f1,
                auc_score=auc_score,
                training_time=0.0,  # Would track actual training time
                feature_importance=feature_importance,
                confusion_matrix=cm,
                educational_notes=educational_notes
            )
            
        except Exception as e:
            return ModelPerformance(
                model_name=model_name,
                accuracy=0.0,
                precision=0.0,
                recall=0.0,
                f1_score=0.0,
                auc_score=0.0,
                training_time=0.0,
                feature_importance={},
                confusion_matrix=np.array([]),
                educational_notes=[f"Evaluation failed: {str(e)}"]
            )
    
    def cross_validation_analysis(self, 
                                model, 
                                X, 
                                y, 
                                cv_folds: int = 5, 
                                model_name: str = "Model") -> Dict[str, Any]:
        """Perform cross-validation analysis"""
        
        try:
            # Perform cross-validation
            cv_scores = cross_val_score(model, X, y, cv=cv_folds, scoring='accuracy')
            
            # Calculate statistics
            cv_mean = cv_scores.mean()
            cv_std = cv_scores.std()
            cv_min = cv_scores.min()
            cv_max = cv_scores.max()
            
            # Determine model stability
            stability_score = cv_mean - cv_std
            
            return {
                'model_name': model_name,
                'cv_folds': cv_folds,
                'cv_scores': cv_scores.tolist(),
                'cv_mean': cv_mean,
                'cv_std': cv_std,
                'cv_min': cv_min,
                'cv_max': cv_max,
                'stability_score': stability_score,
                'performance_consistency': 'High' if cv_std < 0.05 else 'Medium' if cv_std < 0.1 else 'Low',
                'educational_assessment': self._assess_model_performance(cv_mean, cv_std)
            }
            
        except Exception as e:
            return {
                'model_name': model_name,
                'error': str(e),
                'educational_assessment': "Cross-validation failed - check data quality"
            }
    
    def _assess_model_performance(self, mean_score: float, std_score: float) -> str:
        """Provide educational assessment of model performance"""
        
        if mean_score > 0.8 and std_score < 0.05:
            return "Excellent performance with high consistency - suitable for educational examples"
        elif mean_score > 0.7 and std_score < 0.1:
            return "Good performance with moderate consistency - good for learning concepts"
        elif mean_score > 0.6:
            return "Fair performance - demonstrates real-world model variability"
        else:
            return "Poor performance - illustrates need for feature engineering and model tuning"


class EducationalDataScienceShowcase:
    """Main educational data science showcase"""
    
    def __init__(self):
        """Initialize complete data science showcase"""
        self.feature_engineering = FeatureEngineering()
        self.pattern_recognition = PatternRecognition()
        self.time_series_analyzer = TimeSeriesAnalyzer()
        self.cluster_analysis = ClusterAnalysis()
        self.model_evaluation = ModelEvaluation()
    
    def create_educational_dataset(self, n_samples: int = 1000) -> pd.DataFrame:
        """Create educational dataset for demonstrations"""
        
        np.random.seed(42)
        
        # Generate time index
        dates = pd.date_range('2020-01-01', periods=n_samples, freq='D')
        
        # Generate educational market data
        trend = np.linspace(100, 150, n_samples)  # Upward trend
        noise = np.random.normal(0, 5, n_samples)  # Random noise
        
        # Add some pattern components
        seasonal = 10 * np.sin(2 * np.pi * np.arange(n_samples) / 365)  # Yearly cycle
        cyclical = 3 * np.sin(2 * np.pi * np.arange(n_samples) / 30)   # Monthly cycle
        
        price = trend + noise + seasonal + cyclical
        
        # Generate volume (correlated with price changes)
        price_changes = np.diff(np.concatenate([[price[0]], price]))
        volume = np.abs(price_changes) * 1000 + 50000 + np.random.normal(0, 10000, n_samples)
        volume = np.maximum(volume, 10000)  # Ensure positive volume
        
        # Create educational dataset
        data = pd.DataFrame({
            'timestamp': dates,
            'price': price,
            'volume': volume.astype(int),
            'high': price + np.abs(np.random.normal(0, 3, n_samples)),
            'low': price - np.abs(np.random.normal(0, 3, n_samples)),
            'open': price + np.random.normal(0, 1, n_samples),
            'close': price,
            'sector': np.random.choice(['Technology', 'Healthcare', 'Finance', 'Energy'], n_samples),
            'region': np.random.choice(['North America', 'Europe', 'Asia'], n_samples),
            'rating': np.random.choice(['A', 'B', 'C', 'D'], n_samples)
        })
        
        # Ensure OHLC relationships
        data['high'] = np.maximum.reduce([data['high'], data['open'], data['close']])
        data['low'] = np.minimum.reduce([data['low'], data['open'], data['close']])
        
        return data
    
    def comprehensive_analysis(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Perform comprehensive educational data science analysis"""
        
        print("🔬 COMPREHENSIVE DATA SCIENCE ANALYSIS")
        print("=" * 50)
        
        analysis_results = {}
        
        # 1. Basic Data Exploration
        print("1️⃣ DATA EXPLORATION")
        analysis_results['data_exploration'] = self._explore_data(data)
        
        # 2. Feature Engineering
        print("\n2️⃣ FEATURE ENGINEERING")
        analysis_results['feature_engineering'] = self._engineer_features(data)
        
        # 3. Pattern Recognition
        print("\n3️⃣ PATTERN RECOGNITION")
        analysis_results['pattern_recognition'] = self._recognize_patterns(data)
        
        # 4. Time Series Analysis
        print("\n4️⃣ TIME SERIES ANALYSIS")
        analysis_results['time_series'] = self._analyze_time_series(data)
        
        # 5. Cluster Analysis
        print("\n5️⃣ CLUSTER ANALYSIS")
        analysis_results['clustering'] = self._perform_clustering(data)
        
        # 6. Machine Learning
        print("\n6️⃣ MACHINE LEARNING")
        analysis_results['machine_learning'] = self._demonstrate_ml(data)
        
        return analysis_results
    
    def _explore_data(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Perform educational data exploration"""
        
        exploration = {
            'shape': data.shape,
            'columns': data.columns.tolist(),
            'dtypes': data.dtypes.to_dict(),
            'missing_values': data.isnull().sum().to_dict(),
            'basic_statistics': data.describe().to_dict(),
            'correlation_matrix': data.select_dtypes(include=[np.number]).corr().to_dict()
        }
        
        print(f"Dataset shape: {data.shape}")
        print(f"Columns: {', '.join(data.columns.tolist())}")
        print(f"Missing values: {data.isnull().sum().sum()}")
        
        return exploration
    
    def _engineer_features(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Perform educational feature engineering"""
        
        # Create technical features
        technical_features = self.feature_engineering.create_technical_features(data)
        
        # Create interaction features
        enhanced_features = self.feature_engineering.create_interaction_features(technical_features)
        
        print(f"Original features: {len(data.columns)}")
        print(f"Engineered features: {len(enhanced_features.columns)}")
        
        return {
            'original_feature_count': len(data.columns),
            'engineered_feature_count': len(enhanced_features.columns),
            'new_features': [col for col in enhanced_features.columns if col not in data.columns][:10],  # Show first 10
            'feature_list': enhanced_features.columns.tolist()
        }
    
    def _recognize_patterns(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Perform educational pattern recognition"""
        
        price_series = data['price']
        
        # Detect various patterns
        trend_patterns = self.pattern_recognition.detect_trends(price_series)
        mean_reversion_patterns = self.pattern_recognition.detect_mean_reversion(price_series)
        cyclical_patterns = self.pattern_recognition.detect_cyclical_patterns(price_series)
        anomaly_patterns = self.pattern_recognition.detect_anomalies(price_series)
        
        patterns = {
            'trend_detection': trend_patterns,
            'mean_reversion': mean_reversion_patterns,
            'cyclical_patterns': cyclical_patterns,
            'anomaly_detection': anomaly_patterns
        }
        
        print(f"Trend detected: {trend_patterns['trend_direction']}")
        print(f"Mean reversion score: {mean_reversion_patterns['mean_reversion_score']:.3f}")
        print(f"Cycle period: {cyclical_patterns['cycle_period']}")
        print(f"Anomalies detected: {anomaly_patterns['total_anomalies']}")
        
        return patterns
    
    def _analyze_time_series(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Perform educational time series analysis"""
        
        price_series = data.set_index('timestamp')['price']
        
        # Decompose time series
        decomposition = self.time_series_analyzer.decompose_time_series(price_series)
        
        # Detect seasonality
        seasonality = self.time_series_analyzer.detect_seasonality(price_series)
        
        # Generate forecast
        forecast_result = self.time_series_analyzer.forecast_with_ml(price_series)
        
        ts_analysis = {
            'decomposition': decomposition,
            'seasonality_detection': seasonality,
            'forecasting': forecast_result
        }
        
        print(f"Trend strength: {decomposition['trend_strength']:.3f}")
        print(f"Seasonal strength: {decomposition['seasonal_strength']:.3f}")
        print(f"Has seasonality: {seasonality['has_seasonality']}")
        
        return ts_analysis
    
    def _perform_clustering(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Perform educational cluster analysis"""
        
        # Select numeric features for clustering
        numeric_features = data.select_dtypes(include=[np.number]).drop(['timestamp'], axis=1, errors='ignore')
        
        # Remove any remaining NaN values
        clean_features = numeric_features.dropna()
        
        if len(clean_features) < 10:
            return {'error': 'Insufficient clean data for clustering'}
        
        # Standardize features
        scaler = StandardScaler()
        scaled_features = scaler.fit_transform(clean_features)
        
        # Apply different clustering algorithms
        clustering_results = {}
        
        try:
            clustering_results['kmeans'] = self.cluster_analysis.kmeans_clustering(scaled_features, n_clusters=3)
            clustering_results['dbscan'] = self.cluster_analysis.dbscan_clustering(scaled_features)
            clustering_results['hierarchical'] = self.cluster_analysis.hierarchical_clustering(scaled_features)
            
            print(f"K-Means clusters: {clustering_results['kmeans']['n_clusters']}")
            print(f"DBSCAN clusters: {clustering_results['dbscan']['n_clusters']}")
            print(f"Hierarchical clusters: {clustering_results['hierarchical']['n_clusters']}")
            
        except Exception as e:
            clustering_results['error'] = str(e)
            print(f"Clustering error: {e}")
        
        return clustering_results
    
    def _demonstrate_ml(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Demonstrate educational machine learning"""
        
        try:
            # Create target variable (price direction)
            price_change = data['price'].pct_change()
            target = (price_change > price_change.median()).astype(int)  # Binary classification
            
            # Create features
            numeric_features = data.select_dtypes(include=[np.number]).drop(['price'], axis=1, errors='ignore')
            categorical_features = data.select_dtypes(include=['object'])
            
            # Encode categorical features
            for col in categorical_features.columns:
                le = LabelEncoder()
                numeric_features[col] = le.fit_transform(categorical_features[col].astype(str))
            
            # Align target with features
            valid_indices = ~(numeric_features.isna().any(axis=1) | target.isna())
            X = numeric_features[valid_indices]
            y = target[valid_indices]
            
            if len(X) < 50:
                return {'error': 'Insufficient data for ML demonstration'}
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
            
            # Train models
            models = {
                'RandomForest': RandomForestClassifier(n_estimators=50, random_state=42),
                'SVM': SVC(random_state=42, probability=True),
                'NeuralNetwork': MLPClassifier(hidden_layer_sizes=(50,), random_state=42, max_iter=500)
            }
            
            ml_results = {}
            
            for model_name, model in models.items():
                try:
                    # Train model
                    model.fit(X_train, y_train)
                    
                    # Evaluate
                    performance = self.model_evaluation.evaluate_classification_model(
                        model, X_test, y_test, model_name
                    )
                    
                    # Cross-validation
                    cv_analysis = self.model_evaluation.cross_validation_analysis(
                        model, X_train, y_train, cv_folds=3, model_name=model_name
                    )
                    
                    ml_results[model_name] = {
                        'performance': {
                            'accuracy': performance.accuracy,
                            'precision': performance.precision,
                            'recall': performance.recall,
                            'f1_score': performance.f1_score,
                            'educational_notes': performance.educational_notes
                        },
                        'cross_validation': cv_analysis,
                        'feature_importance': performance.feature_importance
                    }
                    
                    print(f"{model_name} - Accuracy: {performance.accuracy:.3f}")
                    
                except Exception as e:
                    ml_results[model_name] = {'error': str(e)}
            
            return ml_results
            
        except Exception as e:
            return {'error': f'ML demonstration failed: {str(e)}'}


def demonstrate_data_science_showcase():
    """Demonstrate educational data science capabilities"""
    
    print("🎓 DATA SCIENCE SHOWCASE - EDUCATIONAL DEMONSTRATION")
    print("=" * 60)
    print("⚠️  EDUCATIONAL PURPOSES ONLY - NO REAL MONEY")
    print("⚠️  This showcase demonstrates data science concepts and techniques")
    print("⚠️  All data is simulated for educational purposes")
    print()
    
    # Initialize showcase
    showcase = EducationalDataScienceShowcase()
    
    # Create educational dataset
    data = showcase.create_educational_dataset(n_samples=500)
    
    print(f"📊 Created educational dataset with {len(data)} samples")
    print(f"Date range: {data['timestamp'].min()} to {data['timestamp'].max()}")
    print(f"Price range: ${data['price'].min():.2f} - ${data['price'].max():.2f}")
    print()
    
    # Perform comprehensive analysis
    results = showcase.comprehensive_analysis(data)
    
    # Summary
    print("\n" + "="*60)
    print("📈 ANALYSIS SUMMARY")
    print("=" * 60)
    
    if 'pattern_recognition' in results:
        patterns = results['pattern_recognition']
        print(f"🔍 Pattern Detection Results:")
        print(f"   • Trend: {patterns['trend_detection']['trend_direction']}")
        print(f"   • Mean Reversion Score: {patterns['mean_reversion']['mean_reversion_score']:.3f}")
        print(f"   • Anomalies Found: {patterns['anomaly_detection']['total_anomalies']}")
    
    if 'time_series' in results:
        ts = results['time_series']
        print(f"📊 Time Series Analysis:")
        print(f"   • Trend Strength: {ts['decomposition']['trend_strength']:.3f}")
        print(f"   • Seasonality Detected: {ts['seasonality_detection']['has_seasonality']}")
        if 'forecast' in ts['forecasting'] and 'error' not in ts['forecasting']:
            print(f"   • ML Forecast: ${ts['forecasting']['forecast']:.2f}")
    
    if 'machine_learning' in results and 'error' not in results['machine_learning']:
        ml_results = results['machine_learning']
        print(f"🤖 Machine Learning Results:")
        for model_name, result in ml_results.items():
            if 'error' not in result:
                acc = result['performance']['accuracy']
                print(f"   • {model_name}: {acc:.1%} accuracy")
    
    print("\n" + "="*60)
    print("✅ DATA SCIENCE SHOWCASE COMPLETE")
    print("🔍 This framework demonstrates:")
    print("   • Feature Engineering & Transformation")
    print("   • Pattern Recognition & Classification")
    print("   • Time Series Analysis & Decomposition")
    print("   • Clustering & Unsupervised Learning")
    print("   • Supervised Learning & Model Evaluation")
    print("   • Cross-Validation & Performance Assessment")
    print("   • Statistical Analysis & Visualization")
    print("=" * 60)


if __name__ == "__main__":
    demonstrate_data_science_showcase()