import pytest
from sortedcontainers import SortedDict
from cofmpy.utils import lookup_with_window

@pytest.fixture
def simple_sorted_dict():
    return SortedDict({
        1.0: {"val": 10},
        2.0: {"val": 20},
        3.0: {"val": 30},
        4.0: {"val": 40},
        5.0: {"val": 50},
    })

def test_exact_match(simple_sorted_dict):
    status, ts_list, val_list = lookup_with_window(simple_sorted_dict, 2.0)
    assert status is True
    assert ts_list == [2.0]
    assert val_list == [{"val": 20}]

def test_previous_only(simple_sorted_dict):
    status, ts_list, val_list = lookup_with_window(simple_sorted_dict, 3.5, n_previous=0)
    assert status is True
    assert ts_list == [3.0]
    assert val_list == [{"val": 30}]

def test_window_lookup(simple_sorted_dict):
    status, ts_list, val_list = lookup_with_window(simple_sorted_dict, 3.5, n_previous=2)
    assert status is True
    assert ts_list == [2.0, 3.0, 4.0]
    assert val_list == [20, 30, {"val": 40}]

def test_window_insufficient_past(simple_sorted_dict):
    status, ts_list, val_list = lookup_with_window(simple_sorted_dict, 1.5, n_previous=2)
    assert status is False
    assert ts_list == []
    assert val_list == []

def test_window_insufficient_future(simple_sorted_dict):
    status, ts_list, val_list = lookup_with_window(simple_sorted_dict, 5.5, n_previous=2)
    assert status is False
    assert ts_list == []
    assert val_list == []

def test_timestamp_none(simple_sorted_dict):
    status, ts_list, val_list = lookup_with_window(simple_sorted_dict, None)
    assert status is False
    assert ts_list == []
    assert val_list == []

def test_timestamp_negative(simple_sorted_dict):
    status, ts_list, val_list = lookup_with_window(simple_sorted_dict, -1.0)
    assert status is False
    assert ts_list == []
    assert val_list == []

def test_empty_dict():
    status, ts_list, val_list = lookup_with_window(SortedDict(), 2.0)
    assert status is False
    assert ts_list == []
    assert val_list == []

def test_window_at_end(simple_sorted_dict):
    status, ts_list, val_list = lookup_with_window(simple_sorted_dict, 4.5, n_previous=1)
    assert status is True
    assert ts_list == [4.0, 5.0]
    assert val_list == [40, {"val": 50}]
