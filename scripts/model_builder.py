#!/usr/bin/env python3
"""
Functionality for building models as nn.Module class.

TODO:
    - Add TipburnSegmenter
    - Think about what backbones to use for semantic segmentation
"""
# Import statements
import torch
import torch.nn as nn
import torchvision


# Define nn.Module class for model
class TipburnClassifier(nn.Module):
    def __init__(
        self,
        bb_name,
        n_classes,
        n_channels=3,
        bb_weights="IMAGENET1K_V1",
        bb_freeze=True,
    ):
        """Creates tipburn classifier as PyTorch nn.Module class.

        Creates a CNN with a backbone. Backbone can be pretrained and frozen.
        Names of networks and weights should follow the torchvision API:
            https://pytorch.org/vision/stable/models.html#listing-and-retrieving-available-models
        Only supports the following backbones:
            resnet50, wide_resnet50_2

        Args:
            bb_name (str): Name of backbone network as in torchvision.models.
            n_classes (int): Numbers of classes to predict.
            n_channels (int, optional): Number of input channels from data. Defaults to 3.
            bb_weights (str, optional): Name of pretrained weights. Defaults to IMAGENET_1K_V1.
            bb_freeze (bool, optional): If true, freezes weights in backbone. Defaults to True.

        Raises:
            Exception: _description_
        """
        super(TipburnClassifier, self).__init__()
        self.n_classes = n_classes

        # Set backbone
        # Allows for different models and pretrained weights
        backbone_call = f'torchvision.models.{bb_name}(weights="{bb_weights}")'
        self.backbone = eval(backbone_call)

        # Freeze weights in backbone
        for param in self.backbone.parameters():
            param.requires_grad = not bb_freeze

        # For ResNets
        if bb_name in ["resnet50", "wide_resnet50_2"]:
            # Remember number of input features of second layer
            out_features_bn1 = self.backbone.bn1.num_features

            # Change input channels of first conv layer
            self.backbone.conv1 = nn.Conv2d(
                n_channels,
                out_features_bn1,
                kernel_size=(7, 7),
                stride=(2, 2),
                padding=(3, 3),
                bias=False,
            )

            # Remember number of output features of backbone
            out_features_bb = list(self.backbone.children())[-1].in_features

            # Remove final layer of backbone
            self.backbone = nn.Sequential(*list(self.backbone.children())[:-1])

            # Classifier with output features of backbone as input
            # TODO: make more sophisticated -> dropout, batch normalization?
            self.classifier = nn.Sequential(
                nn.Flatten(), nn.Linear(out_features_bb, self.n_classes)
            )
        else:
            raise Exception("Selected backbone model is unsupported")

    def forward(self, x):
        features = self.backbone(x)
        pred_logits = self.classifier(features)
        return pred_logits
