#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Author:  Dominik Gresch <greschd@gmx.ch>
# Date:    04.06.2015 14:26:21 CEST
# File:    helpers.py

"""
This module contains a helper function to create a list of hoppings from a given matrix (:meth:`matrix_to_hop`).
"""

import numpy as np
from fsc.export import export

@export
def matrix_to_hop(mat, orbitals=None, R=(0, 0, 0), multiplier=1.):
    r"""
    Turns a square matrix into a series of hopping terms.

    :param mat: The matrix to be converted.

    :param orbitals:    Indices of the orbitals that make up the basis w.r.t. which the matrix is defined. By default (``orbitals=None``), the first ``len(mat)`` orbitals are used.
    :type orbitals:     list

    :param R:   Lattice vector for all the hopping terms.
    :type R:    list

    :param multiplier:  Multiplicative constant for the hopping strength.
    :type multiplier: numbers.Complex
    """
    if orbitals is None:
        orbitals = list(range(len(mat)))
    hop = []
    for i, row in enumerate(mat):
        for j, x in enumerate(row):
            hop.append([multiplier * x, orbitals[i], orbitals[j], np.array(R, dtype=int)])
    return hop
