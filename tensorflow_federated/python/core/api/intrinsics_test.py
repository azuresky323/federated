# Copyright 2018, The TensorFlow Federated Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Tests for types."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import collections

# Dependency imports
from absl.testing import absltest
import tensorflow as tf

from tensorflow_federated.python.core.api.computations import federated_computation
from tensorflow_federated.python.core.api.computations import tf_computation
from tensorflow_federated.python.core.api.intrinsics import federated_aggregate
from tensorflow_federated.python.core.api.intrinsics import federated_average
from tensorflow_federated.python.core.api.intrinsics import federated_broadcast
from tensorflow_federated.python.core.api.intrinsics import federated_collect
from tensorflow_federated.python.core.api.intrinsics import federated_map
from tensorflow_federated.python.core.api.intrinsics import federated_reduce
from tensorflow_federated.python.core.api.intrinsics import federated_sum
from tensorflow_federated.python.core.api.intrinsics import federated_zip
from tensorflow_federated.python.core.api.placements import CLIENTS
from tensorflow_federated.python.core.api.placements import SERVER
from tensorflow_federated.python.core.api.types import FederatedType
from tensorflow_federated.python.core.api.types import NamedTupleType


class IntrinsicsTest(absltest.TestCase):

  def test_federated_broadcast_with_server_all_equal_int(self):
    @federated_computation(FederatedType(tf.int32, SERVER, True))
    def foo(x):
      return federated_broadcast(x)
    self.assertEqual(str(foo.type_signature), '(int32@SERVER -> int32@CLIENTS)')

  def test_federated_broadcast_with_server_non_all_equal_int(self):
    with self.assertRaises(TypeError):
      @federated_computation(FederatedType(tf.int32, SERVER))
      def _(x):
        return federated_broadcast(x)

  def test_federated_broadcast_with_client_int(self):
    with self.assertRaises(TypeError):
      @federated_computation(FederatedType(tf.int32, CLIENTS, True))
      def _(x):
        return federated_broadcast(x)

  def test_federated_broadcast_with_non_federated_val(self):
    with self.assertRaises(TypeError):
      @federated_computation(tf.int32)
      def _(x):
        return federated_broadcast(x)

  def test_federated_map_with_client_all_equal_int(self):
    @federated_computation(FederatedType(tf.int32, CLIENTS, True))
    def foo(x):
      return federated_map(x, tf_computation(lambda x: x > 10, tf.int32))
    self.assertEqual(
        str(foo.type_signature), '(int32@CLIENTS -> bool@CLIENTS)')

  def test_federated_map_with_client_non_all_equal_int(self):
    @federated_computation(FederatedType(tf.int32, CLIENTS))
    def foo(x):
      return federated_map(x, tf_computation(lambda x: x > 10, tf.int32))
    self.assertEqual(
        str(foo.type_signature), '({int32}@CLIENTS -> {bool}@CLIENTS)')

  def test_federated_map_with_non_federated_val(self):
    with self.assertRaises(TypeError):
      @federated_computation(tf.int32)
      def _(x):
        return federated_map(x, tf_computation(lambda x: x > 10, tf.int32))

  def test_federated_sum_with_client_int(self):
    @federated_computation(FederatedType(tf.int32, CLIENTS))
    def foo(x):
      return federated_sum(x)
    self.assertEqual(
        str(foo.type_signature), '({int32}@CLIENTS -> int32@SERVER)')

  def test_federated_sum_with_client_string(self):
    with self.assertRaises(TypeError):
      @federated_computation(FederatedType(tf.string, CLIENTS))
      def _(x):
        return federated_sum(x)

  def test_federated_sum_with_server_int(self):
    with self.assertRaises(TypeError):
      @federated_computation(FederatedType(tf.int32, SERVER))
      def _(x):
        return federated_sum(x)

  def test_federated_zip_with_client_non_all_equal_int_and_bool(self):
    @federated_computation([
        FederatedType(tf.int32, CLIENTS),
        FederatedType(tf.bool, CLIENTS, True)])
    def foo(x, y):
      return federated_zip([x, y])
    self.assertEqual(
        str(foo.type_signature),
        '(<{int32}@CLIENTS,bool@CLIENTS> -> {<int32,bool>}@CLIENTS)')

  def test_federated_zip_with_client_all_equal_int_and_bool(self):
    @federated_computation([
        FederatedType(tf.int32, CLIENTS, True),
        FederatedType(tf.bool, CLIENTS, True)])
    def foo(x, y):
      return federated_zip([x, y])
    self.assertEqual(
        str(foo.type_signature),
        '(<int32@CLIENTS,bool@CLIENTS> -> <int32,bool>@CLIENTS)')

  def test_federated_zip_with_server_int_and_bool(self):
    with self.assertRaises(TypeError):
      @federated_computation([
          FederatedType(tf.int32, SERVER), FederatedType(tf.bool, SERVER)])
      def _(x, y):
        return federated_zip([x, y])

  def test_federated_reduce_with_tf_add_client_int(self):
    @federated_computation(FederatedType(tf.int32, CLIENTS))
    def foo(x):
      # TODO(b/113112108): Possibly add plain constants as a building block.
      zero = tf_computation(lambda: tf.constant(0))()
      plus = tf_computation(tf.add, [tf.int32, tf.int32])
      return federated_reduce(x, zero, plus)
    self.assertEqual(
        str(foo.type_signature),
        '({int32}@CLIENTS -> int32@SERVER)')

  def test_federated_collect_with_client_int(self):
    @federated_computation(FederatedType(tf.int32, CLIENTS))
    def foo(x):
      return federated_collect(x)
    self.assertEqual(
        str(foo.type_signature), '({int32}@CLIENTS -> int32*@SERVER)')

  def test_federated_collect_with_server_int_fails(self):
    with self.assertRaises(TypeError):
      @federated_computation(FederatedType(tf.int32, SERVER))
      def _(x):
        return federated_collect(x)

  def test_federated_average_with_client_float32_without_weight(self):
    @federated_computation(FederatedType(tf.float32, CLIENTS))
    def foo(x):
      return federated_average(x)
    self.assertEqual(
        str(foo.type_signature), '({float32}@CLIENTS -> float32@SERVER)')

  def test_federated_average_with_client_tuple_with_int32_weight(self):
    @federated_computation([
        FederatedType([('x', tf.float64), ('y', tf.float64)], CLIENTS),
        FederatedType(tf.int32, CLIENTS)])
    def foo(x, y):
      return federated_average(x, y)
    self.assertEqual(
        str(foo.type_signature),
        '(<{<x=float64,y=float64>}@CLIENTS,{int32}@CLIENTS> '
        '-> <x=float64,y=float64>@SERVER)')

  def test_federated_average_with_client_int32_fails(self):
    with self.assertRaises(TypeError):
      @federated_computation(FederatedType(tf.int32, CLIENTS))
      def _(x):
        return federated_average(x)

  def test_federated_average_with_string_weight_fails(self):
    with self.assertRaises(TypeError):
      @federated_computation([
          FederatedType(tf.float32, CLIENTS),
          FederatedType(tf.string, CLIENTS)])
      def _(x, y):
        return federated_average(x, y)

  def test_federated_aggregate_with_client_int(self):
    # The representation used during the aggregation process will be a named
    # tuple with 2 elements - the integer 'total' that represents the sum of
    # elements encountered, and the integer element 'count'.
    # pylint: disable=invalid-name
    Accumulator = collections.namedtuple('Accumulator', 'total count')
    accumulator_type = NamedTupleType(Accumulator(tf.int32, tf.int32))

    # The 'zero' in the algebra will consist of a zero total and a zero count.
    @tf_computation
    def make_zero():
      return Accumulator(tf.constant(0), tf.constant(0))

    # The operator to use during the first stage simply adds an element to the
    # total and updates the count.
    @tf_computation([accumulator_type, tf.int32])
    def accumulate(accu, elem):
      return Accumulator(accu.total + elem, accu.count + 1)

    # The operator to use during the second stage simply adds total and count.
    @tf_computation([accumulator_type, accumulator_type])
    def merge(x, y):
      return Accumulator(x.total + y.total, x.count + y.count)

    # The operator to use during the final stage simply computes the ratio.
    @tf_computation(accumulator_type)
    def report(accu):
      return tf.to_float(accu.total) / tf.to_float(accu.count)

    @federated_computation(FederatedType(tf.int32, CLIENTS))
    def foo(x):
      return federated_aggregate(x, make_zero(), accumulate, merge, report)

    self.assertEqual(
        str(foo.type_signature), '({int32}@CLIENTS -> float32@SERVER)')

  def test_num_over_temperature_threshold_example(self):
    @federated_computation([
        FederatedType(tf.float32, CLIENTS),
        FederatedType(tf.float32, SERVER, True)])
    def foo(temperatures, threshold):
      return federated_sum(federated_map(
          federated_zip([temperatures, federated_broadcast(threshold)]),
          tf_computation(
              lambda x, y: tf.to_int32(tf.greater(x, y)),
              [tf.float32, tf.float32])))
    self.assertEqual(
        str(foo.type_signature),
        '(<{float32}@CLIENTS,float32@SERVER> -> int32@SERVER)')


if __name__ == '__main__':
  absltest.main()
