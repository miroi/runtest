import os
import sys
import pytest
import runtest

# ------------------------------------------------------------------------------


def test_extract_numbers():

    text = '''<<A( 3),B( 3)>> - linear response function (real):
-----------------------------------------------------------------------------------------------
   A - Z-Dipole length      B1u  T+
   B - Z-Dipole length      B1u  T+
-----------------------------------------------------------------------------------------------
 Frequency (real)     Real part                                     Convergence
-----------------------------------------------------------------------------------------------
  0.00000000 a.u.   -1.901357604797 a.u.                       3.04E-07   (converged)
-----------------------------------------------------------------------------------------------
----------------------------------------------------------------------------


                         +--------------------------------+
                         ! Electric dipole polarizability !
                         +--------------------------------+


 1 a.u =   0.14818471 angstrom**3


@   Elements of the electric dipole polarizability tensor

@   xx            1.90135760 a.u.   (converged)
@   yy            1.90135760 a.u.   (converged)
@   zz            1.90135760 a.u.   (converged)

@   average       1.90135760 a.u.
@   anisotropy    0.000      a.u.

@   xx            0.28175212 angstrom**3
@   yy            0.28175212 angstrom**3
@   zz            0.28175212 angstrom**3

@   average       0.28175212 angstrom**3
@   anisotropy    0.000      angstrom**3'''

    f = runtest.Filter()
    f.add()

    numbers, locations = runtest.extract_numbers(f.filter_list[0], text.splitlines())

    assert numbers == [0.0, -1.901357604797, 3.04e-07, 1, 0.14818471, 1.9013576, 1.9013576, 1.9013576, 1.9013576, 0.0, 0.28175212, 0.28175212, 0.28175212, 0.28175212, 0.0]
    assert locations == [(7, 2, 10), (7, 20, 15), (7, 63, 8), (17, 1, 1), (17, 11, 10), (22, 18, 10), (23, 18, 10), (24, 18, 10), (26, 18, 10), (27, 18, 5), (29, 18, 10), (30, 18, 10), (31, 18, 10), (33, 18, 10), (34, 18, 5)]

# ------------------------------------------------------------------------------


def test_extract_numbers_mask():

    text = '''1.0 2.0 3.0 4.0
1.0 2.0 3.0 4.0
1.0 2.0 3.0 4.0'''

    f = runtest.Filter()
    f.add(mask=[1, 4])

    numbers, locations = runtest.extract_numbers(f.filter_list[0], text.splitlines())

    assert numbers == [1.0, 4.0, 1.0, 4.0, 1.0, 4.0]
    assert locations == [(0, 0, 3), (0, 12, 3), (1, 0, 3), (1, 12, 3), (2, 0, 3), (2, 12, 3)]

# ------------------------------------------------------------------------------


def test_parse_args():

    input_dir = '/raboof/mytest'
    argv = ['./test', '-b', '/raboof/build/']

    options = runtest.parse_args(input_dir, argv)

    assert options == {'verbose': False, 'work_dir': '/raboof/mytest', 'binary_dir': '/raboof/build/', 'skip_run': False, 'debug': False, 'log': None}

# ------------------------------------------------------------------------------


def test_filter_file():

    text = '''
1.0 2.0 3.0
1.0 2.0 3.0
1.0 2.0 3.0
1.0 2.0 3.0
1.0 2.0 3.0
1.0 2.0 3.0
1.0 2.0 3.0
raboof 1.0 3.0 7.0
       1.0 3.0 7.0
       1.0 3.0 7.0
       1.0 3.0 7.0
       1.0 3.0 7.0
       1.0 3.0 7.0
       1.0 3.0 7.0
       1.0 3.0 7.0'''

    f = runtest.Filter()
    f.add(rel_tolerance=1.0e-5, from_re='raboof', num_lines=5)

    res = runtest.filter_file(f=f.filter_list[0], file_name='raboof', output=text.splitlines())
    assert res == ['raboof 1.0 3.0 7.0', '       1.0 3.0 7.0', '       1.0 3.0 7.0', '       1.0 3.0 7.0', '       1.0 3.0 7.0']

# ------------------------------------------------------------------------------


def test_unrecognized_kw():

    kwargs = {'num_lines': 5, 'raboof': 137}

    with pytest.raises(runtest.FilterKeywordError) as e:
        res = runtest.check_for_unrecognized_kw(kwargs)

    assert e.value.message == 'ERROR: keyword "raboof" not recognized\n' \
        + '       available keywords: from_re, to_re, re, from_string, ' \
        + 'to_string, string, ignore_below, ignore_above, ignore_sign, mask, num_lines, rel_tolerance, abs_tolerance\n'

# ------------------------------------------------------------------------------


def test_incompatible_kw():

    kwargs = {'num_lines': 5, 'string': 'raboof'}

    with pytest.raises(runtest.FilterKeywordError) as e:
        res = runtest.check_for_incompatible_kw(kwargs)

    assert e.value.message == 'ERROR: incompatible keywords: "string" and "num_lines"\n'

# ------------------------------------------------------------------------------


def test_check():

    HERE = os.path.abspath(os.path.dirname(__file__))

    out_name = os.path.join(HERE, 'out.txt')
    ref_name = os.path.join(HERE, 'ref.txt')

    f = runtest.Filter()
    f.add(abs_tolerance=0.1)
    f.check(work_dir='not used', out_name=out_name, ref_name=ref_name, verbose=False)

    f = runtest.Filter()
    f.add()
    with pytest.raises(runtest.FilterKeywordError) as e:
        f.check(work_dir='not used', out_name=out_name, ref_name=ref_name, verbose=False)
    assert e.value.message == 'ERROR: for floats you have to specify either rel_tolerance or abs_tolerance\n'

    f = runtest.Filter()
    f.add(abs_tolerance=0.01)
    with pytest.raises(runtest.TestFailedError) as e:
        f.check(work_dir='not used', out_name=out_name, ref_name=ref_name, verbose=False)
    assert e.value.message == 'ERROR: test %s failed\n' % out_name
    with open(os.path.join(HERE, 'out.txt.diff'), 'r') as f:
        assert f.read() == '''
.       1.0 2.0 3.0
ERROR           ### expected: 3.05 (abs diff: 5.00e-02)\n'''

    f = runtest.Filter()
    f.add(abs_tolerance=0.01, ignore_sign=True)
    with pytest.raises(runtest.TestFailedError) as e:
        f.check(work_dir='not used', out_name=out_name, ref_name=ref_name, verbose=False)
    assert e.value.message == 'ERROR: test %s failed\n' % out_name
    with open(os.path.join(HERE, 'out.txt.diff'), 'r') as f:
        assert f.read() == '''
.       1.0 2.0 3.0
ERROR           ### expected: 3.05 (abs diff: 5.00e-02 ignoring signs)\n'''