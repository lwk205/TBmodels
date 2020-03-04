#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for folding models."""

import numpy as np
import pytest

from parameters import T_VALUES


@pytest.mark.parametrize('t_values', T_VALUES)
@pytest.mark.parametrize('supercell_size', [(1, 1, 1), (2, 1, 1), (2, 1, 3)])
def test_fold_supercell_simple(get_model, t_values, supercell_size, sparse, models_close):
    """
    Test that creating a supercell model and then folding it back creates
    the same model.
    """
    model = get_model(
        *t_values,
        sparse=sparse,
        uc=[[1, 0, 0.5], [0.1, 0.4, 0.], [0., 0., 1.2]],
        pos=[[0, 0, 0], [0.2, 0.3, 0.1]]
    )
    supercell_model = model.supercell(size=supercell_size)
    orbital_labels = ['a', 'b'] * np.prod(supercell_size)
    for i, offset_red in enumerate(supercell_model.pos[::2]):
        # TODO: changing the 'offset_red' manually is a temporary fix:
        # to be removed when more complex orbital matching is implemented.
        offset_cart = supercell_model.uc.T @ (offset_red - 1e-12)
        folded_model = supercell_model.fold_model(
            new_unit_cell=model.uc,
            unit_cell_offset=offset_cart,
            orbital_labels=orbital_labels,
            target_indices=[2 * i, 2 * i + 1],
        )
        assert models_close(model, folded_model)


def test_fold_inexact_positions(get_model, models_close):
    """
    Test that creating a supercell model and then folding it back creates
    the same model.
    """
    model = get_model(0.1, 0.3)
    model.uc = np.array([[1, 0, 0.5], [0.1, 0.4, 0.], [0., 0., 1.2]])
    model.pos = np.array([[0, 0, 0], [0.5, 0.5, 0.5]])
    supercell_model = model.supercell(size=(8, 1, 1))
    orbital_labels = ['a', 'b'] * 8
    np.random.seed(42)
    for i in range(len(supercell_model.pos)):
        # do not move positions around "base" unit cell
        if i in range(3, 7):
            continue
        delta = np.random.uniform(-0.01, 0.01, 3)
        supercell_model.pos[i] += delta
    folded_model = supercell_model.fold_model(
        new_unit_cell=model.uc,
        unit_cell_offset=supercell_model.uc.T @ supercell_model.pos[4],
        orbital_labels=orbital_labels,
        position_tolerance=0.1,
        check_cc=False
    )
    assert models_close(model, folded_model)


@pytest.fixture
def get_model_pos_outside(get_model):
    """
    Fixture which creates a model where one position is outside the
    unit cell.
    """
    def inner():
        model = get_model(0.1, 0.3, uc=np.eye(3))
        model.pos[0][0] = -0.01
        return model

    return inner


def test_consistency_checks_disabled(get_model_pos_outside):  # pylint: disable=redefined-outer-name,invalid-name
    """
    Test that no error is raised if the folding consistency checks
    are disabled.
    """
    model = get_model_pos_outside()
    model.fold_model(
        new_unit_cell=model.uc,
        orbital_labels=['a', 'b'],
        check_orbital_ratio=False,
        check_uc_volume=False
    )


def test_orbital_number_consistency_check(get_model_pos_outside):  # pylint: disable=redefined-outer-name,invalid-name
    """
    Test that the orbital ratio check raises an error for a model
    that has a position outside the unit cell.
    """
    model = get_model_pos_outside()
    with pytest.raises(ValueError) as excinfo:
        model.fold_model(new_unit_cell=model.uc, orbital_labels=['a', 'b'], check_uc_volume=False)
    assert "individual orbital numbers" in str(excinfo.value)


def test_volume_consistency_check(get_model_pos_outside):  # pylint: disable=redefined-outer-name
    """
    Test that the unit cell volume check raises an error for a model
    that has a position outside the unit cell.
    """
    model = get_model_pos_outside()
    with pytest.raises(ValueError) as excinfo:
        model.fold_model(
            new_unit_cell=model.uc, orbital_labels=['a', 'b'], check_orbital_ratio=False
        )
    assert "unit cell volume" in str(excinfo.value)


def test_fractional_occupation_consistency_check(get_model):  # pylint: disable=invalid-name
    """
    Check that an error is raised when the resulting number of
    occupations is fractional. This is tested by manually changing
    the occupation number in a supercell model
    """
    model = get_model(0.1, 0.3, uc=np.eye(3))
    supercell_model = model.supercell(size=(2, 1, 1))
    supercell_model.occ += 1
    with pytest.raises(ValueError) as excinfo:
        supercell_model.fold_model(new_unit_cell=model.uc, orbital_labels=['a', 'b'] * 2)
    assert "fractional" in str(excinfo.value)