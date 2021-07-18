import unittest

import random
from spn.base.nodes.node import get_nodes_by_type, SumNode, LeafNode
from spn.base.rat.inference import log_likelihood, likelihood
from spn.backend.pytorch.inference import log_likelihood, likelihood
import torch
import numpy as np
from spn.base.rat.region_graph import random_region_graph, _print_region_graph
from spn.base.rat.rat_spn import RatSpn, construct_spn
from spn.backend.pytorch.rat.rat_spn import TorchRatSpn, toNodes, toTorch, _RegionLayer, _LeafLayer


class TestTorchRatSpn(unittest.TestCase):
    def test_torch_rat_spn_to_nodes(self):

        # create region graph
        rg = random_region_graph(X=set(range(9)), depth=3, replicas=2, num_splits=3)

        # create torch rat spn from region graph
        torch_rat = TorchRatSpn(rg, num_nodes_root=4, num_nodes_region=2, num_nodes_leaf=3)

        # randomly change parameters from inital values
        for region in torch_rat.region_graph.regions:

            region_layer: _RegionLayer = torch_rat.rg_layers[region]

            if isinstance(region_layer, _RegionLayer):
                region_layer.weight.data = torch.rand_like(region_layer.weight.data)
            else:
                for leaf_node in region_layer.leaf_nodes:
                    # TODO: only works for Gaussians (provide method to randomize parameters ?)
                    leaf_node.set_params(random.random(), random.random())

        # convert torch rat spn to node rat spn
        rat = toNodes(torch_rat)

        # create dummy input data (batch size x random variables)
        dummy_data = np.random.randn(3, 9)

        # compute outputs for node rat spn
        nodes_output = log_likelihood(rat, dummy_data)

        # compute outputs for torch rat spn
        torch_output = log_likelihood(torch_rat, torch.tensor(dummy_data, dtype=torch.float32))

        # compare outputs
        # self.assertTrue( np.allclose(nodes_output, torch_output.detach().cpu().numpy(), rtol=0.3, equal_nan=True) )

    def test_nodes_rat_spn_to_torch(self):

        # create region graph
        rg = random_region_graph(X=set(range(9)), depth=3, replicas=2, num_splits=3)

        # create torch rat spn from region graph
        rat = construct_spn(rg, num_nodes_root=5, num_nodes_region=3, num_nodes_leaf=2)

        sum_nodes = get_nodes_by_type(rat.root_node, SumNode)
        leaf_nodes = get_nodes_by_type(rat.root_node, LeafNode)

        # randomly change parameters from inital values
        for node in sum_nodes:
            node.weights = np.random.rand(len(node.weights))

        for node in leaf_nodes:
            node.set_params(random.random(), random.random())

        # convert node rat spn to torch rat spn
        torch_rat = toTorch(rat)

        # create dummy input data (batch size x random variables)
        dummy_data = np.random.randn(3, 9)

        # compute outputs for node rat spn
        nodes_output = log_likelihood(rat, dummy_data)

        # compute outputs for torch rat spn
        torch_output = log_likelihood(torch_rat, torch.tensor(dummy_data, dtype=torch.float32))

        # compare outputs
        # self.assertTrue( np.allclose(nodes_output, torch_output.detach().cpu().numpy(), rtol=1e-3, equal_nan=True) )

    def test_torch_rat_spn_to_nodes_to_torch(self):

        # create region graph
        rg = random_region_graph(X=set(range(9)), depth=3, replicas=2, num_splits=3)

        # create torch rat spn from region graph
        torch_rat = TorchRatSpn(rg, num_nodes_root=4, num_nodes_region=2, num_nodes_leaf=3)

        # randomly change parameters from inital values
        for region in torch_rat.region_graph.regions:

            region_layer: _RegionLayer = torch_rat.rg_layers[region]

            if isinstance(region_layer, _RegionLayer):
                region_layer.weight.data = torch.rand_like(region_layer.weight.data)
            else:
                for leaf_node in region_layer.leaf_nodes:
                    # TODO: only works for Gaussians (provide method to randomize parameters ?)
                    leaf_node.set_params(random.random(), random.random())

        # convert torch rat spn to nodes and back to torch
        torch_rat_2 = toTorch(toNodes(torch_rat))

        # compare parameters
        for p1, p2 in zip(torch_rat.parameters(), torch_rat_2.parameters()):
            self.assertTrue(torch.allclose(p1.data, p2.data))

        # create dummy input data (batch size x random variables)
        dummy_data = np.random.randn(3, 9)

        # compute outputs for node rat spn
        torch_output = log_likelihood(torch_rat, torch.tensor(dummy_data, dtype=torch.float32))

        # compute outputs for torch rat spn
        torch_output_2 = log_likelihood(torch_rat_2, torch.tensor(dummy_data, dtype=torch.float32))

        # compare outputs
        self.assertTrue(torch.allclose(torch_output, torch_output_2))


if __name__ == "__main__":
    unittest.main()
