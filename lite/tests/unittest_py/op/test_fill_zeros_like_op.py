# Copyright (c) 2021 PaddlePaddle Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
sys.path.append('../')

from auto_scan_test import AutoScanTest, IgnoreReasons
from program_config import TensorConfig, ProgramConfig, OpConfig, CxxConfig, TargetType, PrecisionType, DataLayoutType, Place
import unittest

import hypothesis
from hypothesis import given, settings, seed, example, assume

import numpy as np
from functools import partial
import hypothesis.strategies as st


class TestFillZerosLikeOp(AutoScanTest):
    def __init__(self, *args, **kwargs):
        AutoScanTest.__init__(self, *args, **kwargs)
        self.enable_testing_on_place(
            TargetType.Host,
            PrecisionType.FP32,
            DataLayoutType.NCHW,
            thread=[1, 2, 4])

    def is_program_valid(self,
                         program_config: ProgramConfig,
                         predictor_config: CxxConfig) -> bool:
        return True

    def sample_program_configs(self, draw):
        in_shape_tmp = draw(
            st.lists(
                st.integers(
                    min_value=1, max_value=8), min_size=1, max_size=4))
        in_shape = draw(st.sampled_from([in_shape_tmp, []]))

        def generate_input(*args, **kwargs):
            if kwargs["type"] == "int32":
                return np.random.randint(kwargs["low"], kwargs["high"],
                                         kwargs["shape"]).astype(np.int32)
            elif kwargs["type"] == "int64":
                return np.random.randint(kwargs["low"], kwargs["high"],
                                         kwargs["shape"]).astype(np.int64)
            elif kwargs["type"] == "float32":
                if kwargs["shape"] == []:
                    return np.random.random(kwargs["shape"]).astype(np.float32)
                else:
                    return (kwargs["high"] - kwargs["low"]) * np.random.random(
                        kwargs["shape"]).astype(np.float32) + kwargs["low"]

        input_type = draw(st.sampled_from(["float32", "int64", "int32"]))

        fill_zeros_like_op = OpConfig(
            type="fill_zeros_like",
            inputs={"X": ["input_data"]},
            outputs={"Out": ["output_data"]},
            attrs={})
        program_config = ProgramConfig(
            ops=[fill_zeros_like_op],
            weights={},
            inputs={
                "input_data": TensorConfig(data_gen=partial(
                    generate_input,
                    type=input_type,
                    low=-10,
                    high=10,
                    shape=in_shape))
            },
            outputs=["output_data"])
        return program_config

    def sample_predictor_configs(self):
        return self.get_predictor_configs(), ["fill_zeros_like"], (1e-5, 1e-5)

    def add_ignore_pass_case(self):
        def _teller1(program_config, predictor_config):
            target_type = predictor_config.target()
            in_x_shape = list(program_config.inputs["input_data"].shape)
            if target_type != TargetType.ARM and target_type != TargetType.Host:
                if len(in_x_shape) == 0:
                    return True

        self.add_ignore_check_case(_teller1,
                                   IgnoreReasons.PADDLELITE_NOT_SUPPORT,
                                   "Only test 0D-tensor on CPU(ARM/Host) now.")

    def test(self, *args, **kwargs):
        self.run_and_statis(quant=False, max_examples=100)


if __name__ == "__main__":
    unittest.main(argv=[''])
