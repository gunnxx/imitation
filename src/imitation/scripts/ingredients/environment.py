"""Environment Ingredient for sacred experiments."""
import contextlib
from typing import Any, Generator, Mapping

import numpy as np
import sacred
from stable_baselines3.common import vec_env

import imitation.scripts.ingredients.common as common
from imitation.data import wrappers
from imitation.scripts.ingredients.environment_name import environment_name_ingredient
from imitation.util import util

environment_ingredient = sacred.Ingredient(
    "environment",
    ingredients=[
        environment_name_ingredient,
        common.common_ingredient,
    ],
)


@environment_ingredient.config
def config():
    num_vec = 8  # number of environments in VecEnv
    parallel = True  # Use SubprocVecEnv rather than DummyVecEnv
    max_episode_steps = None  # Set to positive int to limit episode horizons
    env_make_kwargs = {}  # The kwargs passed to `spec.make`.

    locals()  # quieten flake8


@contextlib.contextmanager
@environment_ingredient.capture
def make_venv(
    _rnd: np.random.Generator,
    environment_name: dict,
    common: dict,
    num_vec: int,
    parallel: bool,
    max_episode_steps: int,
    env_make_kwargs: Mapping[str, Any],
    **kwargs,
) -> Generator[vec_env.VecEnv, None, None]:
    """Builds the vector environment.

    Args:
        environment_name: The environment name ingredient to use.
        common: The common ingredient to use for the log directory.
        num_vec: Number of `gym.Env` instances to combine into a vector environment.
        parallel: Whether to use "true" parallelism. If True, then use `SubProcVecEnv`.
            Otherwise, use `DummyVecEnv` which steps through environments serially.
        max_episode_steps: If not None, then a TimeLimit wrapper is applied to each
            environment to artificially limit the maximum number of timesteps in an
            episode.
        env_make_kwargs: The kwargs passed to `spec.make` of a gym environment.
        kwargs: Passed through to `util.make_vec_env`.

    Yields:
        The constructed vector environment.
    """
    # Note: we create the venv outside the try -- finally block for the case that env
    #     creation fails.
    venv = util.make_vec_env(
        environment_name["gym_id"],
        rng=_rnd,
        n_envs=num_vec,
        parallel=parallel,
        max_episode_steps=max_episode_steps,
        log_dir=common["log_dir"],
        env_make_kwargs=env_make_kwargs,
        **kwargs,
    )
    try:
        yield venv
    finally:
        venv.close()


@contextlib.contextmanager
@environment_ingredient.capture
def make_rollout_venv(
    environment_name: dict,
    num_vec: int,
    parallel: bool,
    max_episode_steps: int,
    env_make_kwargs: Mapping[str, Any],
    _rnd: np.random.Generator,
) -> Generator[vec_env.VecEnv, None, None]:
    """Builds the vector environment for rollouts.

    This environment does no logging, and it is wrapped in a `RolloutInfoWrapper`.

    Args:
        environment_name: The environment name ingredient to use.
        num_vec: Number of `gym.Env` instances to combine into a vector environment.
        parallel: Whether to use "true" parallelism. If True, then use `SubProcVecEnv`.
            Otherwise, use `DummyVecEnv` which steps through environments serially.
        max_episode_steps: If not None, then a TimeLimit wrapper is applied to each
            environment to artificially limit the maximum number of timesteps in an
            episode.
        env_make_kwargs: The kwargs passed to `spec.make` of a gym environment.
        _rnd: Random number generator provided by Sacred.

    Yields:
        The constructed vector environment.
    """
    # Note: we create the venv outside the try -- finally block for the case that env
    #     creation fails.
    venv = util.make_vec_env(
        environment_name["gym_id"],
        rng=_rnd,
        n_envs=num_vec,
        parallel=parallel,
        max_episode_steps=max_episode_steps,
        log_dir=None,
        env_make_kwargs=env_make_kwargs,
        post_wrappers=[lambda env, i: wrappers.RolloutInfoWrapper(env)],
    )
    try:
        yield venv
    finally:
        venv.close()


@environment_ingredient.named_config
def fast():
    num_vec = 2
    parallel = False  # easier to debug with everything in one process
    max_episode_steps = 5

    locals()  # quieten flake8
