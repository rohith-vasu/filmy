import mlflow.pyfunc
import numpy as np
import pickle
import os


class ALSModelWrapper(mlflow.pyfunc.PythonModel):
    """
    MLflow PyFunc wrapper for Implicit ALS.
    Only loads artifacts; doesn't implement full predict().
    """

    def load_context(self, context):
        self.model = pickle.load(open(context.artifacts["implicit_model"], "rb"))
        self.dataset_map = pickle.load(open(context.artifacts["dataset_map"], "rb"))
        self.user_factors = np.load(context.artifacts["user_factors"])
        self.item_factors = np.load(context.artifacts["item_factors"])

    def predict(self, context, model_input: np.ndarray) -> np.ndarray:
        """
        This exists only for MLflow; not used in the backend.
        Returns dot(user_vec, item_factors.T)
        """
        return model_input @ self.item_factors.T
