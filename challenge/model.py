import pandas as pd
import numpy as np
import joblib
from datetime import datetime
from sklearn.linear_model import LogisticRegression
from typing import Tuple, Union, List
import os

class DelayModel:

    def __init__(self):
        self._model_path = os.path.join(os.path.dirname(__file__), "model.joblib")
        
        # Initialize model
        self._model = LogisticRegression(class_weight='balanced', random_state=42)
        
        self.top_10_features = [
            "OPERA_Latin American Wings", 
            "MES_7",
            "MES_10",
            "OPERA_Grupo LATAM",
            "MES_12",
            "TIPOVUELO_I",
            "MES_4",
            "MES_11",
            "OPERA_Sky Airline",
            "OPERA_Copa Air"
        ]
        
        # Load model using joblib
        if os.path.exists(self._model_path):
            self._model = joblib.load(self._model_path)

    def _get_min_diff(self, data: pd.Series) -> float:
        fecha_o = datetime.strptime(data['Fecha-O'], '%Y-%m-%d %H:%M:%S')
        fecha_i = datetime.strptime(data['Fecha-I'], '%Y-%m-%d %H:%M:%S')
        min_diff = ((fecha_o - fecha_i).total_seconds())/60
        return min_diff

    def preprocess(
        self,
        data: pd.DataFrame,
        target_column: str = None
    ) -> Union[Tuple[pd.DataFrame, pd.DataFrame], pd.DataFrame]:
        
        """
        Prepare raw data for training or predict.

        Args:
        data (pd.DataFrame): raw data.
        target_column (str, optional): if set, the target is returned.

        Returns:
        Tuple[pd.DataFrame, pd.DataFrame]: features and target.
        or
        pd.DataFrame: features.

        """
        
        features = pd.concat([
            pd.get_dummies(data['OPERA'], prefix = 'OPERA'),
            pd.get_dummies(data['TIPOVUELO'], prefix = 'TIPOVUELO'), 
            pd.get_dummies(data['MES'], prefix = 'MES')], 
            axis = 1
        )

        for col in self.top_10_features:
            if col not in features.columns:
                features[col] = 0
        
        features = features[self.top_10_features]

        if target_column:
            if target_column not in data.columns:
                 data['min_diff'] = data.apply(self._get_min_diff, axis = 1)
                 threshold_in_minutes = 15
                 data[target_column] = np.where(data['min_diff'] > threshold_in_minutes, 1, 0)
            
            target = pd.DataFrame(data[target_column])
            return features, target
        else:
            return features

    def fit(
        self,
        features: pd.DataFrame,
        target: pd.DataFrame
    ) -> None:
        """
        Fit model with preprocessed data.

        Args:
        features (pd.DataFrame): preprocessed data.
        target (pd.DataFrame): target.
        """
        
        self._model.fit(features, target.values.ravel())
        
        # Save using joblib
        joblib.dump(self._model, self._model_path)
        return

    def predict(
        self,
        features: pd.DataFrame
    ) -> List[int]:
        """
        Predict delays for new flights.

        Args:
        features (pd.DataFrame): preprocessed data.

        Returns:
        (List[int]): predicted targets.
        """
        
        if len(features.columns) != len(self.top_10_features):
             for col in self.top_10_features:
                if col not in features.columns:
                    features[col] = 0
             features = features[self.top_10_features]

        predictions = self._model.predict(features)
        return predictions.tolist()