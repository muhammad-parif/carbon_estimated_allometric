# -*- coding: utf-8 -*-
def classFactory(iface):
    from .plugin import CarbonEstimatorPlugin
    return CarbonEstimatorPlugin(iface)
