
from __future__ import annotations

import uuid
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
from stable_baselines3 import PPO, SAC, DDPG
from stable_baselines3.common.base_class import BaseAlgorithm

from ..config import DRLConfig


ALGOS = {
    "PPO": PPO,
    "SAC": SAC,
    "DDPG": DDPG,
}


class EnsembleDRLAgent:
    """Ensemble of PPO + SAC + DDPG for trading.

    - Trains each algorithm on the same environment.
    - Saves each model under a unique ID.
    - For inference, aggregates actions from all models (mean of actions).
    """

    def __init__(self, model_dir: str = "models_ensemble") -> None:
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.registry: Dict[str, Dict] = {}  # model_id -> metadata

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------
    def _build_model(self, algo_name: str, env, config: DRLConfig) -> BaseAlgorithm:
        algo_name = algo_name.upper()
        if algo_name not in ALGOS:
            raise ValueError(f"Unsupported algorithm: {algo_name}")

        Algo = ALGOS[algo_name]
        model = Algo(
            "MlpPolicy",
            env,
            verbose=1,
            tensorboard_log=str(self.model_dir / "tb"),
            seed=config.seed,
            gamma=config.gamma,
        )
        return model

    def train_ensemble(
        self,
        env,
        config: DRLConfig,
        timesteps: int,
        run_id: Optional[str] = None,
    ) -> Dict:
        """Train all algorithms in config.algo_list on the given env.

        Returns a dict with:
        - run_id
        - model_ids: list of model IDs for the ensemble
        """

        if run_id is None:
            run_id = str(uuid.uuid4())

        model_ids: List[str] = []

        for algo_name in config.algo_list:
            model = self._build_model(algo_name, env, config)
            print(f"[Ensemble] Training {algo_name} for {timesteps} timesteps...")
            model.learn(total_timesteps=int(timesteps))

            model_id = f"{run_id}_{algo_name.upper()}"
            model_path = self.model_dir / f"{model_id}.zip"
            model.save(model_path)

            self.registry[str(model_id)] = {
                "algo": algo_name.upper(),
                "path": model_path,
                "run_id": run_id,
            }
            model_ids.append(str(model_id))

        return {"run_id": run_id, "model_ids": model_ids}

    # ------------------------------------------------------------------
    # Inference
    # ------------------------------------------------------------------
    def _load_model(self, model_id: str) -> BaseAlgorithm:
        meta = self.registry.get(model_id)
        if meta is None:
            # try to infer algo from filename
            path = self.model_dir / f"{model_id}.zip"
            if not path.exists():
                raise ValueError(f"Unknown model_id: {model_id}")

            # default to PPO if unknown (you can customize this)
            model = PPO.load(path)
            return model

        algo = meta["algo"].upper()
        path = meta["path"]

        if algo == "PPO":
            return PPO.load(path)
        elif algo == "SAC":
            return SAC.load(path)
        elif algo == "DDPG":
            return DDPG.load(path)
        else:
            raise ValueError(f"Unsupported algo in registry: {algo}")

    def predict_ensemble_action(
        self,
        model_ids: List[str],
        observation: np.ndarray,
        deterministic: bool = False,
    ) -> np.ndarray:
        """Aggregate predictions from all models.

        For continuous actions, we simply take the mean of all actions.
        """

        actions: List[float] = []
        obs = observation

        for model_id in model_ids:
            model = self._load_model(model_id)
            a, _ = model.predict(obs, deterministic=deterministic)
            actions.append(float(a[0]))

        if not actions:
            raise ValueError("No model_ids provided for ensemble.")

        mean_action = float(np.mean(actions))
        return np.array([mean_action], dtype=np.float32)
